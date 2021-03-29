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
    
    if 'USER_ID' in session:
        g.user = User.query.get(session['USER_ID'])
    else:
        g.user = None

@app.route('/', methods=['GET'])
def show_home():
    # top_songs = requests.get(api)

    return render_template('home.html', isHome=True)

@app.route('/search', methods=['GET'])
def search_song():
    term = request.args['term']
    req = requests.get(api.SEARCH_URL, headers=api.API_HEADERS, params=dict(term=term))
    
    if req.status_code is not 200:
        return render_template('results.html', term=term)

    songs = req.json()['tracks']['hits']

    return render_template('results.html', songs=songs, term=term)

@app.route('/songs/<int:song_key>', methods=['GET'])
def show_song(song_key):
    """Show song, along with song recomendations. 404 if no songs found."""
    song = get_song(song_key)
    recom_req = requests.get(api.SONG_RECOMMENDATIONS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    recom_songs = recom_req.json()['tracks']

    if not song and not recom_songs:
        return abort(404)

    return render_template('song.html', song=song, songs=recom_songs)

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
            flash('That username has been taken already.', 'dark')
            return redirect('/sign-up')

        session['USER_ID'] = user.id
        return redirect('/')

    return render_template('sign-up.html', form=form)

@app.route('/sign-in', methods=['GET','POST'])
def sign_in():
    form = UserForm.sign_in()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        print(user)
        if user:
            session['USER_ID'] = user.id

            return redirect('/')
        else:
            flash('Username or password is wrong.', 'dark')
            return redirect(url_for('sign_in'))

    return render_template('sign-in.html', form=form)

@app.route('/sign-out', methods=["POST"])
def sign_out():
    if not g.user:
        flash("You're not signed in", 'dark')
        return redirect('/')
    
    session.pop('USER_ID')

    return redirect('/')

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

    if not g.user:
        flash('Sign up to favorite songs', 'light')

        return redirect('/sign-up')

    songs_json = [get_song(fav) for fav in g.user.favorites_keys]
    print(g.user.favorites_keys)

    return render_template('favorites.html', songs=songs_json)

@app.errorhandler(404)
def show_not_found(err):
    
    return render_template('404.html')

def get_song(song_key):
    """Returns json of API request."""
    req = requests.get(api.SONG_DETAILS_URL, headers=api.API_HEADERS, params=dict(key=song_key))

    return req.json()