import os
import requests
import info.api as api
from forms import UserForm, PlaylistForm
from models import connect_db, db, User, Favorite, Playlist, Playlist_song
from flask import Flask, render_template, redirect, request, session, jsonify, abort, url_for,g as global_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'helep'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///phonia_music')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
db.create_all()

@app.before_request
def authenticate_before_req():
    """Add user object flask global object if user token is in session"""
    
    if 'USER_TOKEN' in session:
        user = User.query.get(session['USER_TOKEN'])

        global_ = user
    else:

        global_ = None

@app.route('/', methods=['GET'])
def show_home():

    return render_template('home.html', isHome=True)

@app.route('/search', methods=['GET'])
def search_song():
    term = request.args['term']
    req = requests.get(api.SEARCH_URL, headers=api.API_HEADERS, params=dict(term=term))
    songs = req.json()['tracks']['hits']

    return render_template('results.html', songs=songs)

@app.route('/songs/<int:song_key>', methods=['GET'])
def show_song(song_key):
    req = requests.get(api.SONG_DETAILS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    recommends_req = requests.get(api.SONG_RECOMMENDATIONS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    songs = recommends_req.json()['tracks']

    if not songs:
        return abort(404)

    return render_template('song.html', song=req.json(), songs=songs)

@app.route('/sign-up', methods=['GET','POST'])
def sign_up():
    form = UserForm()

    if form.validate_on_submit():
        user = User.signup(username=form.username.data, password=form.password.data, full_name=form.full_name.data)

        db.session.commit()

        return redirect('/')

    return render_template('sign-up.html', form=form)

@app.route('/sign-in', methods=['GET','POST'])
def sign_in():
    form = UserForm.sign_in()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        session['USER_TOKEN'] = user.id
        print('HERE')
        print(user, url_for(show_home))

        return redirect(url_for(show_home))

    print('no submit')
    return render_template('sign-in.html', form=form)

@app.errorhandler(404)
def show_not_found(err):
    return render_template('404.html')