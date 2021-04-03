import os
import requests
import info.api as api
from info.music_data import GENRES
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
    """Add user object flask global object if user token is in session."""
    
    if 'USER_ID' in session:
        g.user = User.query.get(session['USER_ID'])
    else:
        g.user = None

@app.route('/', methods=['GET'])
def show_home():
    """Show home page."""

    return render_template('home.html', isHome=True, genres=GENRES)

@app.route('/search', methods=['GET'])
def search_song():
    """Search songs using term from GET request.
    Return page without songs if no songs are found."""

    term = request.args.get('term')

    if not term:
        term = list()
        for val in request.args.values():
            term.append(val)
        term = ' '.join(term)

    req = requests.get(api.SEARCH_URL, headers=api.API_HEADERS, params=dict(term=term))
    
    if req.status_code is not 200:
        return render_template('results.html', term=term)

    songs = req.json()['tracks']['hits']
    
    return render_template('results.html', songs=songs, term=term)

@app.route('/songs/<int:song_key>', methods=['GET'])
def show_song(song_key):
    """Show song, along with song recomendations. 404 if song not found."""

    song = get_song(song_key)

    if not song:
        return abort(404, description='Song not found. Try searching instead.')

    recom_req = requests.get(api.SONG_RECOMMENDATIONS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    recom_songs = recom_req.json()
    
    return render_template('song.html', song=song, songs=recom_songs)

@app.route('/artists/<int:artist_id>', methods=['GET'])
def show_artist(artist_id):
    """Show artist and artist top songs."""
    
    return render_template('artist.html', songs=ARTIST_TOP_JSON)

    top_songs = requests.get(api.ARTISTS_TOP_TRACKS_URL, headers=api.API_HEADERS, params=dict(id=artist_id))

    if not top_songs:
        return abort(404, 'Artist not found. Try the searching instead.')

    return render_template('artist.html', songs=top_songs.json())

@app.route('/sign-up', methods=['GET','POST'])
def sign_up():
    """Show/handle signup, depending on request method.
    Redirect if user is signed in, redirect same page if username is taken."""

    if g.user:
        flash('You have signed up already.', 'dark')
        return redirect('/')

    form = UserForm()

    if form.validate_on_submit():
        user = User.signup(username=form.username.data, password=form.password.data, full_name=form.full_name.data)
        try:
            db.session.commit()
        except IntegrityError:
            flash('That username has been taken.', 'dark')
            return redirect('/sign-up')

        session['USER_ID'] = user.id
        return redirect('/')

    return render_template('user/sign-up.html', form=form)

@app.route('/sign-in', methods=['GET','POST'])
def sign_in():
    form = UserForm.sign_in()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            session['USER_ID'] = user.id

            return redirect('/')
        else:
            flash('Username or password is wrong.', 'dark')
            return redirect(url_for('sign_in'))

    return render_template('user/sign-in.html', form=form)

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
    if not user:
        flash('Sign in or sign up to favorite.', 'dark')
        return redirect('/sign-up')

    song_id = request.json['key']
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
    return render_template('user/favorites.html', songs=songs_json)

@app.route('/u/<username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter_by(username=username).first()
    
    if not user:

        return abort(404, description=f"{username} not found.")

    form = UserForm(obj=user)

    if form.validate_on_submit():
        user = User.authenticate(username=user.username, password=form.password.data)

        if user and user.id == g.user.id:
            user.username = form.username.data
            user.full_name = form.full_name.data

            db.session.commit()

            flash('Profile updated.', 'dark')

            return redirect(f'/u/{user.username}')
        else:
            flash('Wrong password.', 'dark')

            return redirect(f'/u/{username}')

    return render_template('user/profile.html', user=user, form=form, fullPlaylistCard=True)

@app.route(f'/u/<username>/playlists', methods=['GET', 'POST'])
def playlists(username):
    """Show playlists and create playlists."""
    user = User.query.filter_by(username=username).first()

    if not user:
        return abort(404, f"{username} not found.")

    form = PlaylistForm()

    if user and g.user and user.id is g.user.id:
        if form.validate_on_submit():
            if user.id is g.user.id:
                playlist = Playlist(user_id=user.id, name=form.name.data, description=form.description.data)

                user.playlists.append(playlist)
                db.session.commit()

                return redirect(f'/u/{user.username}/playlists/{playlist.id}')
            else:
                flash('Sign up to make playlsits.', 'light')

                return redirect('/sign-up')
    else:
        form = False

    return render_template('playlist/playlists.html', form=form, user=user, fullPlaylistCard=True)

@app.route('/u/<username>/playlists/<int:playlist_id>')
def show_playlist(username, playlist_id):
    user = db.session.query(User.id).filter_by(username=username).first()
    playlist = Playlist.query.filter_by(user_id=user.id, id=playlist_id).first()
    songs_json = [get_song(song) for song in playlist.song_keys]

    return render_template('playlist/playlist.html', playlist=playlist, songs=songs_json)

@app.route('/playlists/<int:playlist_id>/delete', methods=['POST'])
def delete_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=g.user.id)
    if not playlist:
        flash('You do not have permission to delete this playlist.' 'dark')
        return redirect(f'/playlists/{playlist_id}')
    
    playlist.delete()
    db.session.commit()

    return redirect(f'/u/{g.user.username}/playlists')

@app.route('/playlists/<int:playlist_id>/add/<song_key>', methods=["POST"])
def playlist(playlist_id, song_key):
    """Add or remove song from playlist with AJAX."""
    user = g.user

    if not user:
        
        return abort(404, "Sign up to favorite songs.")

    playlist = Playlist.query.filter_by(id=playlist_id).first()

    if playlist.user.id is not user.id:

        flash('Not yours!', 'dark')
        return redirect(f'/playlists/<song_id>')
    
    playlist_song = Playlist_song(playlist_id=playlist_id, song_key=song_key)
    playlist.songs.append(playlist_song)

    try:
        db.session.commit()

        return jsonify(action="added")
    except IntegrityError:
        db.session.rollback()
        playlist_song = Playlist_song.query.filter_by(playlist_id=playlist_id, song_key=song_key)
        
        playlist_song.delete()
        db.session.commit()

        return jsonify(action="removed")

@app.errorhandler(404)
def show_not_found(e):
    default_desc = "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."

    if e.description == default_desc:
        e.description = "It seems we can't find what you're looking for, sorry."

    return render_template('404.html', error=e), 404

def get_song(song_key):
    """Returns JSON of API request."""
    req = requests.get(api.SONG_DETAILS_URL, headers=api.API_HEADERS, params=dict(key=song_key))

    return req.json()