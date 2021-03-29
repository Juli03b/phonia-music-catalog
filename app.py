import os
import requests
import info.api as api
from forms import UserForm, PlaylistForm
from sqlalchemy.exc import IntegrityError
from models import connect_db, db, User, Favorite, Playlist, Playlist_song
from flask import Flask, render_template, redirect, request, session, jsonify, flash, abort, url_for, g

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'helep')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///phonia_music')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
db.create_all()

@app.before_request
def authenticate_before_req():
    """Add user object flask global object if user token is in session"""
    
    if 'USER_TOKEN' in session:
        g.user = User.query.get(session['USER_TOKEN'])
    else:
        g.user = None

@app.route('/', methods=['GET'])
def show_home():

    return render_template('home.html', isHome=True)

@app.route('/search', methods=['GET'])
def search_song():
    term = request.args['term']
    req = requests.get(api.SEARCH_URL, headers=api.API_HEADERS, params=dict(term=term))
    songs = req.json()['tracks']['hits']

    return render_template('results.html', songs=songs, term=term)

@app.route('/songs/<int:song_key>', methods=['GET'])
def show_song(song_key):
    req = requests.get(api.SONG_DETAILS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    recommends_req = requests.get(api.SONG_RECOMMENDATIONS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    recommended_songs = recommends_req.json()['tracks']

    if not songs:
        return abort(404)

    return render_template('song.html', song=req.json(), songs=recommended_songs)

@app.route('/sign-up', methods=['GET','POST'])
def sign_up():
    if g.user:
        flash('You have signed up already.', 'dark')
        return redirect('/')

    form = UserForm()

    if form.validate_on_submit():
        user = User.signup(username=form.username.data, password=form.password.data, full_name=form.full_name.data)
        try:
            db.session.commit()
        except IntegrityError:
            flash('That username already exists', 'danger')
            return redirect('/sign-up')

        session['USER_TOKEN'] = user.id
        return redirect('/')

    return render_template('sign-up.html', form=form)

@app.route('/sign-in', methods=['GET','POST'])
def sign_in():
    form = UserForm.sign_in()

    if form.validate_on_submit():

        user = User.authenticate(form.username.data, form.password.data)
        session['USER_TOKEN'] = g.id

        return redirect(url_for(show_home))

    return render_template('sign-in.html', form=form)

@app.route('/favorite', methods=['POST'])
def favorite():
    user = g.user
    song_id = request.json['id']
    song_fav = Favorite(user_id=user.id, song_key=song_id)

    user.favorites.append(song_fav)

    try:
        db.session.commit()

        return jsonify(action='favorited')

    except IntegrityError:
        db.session.rollback()

        song_fav = Favorite.query.filter_by(user_id=user.id, song_key=song_id)
        song_fav.delete()

        db.session.commit()

        return jsonify(action='unfavorited')

@app.route('/favorites')
def show_favorites():
    user = g.user

    if not user:
        flash('Sign up to favorite songs', 'info')
        
        return redirect('/sign-up')

    songs = [get_song(fav.song_key).json() for fav in user.favorites]
    print(songs, 'SONGS')
    return render_template('favorites.html', songs=songs)

@app.errorhandler(404)
def show_not_found(err):
    
    return render_template('404.html')

def get_song(song_key):
    req = requests.get(api.SONG_DETAILS_URL, headers=api.API_HEADERS, params=dict(key=song_key))

    return req