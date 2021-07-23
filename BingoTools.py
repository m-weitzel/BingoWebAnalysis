import pandas as pd
from collections import Counter
import time
import requests
from definitions import ROOT_DIR
import os
import numpy as np


class BingoBoard:
	def __init__(self, seed, version='v10.1', silent=False, **kwargs):

		if 'goallist' in kwargs.keys():
			print('Generating board from goal list.')
			goals = kwargs['goallist']
		else:
			if not silent:
				print(f'Pulling seed {seed}...')
			board = pull_boards_from_api(int(seed), version=version)
			goals = board[board['seed'] == int(seed)].goals[0]
			if not silent:
				print(f'Completed.')

		self.seed = seed
		self.version = version
		self.board = self.load_board(goals)
		self.board_view = self.board[['goals', 'time w/ base and synergy', 'base time', 'total synergy']].sort_values('time w/ base and synergy')

		pd.options.display.max_columns = None
		pd.options.display.width = None
		if not silent:
			print(self.board_view)

	def load_board(self, goals):

		board = pd.DataFrame(columns={'row', 'goals'})
		times = self.load_times_new()

		rows = get_rows(goals)
		for r, goals in rows.items():
			# syn = self.calculate_row_synergy(goals, times)
			syn = self.calculate_row_synergy_new(goals)
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
		board = board.set_index('row')
		return board

	def load_times(self):
		if self.version == 'v10':
			times = pd.read_csv(os.path.join(ROOT_DIR, 'BingoSheet-v10.csv'))
		else:
			times = pd.read_csv(os.path.join(ROOT_DIR, 'BingoSheet-v10.1.csv'))

		# times = times.drop(['\n', 'jp', '#8.4 diff'], axis=1)
		times = times.drop(['jp'], axis=1)
		times = times.drop(['legitlacs'], axis=1)               # this does weird things with synergy calculation, probably should be done for all inc synergies as well
		times = times[[c for c in times.columns if c[:3] != 'inc']]
		times = times.drop(0, axis=0)
		times = times[~times['name'].isna()]
		times = times[~(times['name'] == 'New goal ideas')]
		times = times.set_index('name')
		return times

	def load_times_new(self):
		data = pd.read_json(f'D:/Programmierung/Python/BingoWebAnalysis/{self.version}.json')

		all_goals = data['normal'].drop(
			['combined', 'version', 'info', 'rowtypes', 'synfilters', 'averageStandardDeviation'])
		goallist_df = pd.DataFrame()
		for goals_by_diff in all_goals:
			goallist_df = pd.concat([goallist_df, pd.json_normalize(goals_by_diff)])

		goallist_df = goallist_df.set_index('name')
		goallist_df = goallist_df.drop(['id', 'jp', 'weight', 'types.legitlacs'], axis=1)

		return goallist_df

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

		selfsynergy = times.reindex(goallist)['selfsynergy'].sum()

		# synergies = times.drop(['difficulty', 'time updated', 'skill', '#timey original', '#timey updated'], axis=1)
		if self.version == 'v10':
			synergies = times.drop(['difficulty', 'skill', 'time', '#timey', '#8.4 diff'], axis=1)#, '#8.4 diff'], axis=1)
		else:
			synergies = times.drop(['difficulty', 'skill', 'time', '#timey'], axis=1)
		synergies = synergies.drop(['*ms: 9.5', '*bottle: 2', '*hookshot: 2.75', '*gclw: 1', 'selfsynergy'], axis=1)
		# print(goallist)
		synergies = synergies.loc[goallist]
		synergies = synergies.dropna(axis='columns', thresh=2)

		subtype_synergy = 0
		type_synergy = 0

		for c in synergies.columns:
			try:
				type_synergies = synergies.loc[synergies[c].str.find('*') < 0][c]
				if len(type_synergies) > 0:
					if len(type_synergies) > 1:
						if c in ['endon']:
							this_type_synergies = type_synergies.reindex(type_synergies.astype('float').sort_values(ascending=True).index)
							type_synergy += this_type_synergies[1:].astype('float').sum()
						else:
							this_type_synergies = type_synergies.reindex(type_synergies.astype('float').sort_values(ascending=False).index)
							# if not any(this_type_synergies>'0'):
							# 	if any(this_type_synergies == '0'):
							# 		type_synergy += this_type_synergies.astype('float').sum()
							# 	else:
							# 		type_synergy += this_type_synergies.astype('float').sort_values(ascending=True)[1:].sum()
							# else:
							type_synergy += this_type_synergies[1:].astype('float').sum()
					if c in ['childchu', 'botwrupee', 'ganonchu']:
						try:
							subtype_synergy += synergies.loc[synergies[c].str.find('*') == 0][c].str.replace('*', '', regex=False).astype(
								'float').sort_values(ascending=True)[0]
						except IndexError:
							pass
					else:
						sts = lambda x: min(float(max(type_synergies)), x)
						subtype_synergy += synergies.loc[synergies[c].str.find('*') == 0][c].str.replace('*', '', regex=False).astype('float').apply(sts).sum()

			except AttributeError:
				type_synergies = synergies.loc[~synergies[c].isna()][c]
				if len(type_synergies) > 0:
					if len(type_synergies) > 1:
						if c in ['endon']:
							this_type_synergies = type_synergies.reindex(type_synergies.astype('float').sort_values(ascending=True).index)
							type_synergy += this_type_synergies[1:].astype('float').sum()
						else:
							this_type_synergies = type_synergies.reindex(type_synergies.astype('float').sort_values(ascending=False).index)
							# if not any(this_type_synergies>'0'):
							# 	if any(this_type_synergies == '0'):
							# 		type_synergy += this_type_synergies.astype('float').sum()
							# 	else:
							# 		type_synergy += this_type_synergies.astype('float').sort_values(ascending=True)[1:].sum()
							# else:
							type_synergy += this_type_synergies[1:].astype('float').sum()
					# if c in ['childchu', 'botwrupee', 'ganonchu']:
					# 	try:
					# 		subtype_synergy += synergies.loc[synergies[c].str.find('*') == 0][c].str.replace('*','').astype(
					# 			'float').sort_values(ascending=False)[0]
					# 	except IndexError:
					# 		pass
					# else:
					# 	sts = lambda x: min(float(max(type_synergies)), x)
					# 	subtype_synergy += synergies[c][1:].astype('float').sum()

		return rowtype_synergy, selfsynergy, type_synergy, subtype_synergy

	def calculate_row_synergy_new(self, goallist):

		# data = pd.read_json('D:/Programmierung/Python/BingoWebAnalysis/10-1.json')
		data = pd.read_json(f'D:/Programmierung/Python/BingoWebAnalysis/{self.version}.json')

		all_goals = data['normal'].drop(
			['combined', 'version', 'info', 'rowtypes', 'synfilters', 'averageStandardDeviation'])
		goallist_df = pd.DataFrame()
		for goals_by_diff in all_goals:
			goallist_df = pd.concat([goallist_df, pd.json_normalize(goals_by_diff)])

		goallist_df = goallist_df.set_index('name')
		goallist_df = goallist_df.drop(['id', 'jp', 'weight', 'types.legitlacs'], axis=1)

		types = {}
		subtypes = {}
		rowtypes = {}
		selfsynergy = 0

		for this_goal in goallist:
			this_synergies = goallist_df.loc[this_goal].dropna().drop(['time', 'skill', 'difficulty'])
			selfsynergy += this_synergies['types.selfsynergy']
			this_synergies = this_synergies.drop('types.selfsynergy')

			new_rowtypes = {}
			new_subtypes = {}
			new_types = {}

			for syntime, syn in zip(this_synergies, this_synergies.index):
				direction = syn[0]
				new_entry = {syn.split('.')[1]: syntime}

				if direction == 'r':
					new_rowtypes = {**new_rowtypes, **new_entry}
				elif direction == 's':
					new_subtypes = {**new_subtypes, **new_entry}
				elif direction == 't':
					new_types = {**new_types, **new_entry}

			for syn, new_typesyntime in zip(new_types.keys(), new_types.values()):
				if syn in types.keys():
					types[syn].append(new_typesyntime)
				else:
					types[syn] = [new_typesyntime]

			for syn, new_subtypesyntime in zip(new_subtypes.keys(), new_subtypes.values()):
				if syn in subtypes.keys():
					subtypes[syn].append(new_subtypesyntime)
				else:
					subtypes[syn] = [new_subtypesyntime]

			for syn, new_rowtypesyntime in zip(new_rowtypes.keys(), new_rowtypes.values()):
				if syn in rowtypes.keys():
					rowtypes[syn].append(new_rowtypesyntime)
				else:
					rowtypes[syn] = [new_rowtypesyntime]

		total_rowtypesynergy = 0
		total_typesynergy = 0
		total_subtypesynergy = 0
		for typesyn_key, typesyn_vals in zip(types.keys(), types.values()):
			sorted_vals = sorted(typesyn_vals)
			if typesyn_key == 'endon':
				total_typesynergy += np.sum(sorted_vals[:-1])
			else:
				total_typesynergy += np.sum(sorted_vals[:-1])
			if typesyn_key in subtypes.keys():
				subtype_synergies = subtypes[typesyn_key]
				if not np.any([s > 0 for s in subtype_synergies]):
					total_subtypesynergy += np.min(subtype_synergies)
				else:
					total_subtypesynergy += np.sum([min(np.min(typesyn_vals), subtime) for subtime in subtype_synergies])

		rowtypes_bases = {'bottle': 2, 'gclw': 1, 'ms': 9.5, 'bottle': 2, 'hookshot': 2.75}
		for rowtypesyn_key, rowtypesyn_vals in zip(rowtypes.keys(), rowtypes.values()):
			this_rowtype_sum = np.sum(rowtypesyn_vals)
			base = rowtypes_bases[rowtypesyn_key]
			if np.sum(rowtypesyn_vals) < base:
				total_rowtypesynergy += base - this_rowtype_sum

		synergies_dict = {'rowtype_synergy': total_rowtypesynergy, 'selfsynergy': selfsynergy,
		                  'type_synergy': total_typesynergy, 'subtype_synergy': total_subtypesynergy}

		return tuple(synergies_dict.values())

	def calc_dist_to_estimate(this, comp_time):
		this_timedelta = pd.to_timedelta(
			this.board.loc[this.board.index == comp_time, 'time w/ base and synergy'].values[0])
		estimate = pd.to_timedelta('1:13:30')

		if estimate.total_seconds() > this_timedelta.total_seconds():
			delta = -((estimate - this_timedelta).components.minutes + (
						estimate - this_timedelta).components.seconds / 60)
		# return '-'+timestring_from_timedelta(estimate-this_timedelta)
		else:
			delta = (this_timedelta - estimate).components.minutes + (this_timedelta - estimate).components.seconds / 60
		# return timestring_from_timedelta(this_timedelta-estimate)
		return delta


def find_goal_combinations(goallist):
	import itertools
	goal_combinations = list()
	for i in range(2, 4):
		combinations_object = itertools.combinations([g.replace('\'', '') for g in goallist], i)
		goal_combinations += [sorted(o) for o in combinations_object]
	combi_counter = Counter([str(g) for g in goal_combinations])
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


def pull_boards_from_api(seeds, version):
	# api_point = 'http://192.168.178.50:3000'
	api_point = 'http://akihabara:3000'

	mode = 'normal'
	try:
		str_seeds = ','.join([str(s) for s in seeds])
	except TypeError:
		str_seeds = str(seeds)

	api_boards = requests.get(f'{api_point}?version={version}&mode={mode}&seeds={str_seeds}')

	boards_df = pd.json_normalize(api_boards.json()['boards'])
	return boards_df


def pull_seed_range(startseed, save=True):

	start = time.time()
	all_seeds = pull_boards_from_api(range(startseed, startseed+100), version='v10.1')
	end = time.time()
	print(f'Analyzed seeds {startseed} to {startseed+100}, {(100/(end-start)):.3f} seeds per second.')

	if save:
		goalcounter = Counter(all_seeds.goals.sum())
		goal_counting_df = pd.DataFrame({'goal': [d[0] for d in goalcounter.items()], 'count': list(goalcounter.values())}).set_index('goal').sort_values('count')
		goal_counting_df.to_csv(os.path.join(ROOT_DIR, f'goals/goals{startseed}-{startseed+99}.csv'))

		print(f'Saved seeds {startseed} to {startseed+100}.')


def load_times(version):
	times = pd.read_csv(os.path.join(ROOT_DIR, f'BingoSheet-{version}.csv'))
	# times = pd.read_csv(os.path.join(ROOT_DIR, 'Bingo Sheet - Bingo sheet.csv'))
	times = times.drop(['\n', 'jp', '#8.4 diff'], axis=1)
	times = times[[c for c in times.columns if c[:3] != 'inc']]
	times = times.drop(['legitlacs'], axis=1)
	times = times.drop(0, axis=0)
	times = times[~times['name'].isna()]
	times = times[~(times['name'] == 'New goal ideas')]
	times = times.set_index('name')
	return times


def classify_row(row):
	row = set([g.lower() for g in row])

	rowtype_list = ['saw rba', 'deep fire', 'deep shadow', 'deep spirit', 'trials', 'child zl', 'back in time', 'colored gauntlets',
					'lacs ba', 'water temple', 'collection']

	rowtype_df = pd.DataFrame([[0]*len(rowtype_list)], columns=rowtype_list)

	rowtype_df.loc[0]['deep fire'] = len(row.intersection(['defeat volvagia', 'defeat both flare dancers',
															'megaton mammer', 'get to the end of water trial',
															'get to the end of shadow trial', 'open all 6 gold rupee chests'
															]))
	rowtype_df.loc[0]['deep shadow'] = len(row.intersection(['all 5 skulltulas in shadow temple', 'obtain all 5 small keys in shadow temple',
															]))

	rowtype_df.loc[0]['deep shadow'] = len(row.intersection(['all 5 skulltulas in spirit temple', 'defeata nabooru knuckle',
															 'spirit boss key', 'beat the spirit temple', 'defeat twin rova',
															]))

	rowtype_df.loc[0]['trials'] = len(row.intersection(['get to the end of forest trial', 'get to the end of fire trial',
														'get to the end of water trial', 'get to the end of shadow trial',
														'get to the end of spirit trial', 'get to the end of light trial',
														'ganon\'s castle boss key','7 different bottled contents']))

	rowtype_df.loc[0]['saw rba'] = len(row.intersection(['double magic', 'double defense', 'two fairy spells', 'nayru\'s love',
														'farore\'s wind',
														'all 5 skulltulas in shadow temple', 'obtain all 5 small keys in shadow temple',
														'map \& compass in spirit temple', 'all 5 skulltulas in water temple',
														'get to the end of light trial', '8 songs', '9 songs', '10 songs',
														'spirit temple boss key', 'all 3 elemental arrows', 'spirit temple boss key',
														]))

	rowtype_df.loc[0]['back in time'] = len(row.intersection(['all 4 market area skulltulas', 'frog\'s hp',
															 ]))

	rowtype_df.loc[0]['child zl'] = len(row.intersection(['din\'s fire', 'saria\'s song', 'goron bracelet', 'green gauntlets'
															 ]))

	rowtype_df.loc[0]['water temple'] = len(row.intersection(['3 skulltulas in water temple', 'all 5 skulltulas in water temple',
															  'longshot', 'defeat dark link',
															 ]))

	rowtype_df.loc[0]['collection'] = len(row.intersection(['6 hearts', '7 hearts', '8 hearts (no duping)', '9 hearts (no duping)',
															'5 compasses', '6 compasses', '7 compasses',
															'5 maps', '6 maps', '7 maps',
															'15 different skulltulas', '30 different skulltulas', 'stone of agony'
															]))

	return rowtype_df


def is_sarias_row(goallist):
	sarias_goals = set([g.lower() for g in goallist]).intersection(['both hps in lost woods', 'saria\'s song', 'goron bracelet',
											'green gauntlets'])
	if len(sarias_goals) > 0:
		return True
	else:
		return False


def is_multizl_row(goallist):
	zl_goals = set([g.lower() for g in goallist]).intersection(['both hps in lost woods', 'saria\'s song', 'goron bracelet',
											'green gauntlets', 'double magic', 'double defense', 'two fairy spells', 'nayru\'s love',
											'farore\'s wind',
											'all 5 skulltulas in shadow temple', 'obtain all 5 small keys in shadow temple',
											'map \& compass in spirit temple', 'all 5 skulltulas in water temple',
											'get to the end of light trial', '6 songs', '7 songs', '8 songs', '9 songs', '10 songs',
											'spirit temple boss key', 'all 3 elemental arrows', 'spirit temple boss key',])
	if len(zl_goals) > 1:
		return True
	else:
		return False


def means_medians_from_string_list(times_list):
	actual_times = list()
	for t in times_list:
		if t is not 'nan' and t != '—' and t != '-':
			actual_times.append(t)
	if len(actual_times) < 1:
		return 'nan', 'nan'
	else:
		actual_times = pd.to_timedelta(actual_times)
		if actual_times.mean().components.days < 0:
			mean_dt = (pd.to_timedelta('00:00:00') - actual_times.mean()).components
			mean_string = f'-{mean_dt.hours}:{str(mean_dt.minutes).zfill(2)}:{str(mean_dt.seconds).zfill(2)}'
		else:
			mean_dt = actual_times.mean().components
			mean_string = f'{mean_dt.hours}:{str(mean_dt.minutes).zfill(2)}:{str(mean_dt.seconds).zfill(2)}'
		if actual_times.median().components.days < 0:
			median_dt = (pd.to_timedelta('00:00:00') - actual_times.mean()).components
			median_string = f'-{median_dt.hours}:{str(median_dt.minutes).zfill(2)}:{str(median_dt.seconds).zfill(2)}'
		else:
			median_dt = actual_times.median().components
			median_string = f'{median_dt.hours}:{str(median_dt.minutes).zfill(2)}:{str(median_dt.seconds).zfill(2)}'

		return mean_string, median_string


def timestring_from_timedelta(timedelta):
	timedelta = timedelta.components
	return f'{timedelta.hours}:{str(timedelta.minutes).zfill(2)}:{str(timedelta.seconds).zfill(2)}'


def compare_versions(seed, version_tuple=('v10', 'v10.1')):
	b_1 = BingoBoard(seed, version=version_tuple[0])
	b_2 = BingoBoard(seed, version=version_tuple[1])

	comp = pd.DataFrame({'row': b_1.board['row'], version_tuple[0]: b_1.board['time w/ base and synergy'],
                         version_tuple[1]: b_2.board['time w/ base and synergy']})

	return comp

