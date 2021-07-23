import json
import requests
import time
from TournamentAnalysis.BingoTournamentAnalysis import parse_rows
from BingoTools import BingoBoard
import pandas as pd


class BingoRace:
	def __init__(self, race_response):
		race_room = race_response['url'].split('oot/')[1]
		race = json.loads(requests.get(f"https://racetime.gg/oot/{race_room}/data").content)

		self.racers = []
		self.times = []
		self.rows = []
		for ent in race['entrants']:
			self.racers.append(ent['user']['name'])
			# timestamp = pd.to_datetime(race['entrants'][0]['finish_time'].split('DT')[1].split('.')[0], format='%HH%MM%S')

			timestamp = ent['finish_time']
			if timestamp is None:
				this_time = '-'
			else:
				this_time = timestamp.split('DT')[1].split('.')[0].replace('H', ':').replace('M', ':')

			self.times.append(this_time)
			try:
				self.rows.append(parse_rows(ent['comment']))
			except AttributeError:
				self.rows.append('a dirty blank')
		info_split = race['info'].split('=')[1:]
		for partial_info in info_split:
			try:
				self.seed = int(partial_info.split('&')[0])
				break
			except (TypeError, ValueError):
				pass

		self.board = BingoBoard(self.seed, silent=True)
		self.starttime = pd.to_datetime(race['started_at']).tz_convert(tz='Europe/Berlin')
		self.weekly = self.is_weekly()

	def timestring_from_structtime(self, struct):
		timestamp = struct.split('DT')[1].split('.')[0]

	def is_weekly(self):
		if (self.starttime.weekday() == 5) & (self.starttime.hour in [21, 22]):
			return True
		else:
			eastern = self.starttime.tz_convert(tz='US/Eastern')
			if (eastern.weekday() == 5) & (eastern.hour == 21):
				return True
			else:
				return False
