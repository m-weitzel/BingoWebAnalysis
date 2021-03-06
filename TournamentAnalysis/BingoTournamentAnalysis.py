from BingoTools import BingoBoard
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pickle
import os
from collections import Counter
import pandas as pd
import numpy as np
from BingoTools import find_goal_combinations


class TournamentRace:
	def __init__(self, race_room, driver, filter_list=()):#'Myelin', 'Jake Wright', 'xwillmarktheplace')):
		driver.get(f"https://racetime.gg/oot/{race_room[0]}")
		content = driver.page_source
		soup = BeautifulSoup(content, features="html.parser")

		racer_entries = soup.find_all('li', class_='entrant-row')

		if race_room[1]:
			re_indices = [0, 0]
			designated_racers = race_room[1], race_room[2]
			for re_index, re in enumerate(racer_entries):
				next_racer = re.find_next('span', class_='name').text
				if next_racer == designated_racers[0]:
					self.racer1 = next_racer
					re_indices[0] = re_index
				if next_racer == designated_racers[1]:
					self.racer2 = next_racer
					re_indices[1] = re_index
			re_indices = tuple(re_indices)
		else:
			re_indices = (0, 1)

			self.racer1 = racer_entries[re_indices[0]].find_next('span', class_='name').text
			self.racer2 = racer_entries[re_indices[1]].find_next('span', class_='name').text

		self.time1 = racer_entries[re_indices[0]].find_next('time', class_='finish-time').text
		self.time2 = racer_entries[re_indices[1]].find_next('time', class_='finish-time').text

		try:
			self.row_p1 = parse_rows(racer_entries[re_indices[0]].find_next('span', class_='text').text)
		except AttributeError:
			self.row_p1 = 'a dirty blank'
		try:
			self.row_p2 = parse_rows(racer_entries[re_indices[1]].find_next('span', class_='text').text)
		except AttributeError:
			self.row_p2 = 'a dirty blank'

		self.seed = soup.find_all('span', class_='info')[0].find_next('a').text.split('=')[1].split('&')[0]
		self.board = BingoBoard(self.seed)


class Racer:
	def __init__(self, name):
		self.name = name
		self.times = list()
		self.rows = list()
		self.seeds = list()
		self.forfeits = 0
		self.blanks = 0

	def calc_mean_median(self):
		actual_times = list()
		for t in self.times:
			if t is not 'nan':
				actual_times.append(t)
		if len(actual_times) < 1:
			return 'nan', 'nan'
		else:
			actual_times = pd.to_timedelta(actual_times)
			mean_dt = actual_times.mean().components
			median_dt = actual_times.median().components
			return f'{mean_dt.hours}:{str(mean_dt.minutes).zfill(2)}:{str(mean_dt.seconds).zfill(2)}', \
				   f'{median_dt.hours}:{str(median_dt.minutes).zfill(2)}:{str(median_dt.seconds).zfill(2)}'


def parse_rows(text):
	text = text.lower()
	if any([c in text for c in ['row1', 'row 1', 'r1', 'r 1']]):
		return 'row1'
	if any([c in text for c in ['row2', 'row 2', 'r2', 'r 2']]):
		return 'row2'
	if any([c in text for c in ['row3', 'row 3', 'r3', 'r 3']]):
		return 'row3'
	if any([c in text for c in ['row4', 'row 4', 'r4', 'r 4']]):
		return 'row4'
	if any([c in text for c in ['row5', 'row 5', 'r5', 'r 5']]):
		return 'row5'

	if any([c in text for c in ['col1', 'col 1', 'c1', 'c 1']]):
		return 'col1'
	if any([c in text for c in ['col2', 'col 2', 'c2', 'c 2']]):
		return 'col2'
	if any([c in text for c in ['col3', 'col 3', 'c3', 'c 3']]):
		return 'col3'
	if any([c in text for c in ['col4', 'col 4', 'c4', 'c 4']]):
		return 'col4'
	if any([c in text for c in ['col5', 'col 5', 'c5', 'c 5']]):
		return 'col5'

	if any([c in text for c in ['tlbr', 'tl br', 'tl-br']]):
		return 'tlbr'
	if any([c in text for c in ['bltr', 'bl tr', 'bl-tr']]):
		return 'bltr'

	return 'a dirty blank'


def pull_races(new_rooms):
	chrome_options = Options()
	chrome_options.add_argument("--disable-gpu")
	chrome_options.add_argument("--headless")
	chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

	chromedriver_path = 'D:\Programme\chromedriver.exe' if os.name == 'nt' else '/usr/bin/chromedriver'
	driver = webdriver.Chrome(chromedriver_path, options=chrome_options)
	race_result_list = list()
	for room in new_rooms:
		race_result = TournamentRace(room, driver)
		pickle.dump(race_result, open(f'results/{room[0]}.pickle', 'wb'))
		race_result_list.append(race_result)
	driver.quit()
	return race_result_list


def load_races():
	files = os.listdir('results')
	loaded_race_results = list()
	for f in files:
		if f.endswith('.pickle'):
			loaded_race_results.append(pickle.load(open(f'results/{f}', 'rb')))
	return loaded_race_results


def main():

	tournament_race_rooms = [
		('frantic-heartcontainer-2442','',''),                   # blinkzy vs. PhoenixFeather
		('overpowered-dampe-7225','',''),                        # ZAR vs MikeKatz45
		('mysterious-dampe-5521','',''),                         # Titou vs Coffeepot
		('chaotic-temple-4289','Gombill','Countdown'),           # Gombill vs. Countdown, includes Myelin
		('speedy-wallet-6331', '',''),                           # Timato vs. gc_one
		('brainy-fairy-1215', 'Link11','Runnerguy2489'),         # Link11 vs. Runnerguy2489, includes Jake Wright
		('lazy-cow-8260','',''),                                 # scaramanga vs. Nalle
		('perfect-anubis-4156','',''),                           # QuickKiran vs. Chromium_Light
		('witty-nocturne-5332','',''),                           # Tob3000 vs. PsyMarth
		('clumsy-ganondorf-3762','',''),                         # AverageGreg vs. MutantAura
		('scruffy-barinade-0218','',''),                         # MatttInTheHat vs. noface099
		('legendary-lullaby-7764','',''),                        # Fenyan vs. Davpat
		('fancy-dekutree-7025','',''),                           # FantaTanked vs. mgbgnr
		('curious-colossus-9627','',''),                         # Bonooru vs. Tashman91
		('prudent-heartcontainer-3610','',''),                   # Fleush vs. DiamondFlash27, includes xwillmarktheplace
		('lucky-longshot-1478','',''),                           # Moose vs. Princess Kayla
		('critical-smallkey-2398','',''),                        # Lake_oot vs. Midboss
		('sublime-cow-6857','',''),                              # Shaggy vs. Hapenfors
		('clumsy-heartpiece-9095','',''),                        # Amateseru vs. Condor
		('salty-octorok-5065','',''),                            # Xanra vs. Myelin
		('disco-nabooru-0288','',''),                            # xwillmarktheplace vs. moosecrap

		# Filter-relevant races


		# Add new races here
	]



	all_race_results = pull_races(tournament_race_rooms)
	all_race_results = load_races()
	available_goals_list = list()
	picked_goals_list = list()
	list_of_player_names = list()
	player_list = list()
	winning_goals_list = list()

	player_df = pd.DataFrame(columns=['name', 'wins', 'losses']).set_index('name')
	for race_result in all_race_results:

		print(f'{race_result.racer1} got a {race_result.time1} with {race_result.row_p1}.')
		print(f'{race_result.racer2} got a {race_result.time2} with {race_result.row_p2}.')
		print(f'The seed was {race_result.seed}.')
		room_board = race_result.board.board
		available_goals_list.append(room_board.goals[:5].sum())
		try:
			picked_goals_list.append(room_board[room_board.row == race_result.row_p1]['goals'].item())
		except ValueError:
			pass
		try:
			picked_goals_list.append(room_board[room_board.row == race_result.row_p2]['goals'].item())
		except ValueError:
			pass

		if race_result.racer1 in list_of_player_names:
			for p in player_list:
				if p.name == race_result.racer1:
					if race_result.time1 == '—':
						p.times.append('nan')
					else:
						p.times.append(race_result.time1)
					if race_result.row_p1 == 'a dirty blank':
						p.blanks += 1
					p.rows.append(race_result.row_p1)
					p.seeds.append(race_result.seed)

		else:
			r = Racer(race_result.racer1)
			r.rows.append(race_result.row_p1)
			if race_result.row_p1 == 'a dirty blank':
				r.blanks += 1
			if race_result.time1 == '—':
				r.times.append('nan')
				r.forfeits += 1
			else:
				r.times.append(race_result.time1)
			r.seeds.append(race_result.seed)
			player_list.append(r)
			list_of_player_names.append(race_result.racer1)
			player_df = player_df.append(pd.DataFrame({'wins':0, 'losses': 0}, index=[race_result.racer1]))

		if race_result.racer2 in list_of_player_names:
			for p in player_list:
				if p.name == race_result.racer2:
					if race_result.time2 == '—':
						p.times.append('nan')
					else:
						p.times.append(race_result.time2)
					p.rows.append(race_result.row_p2)
					if race_result.row_p2 == 'a dirty blank':
						p.blanks += 1
					p.seeds.append(race_result.seed)
		else:
			r = Racer(race_result.racer2)
			r.rows.append(race_result.row_p2)
			if race_result.row_p2 == 'a dirty blank':
				r.blanks += 1
			if race_result.time2 == '—':
				r.times.append('nan')
				r.forfeits += 1
			else:
				r.times.append(race_result.time2)
			r.seeds.append(race_result.seed)
			player_list.append(r)
			list_of_player_names.append(race_result.racer2)
			player_df = player_df.append(pd.DataFrame({'wins':0, 'losses': 0}, index=[race_result.racer2]))
		if race_result.time1 < race_result.time2:
			player_df.loc[race_result.racer1, 'wins'] += 1
			player_df.loc[race_result.racer2, 'losses'] += 1
			try:
				winning_goals_list.append(room_board[room_board.row == race_result.row_p1]['goals'].item())
			except ValueError:
				pass
		else:
			player_df.loc[race_result.racer2, 'wins'] += 1
			player_df.loc[race_result.racer1, 'losses'] += 1
			try:
				winning_goals_list.append(room_board[room_board.row == race_result.row_p2]['goals'].item())
			except ValueError:
				pass

	available_combinations = find_goal_combinations(available_goals_list).query('count > 1')
	available_goals_list = [inner for outer in available_goals_list for inner in outer]

	print(available_goals_list)
	goalcounter = Counter(available_goals_list)
	goal_counting_df = pd.DataFrame({'goal': [d[0] for d in goalcounter.items()], 'count': list(goalcounter.values())}).set_index('goal').sort_values('count')

	picked_combinations_df = find_goal_combinations(picked_goals_list)

	picked_goals_list = [inner for outer in picked_goals_list for inner in outer]
	picked_goalcounter = Counter(picked_goals_list)
	pick_df = pd.DataFrame({'goal': [d[0] for d in picked_goalcounter.items()], 'pick count': list(picked_goalcounter.values())}).set_index('goal')

	winning_goals_list = [inner for outer in winning_goals_list for inner in outer]
	winning_counter = Counter(winning_goals_list)
	winning_df = pd.DataFrame({'goal': [d[0] for d in winning_counter.items()], 'win count': list(winning_counter.values())}).set_index('goal')

	goals_ap_df = goal_counting_df.merge(pick_df, how='outer', left_index=True, right_index=True).sort_values('count', ascending=False)
	goals_ap_df = goals_ap_df.merge(winning_df, how='outer', left_index=True, right_index=True).sort_values('count', ascending=False)

	goals_ap_df['pick count'] = goals_ap_df['pick count'].fillna(0).astype('int')
	goals_ap_df['win count'] = goals_ap_df['win count'].fillna(0).astype('int')
	goals_ap_df['pick%'] = goals_ap_df.apply(lambda r: r['pick count']/r['count']*100, axis=1).round(1)
	goals_ap_df['win%'] = goals_ap_df.apply(lambda r: r['win count']/r['pick count']*100, axis=1).fillna(0).round(1)
	goals_ap_df = goals_ap_df.sort_values(by='pick%', ascending=False)
	goals_ap_df.to_csv('goals.csv')

	means_medians = [p.calc_mean_median() for p in player_list]
	player_df = player_df.merge(pd.DataFrame({'name': [p.name for p in player_list],
									'average': [m[0] for m in means_medians], 'median': [m[1] for m in means_medians],
									'forfeits': [p.forfeits for p in player_list], 'blanks': [p.blanks for p in player_list]}).set_index('name'),
									how='outer', left_index=True, right_index=True)

	player_df.to_csv('players.csv')

	print(goals_ap_df)
	return goals_ap_df, player_df


if __name__ == '__main__':
	main()

