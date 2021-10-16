
import pandas as pd
from methods import teams, dates

data = teams()
season = data['season'].unique()


for s in season:
	df1 = data[data.season.eq(s)]
	typ = df1['category'].unique()

	for t in typ:

		df2 = df1[df1.category.eq(t)]
		age = df2['teamabbrv'].unique()	

		for a in age:

			df3 = df2[df2.teamabbrv.eq(a)]
			index = df3['link'].index[0]
			call = df3['link'][index]
			date = dates(call, s)
			team = df3['teamabbrv'][index]
			text = f'\n\n{team}\n'
			for index, row in date.iterrows():
				if 'TC Grün-Gold Pankow' in row['home']:
					place = 'Heimspiel vs.	'
					opponent = row['away']
				else:
					place = 'Auswärts vs.	'	
					opponent = row['home']
				string = row['date']+'	'+place+opponent
				text = text+'\n'+string

			print(text)


