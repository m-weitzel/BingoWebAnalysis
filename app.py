import os
from flask import Flask, render_template
import pickle
from models import return_goallist


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])


@app.route('/', methods=['GET', 'POST'])
def index():
	goal_df_repr = return_goallist()
	# return render_template('index.html', goals=goal_df_repr[0], occ=goal_df_repr[1],
	#									 picks=goal_df_repr[2], pickpct=goal_df_repr[3])
	return render_template('index.html', goals=goal_df_repr)


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


if __name__ == '__main__':
    app.run()
