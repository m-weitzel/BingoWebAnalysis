from pandas import DataFrame, read_csv

def return_goallist():
	goals_df = read_csv('goals.csv')
	total_races = int(goals_df['count'].sum()/25)
	
	return (list(goals_df.itertuples(index=False, name=None)), total_races)
