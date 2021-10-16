from dotenv import load_dotenv
import os

load_dotenv()
TOKEN, CAL_FOLDER = os.environ['TOKEN'], os.environ['CAL_FOLDER']
confirm = ['yes','y','ja','j','si','sim']
reject = ['no','n','nein']

conversation = {
	'start1': 'Hallo',
	'start2': 'Ich bin ein Kalenderbot für die Mannschaftsspiele des TC Grün-Gold Pankow.',
	'category': 'In welcher Kategorie suchst du?',
	'season': 'Welche Saison möchtest du?',
	'age': 'Für welche Altersklasse?',
	'restart': 'Möchtest du noch einen Kalender?',
	'end': 'Alles klar. Tschüssi!',
	'reply_keyboard': 'Bitte nutze eine der Antwortmöglichkeiten',
	'sent': 'Bitte schön!'
}

SHORT_SLEEP, LONG_SLEEP = 1, 2

week_days = ['Mo.','Di.','Mi.','Do.','Fr.','Sa.','So.']