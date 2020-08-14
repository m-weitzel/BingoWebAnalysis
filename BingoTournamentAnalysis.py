from BingoFromAPI import BingoBoard
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pickle
import os
from collections import Counter
import pandas as pd
import numpy as np


def parse_rows(text):
	text = text.lower()
	if any([c in text for c in ['col1', 'col 1', 'c1', 'c 1']]):
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

class TournamentRace:
	def __init__(self, race_room, driver):
		driver.get(f"https://racetime.gg/oot/{race_room}")
		content = driver.page_source
		soup = BeautifulSoup(content, features="html.parser")

		racer_entries = soup.find_all('li', class_='entrant-row')
		self.racer1 = racer_entries[0].find_next('span', class_='name').text
		self.time1 = racer_entries[0].find_next('time', class_='finish-time').text
		self.racer2 = racer_entries[1].find_next('span', class_='name').text
		self.time2 = racer_entries[1].find_next('time', class_='finish-time').text

		try:
			self.row_p1 = parse_rows(racer_entries[0].find_next('span', class_='text').text)
		except AttributeError:
			self.row_p1 = 'a dirty blank'
		try:
			self.row_p2 = parse_rows(racer_entries[1].find_next('span', class_='text').text)
		except AttributeError:
			self.row_p2 = 'a dirty blank'

		if False: #(self.racer2 == 'Myelin') | (self.racer2 == 'Jake Wright'):
			self.racer2 = racer_entries[2].find_next('span', class_='name').text
			self.time2 = racer_entries[2].find_next('time', class_='finish-time').text
			try:
				self.row_p2 = parse_rows(racer_entries[1].find_next('span', class_='text').text)
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


def pull_races(new_rooms):
	chrome_options = Options()
	chrome_options.add_argument("--disable-gpu")
	chrome_options.add_argument("--headless")
	chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

	driver = webdriver.Chrome("/usr/bin/chromedriver", options=chrome_options)
	race_result_list = list()
	for room in new_rooms:
		race_result = TournamentRace(room, driver)
		pickle.dump(race_result, open(f'results/{room}.pickle', 'wb'))
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
		 # 'frantic-heartcontainer-2442', # blinkzy vs. PhoenixFeather
		 # 'overpowered-dampe-7225', # ZAR vs MikeKatz45
		 # 'mysterious-dampe-5521', # Titou vs Coffeepot
		 # 'chaotic-temple-4289', # Gombill vs. Countdown, includes Myelin
		 # 'speedy-wallet-6331', # Timato vs. gc_one
		 # 'brainy-fairy-1215', # Link11 vs. Runnerguy2489, includes Jake Wright
		 # 'lazy-cow-8260', # scaramanga vs. Nalle
		 # 'perfect-anubis-4156', # QuickKiran vs. Chromium_Light
		 # 'witty-nocturne-5332', # Tob3000 vs. PsyMarth
		 # 'clumsy-ganondorf-3762', #AverageGreg vs. MutantAura
		 # 'salty-octorok-5065', # Xanra vs. Myelin
		 # 'scruffy-barinade-0218',  # MatttInTheHat vs. noface099
		 # 'legendary-lullaby-7764',  # Fenyan vs. Davpat
		 # 'fancy-dekutree-7025',  # FantaTanked vs. mgbgnr
		 # 'curious-colossus-9627', #Bonooru vs. Tashman91
		
		
		# Add new races here
	]



	# all_race_results = pull_races(tournament_race_rooms)
	all_race_results = load_races()
	available_goals_list = list()
	picked_goals_list = list()
	list_of_player_names = list()
	player_list = list()
	winning_goals_list = list()

	player_df = pd.DataFrame(columns=['name', 'wins', 'losses']).set_index('name')
	player_df = player_df.append({'name': 'PhoenixFeather', 'wins': 0, 'losses': 0}, ignore_index=True).set_index('name')

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
						p.times.append(race_result.time1)
					else:
						p.rows.append(race_result.row_p1)
					p.seeds.append(race_result.seed)

		else:
			r = Racer(race_result.racer1)
			r.rows.append(race_result.row_p1)
			if race_result.time2 == '—':
				r.times.append('nan')
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
						p.seeds.append(race_result.seed)
		else:
			r = Racer(race_result.racer2)
			r.rows.append(race_result.row_p2)
			if race_result.time2 == '—':
				r.times.append('nan')
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

	available_goals_list = [inner for outer in available_goals_list for inner in outer]
	
	print(available_goals_list)
	goalcounter = Counter(available_goals_list)
	goal_counting_df = pd.DataFrame({'goal': [d[0] for d in goalcounter.items()], 'count': list(goalcounter.values())}).set_index('goal').sort_values('count')

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

	player_df = player_df.merge(pd.DataFrame({'name': [p.name for p in player_list],
									'average': [pd.to_timedelta(p.times).mean() for p in player_list]}).set_index('name'),
									how='outer', left_index=True, right_index=True)
	player_df = player_df.merge(pd.DataFrame({'name': [p.name for p in player_list],
									'average': [pd.to_timedelta(p.times).median() for p in player_list]}).set_index('name'),
									how='outer', left_index=True, right_index=True)

	print(goals_ap_df)
	return goals_ap_df, player_df


if __name__ == '__main__':
	main()

