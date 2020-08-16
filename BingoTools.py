import pandas as pd
from collections import Counter
import time
import requests
from definitions import ROOT_DIR
import os


class BingoBoard:
	def __init__(self, seed, **kwargs):

		if 'goallist' in kwargs.keys():
			print('Generating board from goal list.')
			goals = kwargs.goallist
		else:
			print(f'Pulling seed {seed}...')
			board = pull_boards_from_api(int(seed))
			goals = board[board['seed'] == int(seed)].goals[0]
			print(f'Completed.')

		self.seed = seed
		self.board = self.load_board(goals)
		self.board_view = self.board[['row', 'goals', 'time w/ base and synergy', 'base time', 'total synergy']].sort_values('time w/ base and synergy')

		pd.options.display.max_columns = None
		pd.options.display.width = None

	def load_board(self, goals):

		board = pd.DataFrame(columns={'row', 'goals'})
		times = self.load_times()

		rows = get_rows(goals)
		for r, goals in rows.items():
			syn = self.calculate_row_synergy(goals, times)
			board = board.append({'row': r, 'goals': goals, 'rowtype synergy': syn[0], 'selfsynergy': syn[1],
								  'type synergy': syn[2], 'subtype synergy': syn[3]},
								 ignore_index=True)

		board['total synergy'] = board.apply(
			lambda r: r['rowtype synergy'] + r['selfsynergy'] + r['type synergy'] + r['subtype synergy'], axis=1)
		board['base time'] = board.apply(lambda row: self.calculate_base_time(row.goals, times), axis=1)
		time_n = lambda t: '%2d:%02d:%02d' % (t // 60, t % 60, t * 100 % 100 / 100 * 60)
		board['time w/ base and synergy'] = board.apply(lambda row: time_n(row['base time'] - row['total synergy']+24.75), axis=1)
		board = board[
			['row', 'goals', 'base time', 'total synergy', 'time w/ base and synergy', 'rowtype synergy', 'type synergy',
			 'subtype synergy', 'selfsynergy']]
		return board

	def load_times(self):
		times = pd.read_csv(os.path.join(ROOT_DIR, 'BingoSheet-v10.csv'))
		# times = times.drop(['\n', 'jp', '#8.4 diff'], axis=1)
		times = times.drop(['jp'], axis=1)
		times = times[[c for c in times.columns if c[:3] != 'inc']]
		# times = times.drop(['legitlacs'], axis=1)
		times = times.drop(0, axis=0)
		times = times[~times['name'].isna()]
		times = times[~(times['name'] == 'New goal ideas')]
		times = times.set_index('name')
		return times

	def calculate_base_time(self, row, times):
		time = 0
		for goal in row:
			time += times.loc[goal]['time']
		return time

	def show_synergies(self, goallist, times):

		synergies = times.drop(['difficulty', 'skill'], axis=1)
		synergies = synergies.drop(['*ms: 9.5', '*bottle: 2', '*hookshot: 2.75', '*gclw: 1'], axis=1)
		synergies = synergies.drop(['selfsynergy'], axis=1)
		synergies = synergies.loc[goallist]
		synergies = synergies.dropna(axis='columns', thresh=2)

		return synergies

	def calculate_row_synergy(self, goallist, times):
		rowtype_synergies = times[['*ms: 9.5', '*bottle: 2', '*hookshot: 2.75', '*gclw: 1']]
		rowtype_synergy = 0
		rowtype_synergy += 9.5-min([9.5, rowtype_synergies['*ms: 9.5'].sum()])
		rowtype_synergy += 2-min([2, rowtype_synergies['*bottle: 2'].sum()])
		rowtype_synergy += 2.75-min([2.75, rowtype_synergies['*hookshot: 2.75'].sum()])
		rowtype_synergy += 1-min([1, rowtype_synergies['*gclw: 1'].sum()])

		selfsynergy = times.loc[goallist]['selfsynergy'].sum()

		# synergies = times.drop(['difficulty', 'time updated', 'skill', '#timey original', '#timey updated'], axis=1)
		synergies = times.drop(['difficulty', 'skill', 'time', '#timey', '#8.4 diff'], axis=1)
		synergies = synergies.drop(['*ms: 9.5', '*bottle: 2', '*hookshot: 2.75', '*gclw: 1', 'selfsynergy'], axis=1)
		synergies = synergies.loc[goallist]
		synergies = synergies.dropna(axis='columns', thresh=2)

		subtype_synergy = 0
		type_synergy = 0

		for c in synergies.columns:
			try:
				type_synergies = synergies.loc[synergies[c].str.find('*') < 0][c]
				if len(type_synergies) > 0:
					if len(type_synergies) > 1:
						this_type_synergies = type_synergies.reindex(type_synergies.astype('float').abs().sort_values(ascending=False).index)
						if c in ['endon']:
							type_synergy += this_type_synergies[1:].astype('float').sort_values(ascending=False)[0].sum()
						else:
							type_synergy += this_type_synergies[1:].astype('float').sum()
					if c in ['childchu', 'botwrupee', 'ganonchu']:
						try:
							subtype_synergy += synergies.loc[synergies[c].str.find('*') == 0][c].str.replace('*','').astype(
								'float').sort_values()[0]
						except IndexError:
							pass
					else:
						sts = lambda x: min(float(max(type_synergies)), x)
						subtype_synergy += synergies.loc[synergies[c].str.find('*') == 0][c].str.replace('*', '').astype('float').apply(sts).sum()

			except AttributeError:
				type_synergies = synergies.loc[~synergies[c].isna()][c]
				if len(type_synergies) > 1:
					this_type_synergies = type_synergies.reindex(type_synergies.astype('float').abs().sort_values(ascending=False).index)
					type_synergy += this_type_synergies[1:].sum()

		return rowtype_synergy, selfsynergy, type_synergy, subtype_synergy


def find_goal_combinations(goallist):
	import itertools
	goal_combinations = list()
	for row in goallist:
		for i in range(2, 6):
			combinations_object = itertools.combinations(row, i)
			goal_combinations += list(combinations_object)
	combi_counter = Counter(goal_combinations)
	combinations_df = pd.DataFrame({'goal combination': [d[0] for d in combi_counter.items()],
	                                'count': [d for d in combi_counter.values()]}).sort_values('count', ascending=False)
	return combinations_df


def get_rows(goallist):
	row1 = [goallist[0], goallist[1], goallist[2], goallist[3], goallist[4]]
	row2 = [goallist[5], goallist[6], goallist[7], goallist[8], goallist[9]]
	row3 = [goallist[10], goallist[11], goallist[12], goallist[13], goallist[14]]
	row4 = [goallist[15], goallist[16], goallist[17], goallist[18], goallist[19]]
	row5 = [goallist[20], goallist[21], goallist[22], goallist[23], goallist[24]]

	col1 = [goallist[0], goallist[5], goallist[10], goallist[15], goallist[20]]
	col2 = [goallist[1], goallist[6], goallist[11], goallist[16], goallist[21]]
	col3 = [goallist[2], goallist[7], goallist[12], goallist[17], goallist[22]]
	col4 = [goallist[3], goallist[8], goallist[13], goallist[18], goallist[23]]
	col5 = [goallist[4], goallist[9], goallist[14], goallist[19], goallist[24]]

	tlbr = [goallist[0], goallist[6], goallist[12], goallist[18], goallist[24]]
	bltr = [goallist[4], goallist[8], goallist[12], goallist[16], goallist[20]]

	return {'row1': row1, 'row2': row2, 'row3': row3, 'row4': row4, 'row5': row5,
	        'col1': col1, 'col2': col2, 'col3': col3, 'col4': col4, 'col5': col5,
	        'tlbr': tlbr, 'bltr': bltr}


def pull_boards_from_api(seeds):
	api_point = 'http://192.168.178.50:3000'

	version = 'v10.0'
	mode = 'normal'
	try:
		str_seeds = ','.join([str(s) for s in seeds])
	except TypeError:
		str_seeds = str(seeds)

	api_boards = requests.get(f'{api_point}?version={version}&mode={mode}&seeds={str_seeds}')

	boards_df = pd.io.json.json_normalize(api_boards.json()['boards'])
	return boards_df


def pull_seed_range(startseed, save=True):

	start = time.time()
	all_seeds = pull_boards_from_api(range(startseed, startseed+100))
	end = time.time()
	print(f'Analyzed seeds {startseed} to {startseed+100}, {(100/(end-start)):.3f} seeds per second.')

	if save:
		goalcounter = Counter(all_seeds.goals.sum())
		goal_counting_df = pd.DataFrame({'goal': [d[0] for d in goalcounter.items()], 'count': list(goalcounter.values())}).set_index('goal').sort_values('count')
		goal_counting_df.to_csv(os.path.join(ROOT_DIR, f'goals/goals{startseed}-{startseed+99}.csv'))

		print(f'Saved seeds {startseed} to {startseed+100}.')