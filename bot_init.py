import telegram
import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)
from methods import (teams, dates, ical, teamabbrv)
import io
import os
import time
from pandas.core.common import flatten
from definitions import (TOKEN, confirm, reject, conversation, SHORT_SLEEP, LONG_SLEEP, CAL_FOLDER)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

logger = logging.getLogger(__name__)

SEASON, CATEGORY, AGE, RESTART, PAUSE = range(5)

def answer(text, reply_keyboard, sleep_time, context, message):
	chat_id = message.chat_id
	context.bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
	time.sleep(sleep_time)
	if reply_keyboard == None:
		message.reply_text(text,reply_markup=ReplyKeyboardRemove())
	else:
		message.reply_text(text,reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
	context.chat_data['reply_keyboard'] = reply_keyboard

def force_keyboard_reply(reply_keyboard, context, message):
	chat_id = message.chat_id
	text = conversation['reply_keyboard']
	context.bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
	time.sleep(SHORT_SLEEP)
	message.reply_text(text,reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

def start(update, context):

	logger.info('Bot gestartet')

	m = update.message
	answer(conversation['start1']+f' {m.from_user.name}!', None, SHORT_SLEEP, context, m)
	answer(conversation['start2'], None, SHORT_SLEEP, context, m)

	df = teams()
	season = df['season'].unique()

	if len(season) == 1:
		
		context.chat_data['season'] = season[0]
		df = teams()
		df = df[df.season.eq(season[0])]
		category = df['category'].unique()
		context.chat_data['category'] = category

		answer(conversation['category'], [[c] for c in category], SHORT_SLEEP, context, m)
		return CATEGORY

	else:
		answer(conversation['season'], [[s] for s in season], SHORT_SLEEP, context, m)
		return SEASON

def season(update, context):
	m = update.message
	user, reply = m.from_user, m.text
	logger.info('season: %s', reply)

	if reply in list(flatten(context.chat_data['reply_keyboard'])):

		context.chat_data['season'] = reply

		df = teams()
		df = df[df.season.eq(reply)]
		category = df['category'].unique()

		answer(conversation['category'], [[c] for c in category], SHORT_SLEEP, context, m)
		return CATEGORY

	else:
		force_keyboard_reply(context.chat_data['reply_keyboard'], context, m)
		return SEASON


def category(update, context):
	m = update.message
	user, reply = m.from_user, m.text
	logger.info('category: %s', reply)

	if reply in list(flatten(context.chat_data['reply_keyboard'])):

		context.chat_data['category'] = reply

		season = context.chat_data['season']
		df = teams()
		df = df[df.season.eq(season)]
		df = df[df.category.eq(reply)]

		answer(conversation['age'], [df['teamabbrv'].to_list()], SHORT_SLEEP, context, m)
		return AGE

	else:
		force_keyboard_reply(context.chat_data['reply_keyboard'], context, m)
		return CATEGORY
		

def age(update, context):
	m = update.message
	logger.info('age: %s', m.text)

	if m.text in list(flatten(context.chat_data['reply_keyboard'])):

		season = context.chat_data['season']
		category = context.chat_data['category']
		df = teams()
		df = df[df.season.eq(season)]
		df = df[df.teamabbrv.eq(m.text)]
		index = df['link'].index[0]
		call = df['link'][index]

		data = dates(call, season)

		ical(data, m.text, season, 'cal')

		# calendar name to be send
		index = df['season'].index[0]
		season = df['season'][index].split()
		season = season[0][:2]+season[1][-2:]
		index = df['team'].index[0]
		team = df['team'][index].split()
		name = m.text+'_'+season+'.ics'

		# preview of dates send in chat
		text = 'Das sind die Spieltermine in der Kalenderdatei: \n'
		for index, row in data.iterrows():
			if 'TC Grün-Gold Pankow' in row['home']:
				place = 'Heimspiel vs.	'
				opponent = row['away']
			else:
				place = 'Auswärts vs.	'	
				opponent = row['home']
			string = row['date']+'	'+place+opponent
			text = text+'\n'+string

		answer(text, None, LONG_SLEEP, context, m)

		# send calendar file
		with open(CAL_FOLDER+'/cal.ics', 'rb') as f:
			context.bot.send_document(m.chat_id,f,name)
		answer(conversation['sent'], None, SHORT_SLEEP, context, m)

		# ask for restart
		answer(conversation['restart'], [['Ja'],['Nein']], SHORT_SLEEP, context, m)

		return RESTART

	else:

		force_keyboard_reply(context.chat_data['reply_keyboard'], context, m)
		return AGE

def restart(update, context):
	m = update.message
	reply = m.text.lower()
	logger.info('restart: %s', m.text)

	if reply in confirm:
		df = teams()
		season = df['season'].unique()

		if len(season) == 1:

			context.chat_data['season'] = season[0]
			df = teams()
			df = df[df.season.eq(season[0])]
			category = df['category'].unique()
			context.chat_data['category'] = category

			answer(conversation['category'], [[c] for c in category], SHORT_SLEEP, context, m)
			return CATEGORY

		else:

			answer(conversation['season'], [[s] for s in season], SHORT_SLEEP, context, m)
			return SEASON

	elif reply in reject:
		answer(conversation['end'], None, SHORT_SLEEP, context, m)
		return PAUSE

	else:
		force_keyboard_reply([['Ja'],['Nein']], context, m)


def pause(update, context):
	m = update.message
	logger.info('pause: %s', m.text)
	answer(conversation['restart'], [['Ja'],['Nein']], SHORT_SLEEP, context, m)
	return RESTART


def cancel(update, context):
	m = update.message
	logger.info('%s hat die Konservation beendet.', m.from_user.name)
	answer(conversation['end'], None, SHORT_SLEEP, context, m)
	return ConversationHandler.END

def main():
	updater = Updater(TOKEN, use_context=True)
	dp = updater.dispatcher    

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler('start', start)],
		states={
			SEASON: [MessageHandler(Filters.text, season)],
			CATEGORY: [MessageHandler(Filters.text, category)],
			AGE: [MessageHandler(Filters.text, age)],
			RESTART: [MessageHandler(Filters.text, restart)],
			PAUSE: [MessageHandler(Filters.text, pause)]
		},
		fallbacks=[CommandHandler('cancel', cancel)]
	)
	dp.add_handler(conv_handler)
	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
	main()