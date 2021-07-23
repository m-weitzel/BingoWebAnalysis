import requests
import json
from BingoRace import BingoRace
from TournamentAnalysis.BingoTournamentAnalysis import find_goal_combinations, Racer
from collections import Counter
import pandas as pd
from BingoTools import means_medians_from_string_list, is_sarias_row, is_multizl_row
import numpy as np
from datetime import datetime

page = 1
all_relevant_races = []
while True:
	req = requests.get('https://racetime.gg/oot/races/data', params={'page': page})
	data = json.loads(req.content)
	races = data['races']
	page_relevant_races = [r for r in races if ((r['started_at'] > '2020-12-01') & ('bingo' in r['info']) &
	# page_relevant_races = [r for r in races if ((r['started_at'] > '2021-07-16') & ('bingo' in r['info']) &
	                                            ('blackout' not in r['info']) & ('normal' in r['info']))]
	all_relevant_races.extend(page_relevant_races)
	if len(page_relevant_races) < 1:
		break
	page += 1


available_goals_list = list()
picked_goals_list = list()
times_list = list()
player_list = dict()

available_combinations = list()
picked_combinations = list()

player_df = pd.DataFrame(columns=['name']).set_index('name')

print(f'Found {len(all_relevant_races)} races.')

for i, race in enumerate(all_relevant_races):
	br = BingoRace(race)
	room_board = br.board.board
	combis = [find_goal_combinations(sorted(combi_row)) for combi_row in room_board.goals]
	available_combinations.extend(list(pd.concat(combis)['goal combination']))
	available_goals_list.append(room_board.goals[:5].sum())
	for this_row, this_time in zip(br.rows, br.times):
		goals = room_board[room_board.index == this_row]['goals'].to_list()
		if len(goals) > 0:
			picked_goals_list.append(goals[0])
			picked_combinations.extend(list(find_goal_combinations(goals[0])['goal combination']))
			times_list.append(this_time)
		else:
			pass
	for place, (a_racer, a_time, a_row) in enumerate(zip(br.racers, br.times, br.rows)):
		if place == 0:
			win = True
		else:
			win = False
		if a_racer in player_list.keys():
			player_list[a_racer].rows.append(a_row)
			if a_time == '-':
				player_list[a_racer].forfeits += 1
				player_list[a_racer].times.append('nan')
			else:
				player_list[a_racer].times.append(a_time)
				if a_row == 'a dirty blank':
					player_list[a_racer].blanks += 1
				else:
					player_list[a_racer].synergies.append(-room_board.loc[room_board.index == a_row, 'total synergy'].values[0])
					player_list[a_racer].diff_to_estimate.append(br.board.calc_dist_to_estimate(a_row))
					if is_sarias_row(room_board.goals[a_row]):
						player_list[a_racer].sarias += 1
					if is_multizl_row(room_board.goals[a_row]):
						player_list[a_racer].multizl += 1

			if win & br.is_weekly():
				player_list[a_racer].weeklywins += 1
			player_list[a_racer].seeds.append(br.seed)
		else:
			r = Racer(a_racer)
			r.rows.append(a_row)
			if a_time == '-':
				r.forfeits += 1
				r.times.append('nan')
			else:
				r.times.append(a_time)
				if a_row == 'a dirty blank':
					r.blanks += 1
				else:
					r.synergies.append(-room_board.loc[room_board.index == a_row, 'total synergy'].values[0])
					r.diff_to_estimate.append(br.board.calc_dist_to_estimate(a_row))
					if is_sarias_row(room_board.goals[a_row]):
						r.sarias += 1
					if is_multizl_row(room_board.goals[a_row]):
						r.multizl += 1
			if win & br.is_weekly():
				r.weeklywins += 1
			r.seeds.append(br.seed)
			player_list[a_racer] = r
			player_df = player_df.append(pd.DataFrame(index=[a_racer]))
	print(f"Loaded {race['name']} ({i+1}/{len(all_relevant_races)}).")

available_goals_list = [inner for outer in available_goals_list for inner in outer]

goalcounter = Counter(available_goals_list)
goal_counting_df = pd.DataFrame({'goal': [d[0] for d in goalcounter.items()], 'count': list(goalcounter.values())}).set_index('goal').sort_values('count')

picked_goals_list_merged = [inner for outer in picked_goals_list for inner in outer]
picked_goalcounter = Counter(picked_goals_list_merged)
pick_df = pd.DataFrame(
	{'goal': [d[0] for d in picked_goalcounter.items()], 'pick count': list(picked_goalcounter.values())}).set_index(
	'goal')

goals_ap_df = goal_counting_df.merge(pick_df, how='outer', left_index=True, right_index=True).sort_values('count',
                                                                                                          ascending=False)
goals_ap_df['pick count'] = goals_ap_df['pick count'].fillna(0).astype('int')
goals_ap_df['pick%'] = goals_ap_df.apply(lambda r: r['pick count'] / r['count'] * 100, axis=1).round(1)

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


means_medians = [p.calc_mean_median() for p in player_list.values()]

player_df = player_df.merge(pd.DataFrame({'name': [p.name for p in player_list.values()],
                                          'weekly wins': [p.weeklywins for p in player_list.values()],
                                          'races': [len(p.seeds) for p in player_list.values()],
                                          'average': [m[0] for m in means_medians],
                                          'median': [m[1] for m in means_medians],
                                          'forfeits': [p.forfeits for p in player_list.values()],
                                          'blanks': [p.blanks for p in player_list.values()],
                                          'sarias': [p.sarias for p in player_list.values()],
                                          'multizl': [p.multizl for p in player_list.values()],
                                          # 'mean synergy': [np.mean(p.synergies).round(1) for p in player_list],
                                          # 'mean estimate diff': [np.mean(p.diff_to_estimate).round(1) for p in player_list]
                                          'synergy': [-np.mean(p.diff_to_estimate) / 7 * 100 for p in player_list.values()]
                                          }).set_index('name'),
                            how='outer', left_index=True, right_index=True)

goals_ap_df.to_csv('goals.csv')
player_df.to_csv('players.csv')

av_comb_counter = Counter(available_combinations)
available_combinations_df = pd.DataFrame(
	{'goal combination': [d[0] for d in av_comb_counter.items()], 'count': list(av_comb_counter.values())}).set_index(
	'goal combination')
picked_comb_counter = Counter(picked_combinations)
picked_combinations_df = pd.DataFrame(
	{'goal combination': [d[0] for d in picked_comb_counter.items()],
	 'pick count': list(picked_comb_counter.values())}).set_index('goal combination')

combinations_df = available_combinations_df.join(picked_combinations_df,
                                                 how='outer').fillna(0)
combinations_df['pick count'] = combinations_df['pick count'].astype('int')
combinations_df.to_csv('combinations.csv')

timestamp = datetime.now().strftime('%d.%m.%Y, %H:%M:%S')
with open('timestamp.txt', 'w') as f:
	f.write(timestamp)

print('a')
