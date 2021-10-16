import requests
from bs4 import BeautifulSoup
import bs4
import numpy as np
import pandas as pd
from icalendar import Calendar, Event
from datetime import datetime, timedelta, time
import pytz
import os
import re
from definitions import week_days, CAL_FOLDER

def dtstr2dtaw(string, tz):
	""" takes date string (%d.%m.%Y %H:%M) and returns aware datetime """
	tz = pytz.timezone(tz)
	naive = datetime.strptime(string, '%d.%m.%Y %H:%M')
	return tz.localize(naive, is_dst=None).astimezone(pytz.utc)

def typofteam(string):
	if 'Damen' in string:
		typ = 'Damen'
	elif 'Herren' in string:
		typ = 'Herren'
	elif 'Mixed' in string:
		typ = 'Mixed/Beach'
	elif 'Beach' in string:
		typ = 'Mixed/Beach'
	else:
		typ = 'Jugend'
	return typ

def teamabbrv(string):
	string = string.replace('(4er)','').strip()
	if string[0] in ['H','D']:
		abbrv = string[0]
		for i in range(1,len(string.split())):
			abbrv = abbrv+string.split()[i]
		if abbrv == string[0]:
			abbrv = string[0]+'00'
		return abbrv
	elif string[0] == 'U':
		return string.replace(' ','')
	elif 'Midcourt' in string:
		return 'MID'
	elif 'Mixed' in string:
		return 'MX'
	elif 'Beach' in string:
		return 'B'


def teams():

	call = 'https://tvbb.liga.nu/cgi-bin/WebObjects/nuLigaTENDE.woa/wa/clubTeams?club=36249'
	s = requests.Session()
	r = s.get(call)

	soup = BeautifulSoup(r.content, 'html5lib')
	tbody = soup.findAll('tbody')
	# pick last tbody -> registration of winter teams is first
	td = tbody[len(tbody)-1].findAll('td')

	i = 1
	data = []

	for t in td:

		# season
		h2 = t.findAll('h2')
		if h2 != []:
			season = h2[0].contents[0].replace('MD','').strip()

		href = t.findAll('a', href=True, attrs={'class':''})

		if href != []:
			if i % 2 != 0:
				team = href[0].contents[0]
				link = 'https://tvbb.liga.nu'+href[0]['href']
				typ = typofteam(team)
				d = {
					'team': team,
					'teamabbrv': teamabbrv(team),
					'link': link,
					'season': season,
					'category': typ
				}
				data.append(d)
			i += 1

	return pd.DataFrame(data=data) 

def dates(call, season):

	# request data
	s = requests.Session()
	r = s.get(call)
	soup = BeautifulSoup(r.content, 'html5lib')
	tbody = soup.findAll('tbody')
	td = tbody[1].findAll('td')

	# list of match days
	mdays = []
	n = len(td)
	i = 1
	for t in td:
		t = t.text.strip()
		if t in week_days:
			if 'mday' in locals():
				mdays.append(mday)
			mday = []
		mday.append(t)
		i = i+1
		if i == n:
			mdays.append(mday)

	dlist = []
	for mday in mdays:
		if 'Winter' in season:
			d = {
				'date': mday[1],
				'place': mday[2],
				'home': mday[3],
				'away': mday[4],
			}
		else:
			d = {
				'date': mday[1],
				'home': mday[2],
				'away': mday[3]
			}
			
		dlist.append(d)

	return pd.DataFrame(data=dlist)


def ical(data, team, season, name):

	# initialize calender object
	cal = Calendar()

	# create events for each row
	for index, row in data.iterrows():

		# initialize event object
		event = Event()

		# define variables
		if 'TC Grün-Gold Pankow' in row['home']:
			opponent = row['away']
			location = 'H'
		else:
			opponent = row['home']
			location = 'A'

		if 'Winter' in season:
			location = row['place']

		summary = f'{teamabbrv(team)} {location} {opponent}'
		start = dtstr2dtaw(row['date'], 'Europe/Berlin')
		end = start + timedelta(minutes=300)

		event.add('dtend', end)
		event.add('dtstart', start)
		event.add('summary', summary)

		cal.add_component(event)

	# create ical file
	f = open(CAL_FOLDER+'/'+name+'.ics', 'wb')
	f.write(cal.to_ical())
	f.close()
