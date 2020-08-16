import os
from flask import Flask, render_template
from webapp.models import return_goallist, return_playerstats


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])


@app.route('/')
def index():
	goal_df_repr, total_races = return_goallist()
	# return render_template('index.html', goals=goal_df_repr[0], occ=goal_df_repr[1],
	#									 picks=goal_df_repr[2], pickpct=goal_df_repr[3])
	return render_template('index.html', goals=goal_df_repr, total_races=total_races)
	
@app.route('/players')
def player_index():
    players_repr = return_playerstats()
    return render_template('player_index.html', players=players_repr)


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


if __name__ == '__main__':
    app.run()
