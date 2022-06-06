from BingoTools import BingoBoard
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
import pickle
import os
from collections import Counter
import pandas as pd
import numpy as np
from BingoTools import find_goal_combinations, is_sarias_row, is_multizl_row, is_bit_row, is_lacs_row,\
	means_medians_from_string_list, timestring_from_timedelta
import json
import requests
from datetime import datetime



'''class TournamentRace:
	def __init__(self, race_room, driver, version, filter_list=()):#'Myelin', 'Jake Wright', 'xwillmarktheplace')):
		driver.get(f"https://racetime.gg/oot/{race_room[0]}")
		content = driver.page_source
		soup = BeautifulSoup(content, features="html.parser")

		racer_entries = soup.find_all('li', class_='entrant-row')

		if len(race_room) > 1:
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
		try:
			int(self.seed)
		except ValueError:
			self.seed = soup.find_all('span', class_='info')[0].find_next('a').text.split('=')[-1]
		self.version = version
		self.board = BingoBoard(self.seed, self.version, silent=True)'''


def main():

	version = 'v10.1'
	mode = 'load'

	if mode == 'pull':
		# r1_shorts = load_race_shorts('races/r1.txt')
		# r2_shorts = load_race_shorts('races/r2.txt')
		# tournament_race_rooms = r1_shorts+r2_shorts
		tournament_race_rooms = load_race_shorts('races/r3.txt')
		all_race_results = pull_races_new(tournament_race_rooms, version)
		# all_race_results = pull_races_new([['adequate-water-5607']], version)
	elif mode == 'load':
		r1 = load_races('results/r1')
		r2 = load_races('results/r2')
		r3 = load_races('results/r3')
		all_race_results = r1 + r2 + r3

	available_goals_list = list()
	picked_goals_list = list()
	list_of_player_names = list()
	player_list = list()
	winning_goals_list = list()
	times_list = list()
	available_combinations = list()
	picked_combinations = list()

	player_df = pd.DataFrame(columns=['name', 'wins', 'losses']).set_index('name')
	for race_result in all_race_results:

		print(f'{race_result.racer1} got a {race_result.time1} with {race_result.row_p1}.')
		print(f'{race_result.racer2} got a {race_result.time2} with {race_result.row_p2}.')
		print(f'The seed was {race_result.seed}.')
		room_board = race_result.board.board
		combis = [find_goal_combinations(combi_row) for combi_row in room_board.goals]
		available_combinations.extend(list(pd.concat(combis)['goal combination']))
		available_goals_list.append(room_board.goals[:5].sum())
		try:
			picked_goals_p1 = room_board[room_board.index == race_result.row_p1]['goals'].item()
			picked_goals_list.append(picked_goals_p1)
			picked_combinations.extend(list(find_goal_combinations(picked_goals_p1)['goal combination']))
			times_list.append(race_result.time1)
		except ValueError:
			picked_goals_p1 = []
		try:
			picked_goals_p2 = room_board[room_board.index == race_result.row_p2]['goals'].item()
			picked_goals_list.append(picked_goals_p2)
			picked_combinations.extend(list(find_goal_combinations(picked_goals_p2)['goal combination']))
			times_list.append(race_result.time2)
		except ValueError:
			picked_goals_p2 = []

		if race_result.racer1 in list_of_player_names:
			for p in player_list:
				if p.name == race_result.racer1:
					if (race_result.time1 == '—') | (race_result.time1 == '-'):
						p.times.append('nan')
						p.forfeits += 1
					else:
						p.times.append(race_result.time1)
						if race_result.row_p1 == 'a dirty blank':
							p.blanks += 1
						else:
							p.synergies.append(-room_board.loc[room_board.index == race_result.row_p1, 'total synergy'].values[0])
							p.diff_to_estimate.append(race_result.board.calc_dist_to_estimate(race_result.row_p1))
							if is_sarias_row(picked_goals_p1):
								p.sarias += 1
							if is_multizl_row(picked_goals_p1):
								p.multizl += 1
							if is_lacs_row(picked_goals_p1):
								p.lacs += 1
							if is_bit_row(picked_goals_p1):
								p.bit += 1

					p.rows.append(race_result.row_p1)
					p.seeds.append(race_result.seed)

		else:
			r = Racer(race_result.racer1)
			r.rows.append(race_result.row_p1)
			if (race_result.time1 == '—') | (race_result.time1 == '-'):
				r.times.append('nan')
				r.forfeits += 1
			else:
				r.times.append(race_result.time1)
				if race_result.row_p1 == 'a dirty blank':
					r.blanks += 1
				else:
					r.synergies.append(
						-room_board.loc[room_board.index == race_result.row_p1, 'total synergy'].values[0])
					r.diff_to_estimate.append(race_result.board.calc_dist_to_estimate(race_result.row_p1))
					if is_sarias_row(picked_goals_p1):
						r.sarias += 1
					if is_multizl_row(picked_goals_p1):
						r.multizl += 1
					if is_lacs_row(picked_goals_p1):
						r.lacs += 1
					if is_bit_row(picked_goals_p1):
						r.bit += 1

			r.seeds.append(race_result.seed)

			player_list.append(r)
			list_of_player_names.append(race_result.racer1)
			player_df = player_df.append(pd.DataFrame({'wins': 0, 'losses': 0}, index=[race_result.racer1]))

		if race_result.racer2 in list_of_player_names:
			for p in player_list:
				if p.name == race_result.racer2:
					if (race_result.time2 == '—') | (race_result.time2 == '-'):
						p.times.append('nan')
						p.forfeits += 1
					else:
						p.times.append(race_result.time2)
					p.rows.append(race_result.row_p2)
					if race_result.row_p2 == 'a dirty blank':
						p.blanks += 1
					else:
						p.synergies.append(-room_board.loc[room_board.index == race_result.row_p2, 'total synergy'].values[0])
						p.diff_to_estimate.append(race_result.board.calc_dist_to_estimate(race_result.row_p2))
						if is_sarias_row(picked_goals_p2):
							p.sarias += 1
						if is_multizl_row(picked_goals_p2):
							p.multizl += 1
						if is_bit_row(picked_goals_p2):
							p.bit += 1
						if is_lacs_row(picked_goals_p2):
							p.lacs += 1
					p.seeds.append(race_result.seed)

		else:
			r = Racer(race_result.racer2)
			r.rows.append(race_result.row_p2)
			if race_result.row_p2 == 'a dirty blank':
				r.blanks += 1
			else:
				r.synergies.append(-room_board.loc[room_board.index == race_result.row_p2, 'total synergy'].values[0])
				r.diff_to_estimate.append(race_result.board.calc_dist_to_estimate(race_result.row_p2))
			if (race_result.time2 == '—') | (race_result.time2 == '-'):
				r.times.append('nan')
				r.forfeits += 1
			else:
				r.times.append(race_result.time2)
				if is_sarias_row(picked_goals_p2):
					r.sarias += 1
				if is_multizl_row(picked_goals_p2):
					r.multizl += 1
				if is_lacs_row(picked_goals_p2):
					r.lacs += 1
				if is_bit_row(picked_goals_p2):
					r.bit += 1

			r.seeds.append(race_result.seed)

			player_list.append(r)
			list_of_player_names.append(race_result.racer2)
			player_df = player_df.append(pd.DataFrame({'wins': 0, 'losses': 0}, index=[race_result.racer2]))
		if (race_result.time1 < race_result.time2) | (not(race_result.time2.isnumeric())):
			player_df.loc[race_result.racer1, 'wins'] += 1
			player_df.loc[race_result.racer2, 'losses'] += 1
			try:
				winning_goals_list.append(room_board[room_board.index == race_result.row_p1]['goals'].item())
			except ValueError:
				pass
		else:
			player_df.loc[race_result.racer2, 'wins'] += 1
			player_df.loc[race_result.racer1, 'losses'] += 1
			try:
				winning_goals_list.append(room_board[room_board.index == race_result.row_p2]['goals'].item())
			except ValueError:
				pass

	print(f'Pulled {len(all_race_results)} races.')
	# picked_combinations_df = find_goal_combinations(picked_goals_list)

	available_goals_list = [inner for outer in available_goals_list for inner in outer]

	print(available_goals_list)
	goalcounter = Counter(available_goals_list)
	goal_counting_df = pd.DataFrame({'goal': [d[0] for d in goalcounter.items()], 'count': list(goalcounter.values())}).set_index('goal').sort_values('count')

	picked_goals_list_merged = [inner for outer in picked_goals_list for inner in outer]
	picked_goalcounter = Counter(picked_goals_list_merged)
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

	goal_times_dict = dict()
	sub_115_dict = dict()

	def compare_to_115(time):
		try:
			if pd.to_timedelta(time) < pd.to_timedelta('1:15:00'):
				return True
			else:
				return False
		except ValueError:
			return False

	for row, time in zip(picked_goals_list, times_list):
		for goal in row:
			try:
				goal_times_dict[goal].append(time)
				if compare_to_115(time):
					sub_115_dict[goal] += 1
			except KeyError:
				goal_times_dict[goal] = [time]
				sub_115_dict[goal] = int(compare_to_115(time))

	def get_avg(row):
		try:
			return means_medians_from_string_list(goal_times_dict[row.name])[0]
		except KeyError:
			return 'nan'

	def get_median(goal):
		try:
			return means_medians_from_string_list(goal_times_dict[goal.name])[1]
		except KeyError:
			return 'nan'

	def get_sub_115(goal):
		try:
			return sub_115_dict[goal.name]
		except KeyError:
			return np.nan

	goals_ap_df['median'] = goals_ap_df.apply(get_median, axis=1)
	goals_ap_df['sub 1:15'] = goals_ap_df.apply(get_sub_115, axis=1).fillna(0).astype('int')
	goals_ap_df['sub 1:15 rate'] = goals_ap_df.apply(lambda r: r['sub 1:15']/r['pick count']*100 if r['pick count'] > 0 else 0, axis=1).round(1)
	goals_ap_df = goals_ap_df.sort_values(by='pick%', ascending=False)

	goals_ap_df.to_csv('goals.csv')

	means_medians = [p.calc_mean_median() for p in player_list]
	player_df = player_df.merge(pd.DataFrame({'name': [p.name for p in player_list],
									'average': [m[0] for m in means_medians], 'median': [m[1] for m in means_medians],
									'forfeits': [p.forfeits for p in player_list], 'blanks': [p.blanks for p in player_list],
									'sarias': [p.sarias for p in player_list], 'multizl': [p.multizl for p in player_list],
	                                'bit': [p.bit for p in player_list], 'lacs': [p.lacs for p in player_list],
									# 'mean synergy': [np.mean(p.synergies).round(1) for p in player_list],
									# 'mean estimate diff': [np.mean(p.diff_to_estimate).round(1) for p in player_list]
	                                'synergy': [-np.mean(p.diff_to_estimate)/7*100 for p in player_list]
	                                          }).set_index('name'),
									how='outer', left_index=True, right_index=True)

	player_df.to_csv('players.csv')
	av_comb_counter = Counter(available_combinations)
	available_combinations_df = pd.DataFrame(
		{'goal combination': [d[0] for d in av_comb_counter.items()], 'count': list(av_comb_counter.values())}).set_index('goal combination')
	picked_comb_counter = Counter(picked_combinations)
	picked_combinations_df = pd.DataFrame(
		{'goal combination': [d[0] for d in picked_comb_counter.items()], 'count': list(picked_comb_counter.values())}).set_index('goal combination')

	combinations_df = available_combinations_df.join(picked_combinations_df.rename(columns={'count': 'pick count'}), how='outer').fillna(0)
	combinations_df['pick count'] = combinations_df['pick count'].astype('int')
	combinations_df.to_csv('combinations.csv')

	timestamp = datetime.now().strftime('%d.%m.%Y, %H:%M:%S')
	with open('timestamp.txt', 'w') as f:
		f.write(timestamp)

	print(goals_ap_df)
	return goals_ap_df, player_df

class TournamentRace:
	def __init__(self, race_room, version='v10.1'):
		race = json.loads(requests.get(f"https://racetime.gg/oot/{race_room[0]}/data").content)
		self.racers = []
		self.times = []
		self.rows = []
		race_entrants = race['entrants']
		if len(race_entrants) > 2:
			print(f'More than 2 entrants in this race, pulling {race_entrants[0]} and {race_entrants[1]}.')
		self.racer1 = race_entrants[0]['user']['name']
		self.racer2 = race_entrants[1]['user']['name']
		# timestamp = pd.to_datetime(race['entrants'][0]['finish_time'].split('DT')[1].split('.')[0], format='%HH%MM%S')

		def get_time(entrant):
			timestamp = entrant['finish_time']
			if timestamp is None:
				return '-'
			else:
				return timestamp.split('DT')[1].split('.')[0].replace('H', ':').replace('M', ':')

		def get_row(entrant):
			try:
				return parse_rows(entrant['comment'])
			except AttributeError:
				return 'a dirty blank'

		self.time1 = get_time(race_entrants[0])
		self.time2 = get_time(race_entrants[1])

		self.row_p1 = get_row(race_entrants[0])
		self.row_p2 = get_row(race_entrants[1])

		try:
			self.seed = int(race['info'].split('=')[1].split('&')[0])
		except (IndexError, ValueError):
			self.seed = int(race_room[3])
		self.board = BingoBoard(self.seed, version=version, silent=True)


class Racer:
	def __init__(self, name):
		self.name = name
		self.times = list()
		self.rows = list()
		self.seeds = list()
		self.synergies = list()
		self.diff_to_estimate = list()
		self.forfeits = 0
		self.blanks = 0
		self.sarias = 0
		self.multizl = 0
		self.weeklywins = 0
		self.lacs = 0
		self.bit = 0


	def calc_mean_median(self):
		return means_medians_from_string_list(self.times)


def parse_rows(text):
	text = text.lower()
	if any([c in text for c in {'row1', 'row 1', 'r1', 'r 1'}]):
		return 'row1'
	if any([c in text for c in {'row2', 'row 2', 'r2', 'r 2'}]):
		return 'row2'
	if any([c in text for c in {'row3', 'row 3', 'r3', 'r 3'}]):
		return 'row3'
	if any([c in text for c in {'row4', 'row 4', 'r4', 'r 4'}]):
		return 'row4'
	if any([c in text for c in {'row5', 'row 5', 'r5', 'r 5'}]):
		return 'row5'

	if any([c in text for c in {'col1', 'col 1', 'c1', 'c 1'}]):
		return 'col1'
	if any([c in text for c in {'col2', 'col 2', 'c2', 'c 2'}]):
		return 'col2'
	if any([c in text for c in {'col3', 'col 3', 'c3', 'c 3'}]):
		return 'col3'
	if any([c in text for c in {'col4', 'col 4', 'c4', 'c 4'}]):
		return 'col4'
	if any([c in text for c in {'col5', 'col 5', 'c5', 'c 5'}]):
		return 'col5'

	if any([c in text for c in {'tlbr', 'tl br', 'tl-br'}]):
		return 'tlbr'
	if any([c in text for c in {'bltr', 'bl tr', 'bl-tr'}]):
		return 'bltr'

	return 'a dirty blank'


'''def pull_races(new_rooms, version):
	chrome_options = Options()
	chrome_options.add_argument("--disable-gpu")
	chrome_options.add_argument("--headless")
	chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

	chromedriver_path = 'D:\Programme\chromedriver.exe' if os.name == 'nt' else '/usr/bin/chromedriver'
	driver = webdriver.Chrome(chromedriver_path, options=chrome_options)
	race_result_list = list()
	for room in new_rooms:
		race_result = TournamentRace(room, driver, version=version)
		pickle.dump(race_result, open(f'results/{room[0]}.pickle', 'wb'))
		race_result_list.append(race_result)
	driver.quit()
	return race_result_list'''


def pull_races_new(new_rooms, version):
	race_result_list = []
	for room in new_rooms:
		race_result = TournamentRace(room, version)
		pickle.dump(race_result, open(f'results/{room[0]}.pickle', 'wb'))
		race_result_list.append(race_result)
		print(f'Pulled {room}.')

	return race_result_list


def load_races(dir):
	files = os.listdir(dir)
	loaded_race_results = list()
	for f in files:
		if f.endswith('.pickle'):
			loaded_race_results.append(pickle.load(open(os.path.join(dir, f'{f}'), 'rb')))
	return loaded_race_results


def load_race_shorts(path):
	racenames = []
	with open(path, 'r') as f:
		for line in f:
			# racenames.append([line.split('\'')[1]])
			racenames.append(line.split('\n')[0].split(' #')[0].split(','))
	return racenames


if __name__ == '__main__':
	main()

