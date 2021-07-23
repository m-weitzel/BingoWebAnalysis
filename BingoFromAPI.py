import pandas as pd
from collections import Counter
from joblib import Parallel, delayed
from BingoTools import pull_boards_from_api, pull_seed_range
import os
from BingoTools import load_times


for start_of_10k in range(200000, 500000, 10000):
	Parallel(n_jobs=4, verbose=1, backend="threading")(map(delayed(pull_seed_range), range(start_of_10k, start_of_10k+10000, 100)))
	print(f'{start_of_10k}-{start_of_10k+10000} done.')


# for startseed in range(0, 1000, 100):
# 	pull_seed_range(startseed)


def merge_csvs():
	csv_path = 'goals'
	files = os.listdir(csv_path)

	goals_df = pd.DataFrame(columns={'goal', 'count'})
	times = load_times()
	for f in files:
		if f.endswith('.csv'):
			new_goals = pd.read_csv(os.path.join(csv_path, f))
			goals_df = goals_df.append(new_goals, ignore_index=True)

	# print(f'Loaded {len(new_goals)} entries from {f}.')

	goals_df = goals_df.groupby('goal').aggregate({'count': 'sum', 'goal': 'first'}).sort_values('count')
	goals_df.to_csv('merged_goals.csv')