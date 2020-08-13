from pandas import DataFrame, read_csv

def return_goallist():
	goals_df = read_csv('goals.csv')
	
	return list(goals_df.itertuples(index=False, name=None))
