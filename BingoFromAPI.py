import pandas as pd
from collections import Counter
from joblib import Parallel, delayed
from BingoTools import pull_boards_from_api, pull_seed_range


# for start_of_10k in range(200000, 500000, 10000):
# 	Parallel(n_jobs=2, verbose=1, backend="threading")(map(delayed(pull_seed_range), range(start_of_10k, start_of_10k+10000, 100)))
# 	print(f'{start_of_10k}-{start_of_10k+10000} done.')


for startseed in range(100, 110, 10):
	pull_seed_range(startseed)


