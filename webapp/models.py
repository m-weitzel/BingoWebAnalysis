from pandas import DataFrame, read_csv

def return_goallist():
	goals_df = read_csv('../TournamentAnalysis/goals.csv')
	total_races = int(goals_df['count'].sum()/25)
	
	return (list(goals_df.itertuples(index=False, name=None)), total_races)

def return_playerstats():
	player_df = read_csv('../TournamentAnalysis/players.csv')
	return list(player_df.itertuples(index=False, name=None))
