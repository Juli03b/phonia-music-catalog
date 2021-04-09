import os
import requests
import info.api as api
from info.music_data import GENRES
from forms import UserForm, PlaylistForm
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError
from models import connect_db, db, User, Favorite, Playlist, Song, Play
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
    top_songs = requests.get(api.CHART_SONGS_URL, headers=api.API_HEADERS)

    return render_template('home.html', isHome=True, genres=GENRES, songs=top_songs.json(), isJSON=True)

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

    if req.status_code is not 200 or not req.json():
        return render_template('results.html', term=term)

    songs = req.json()['tracks']['hits']
    artists = req.json()['artists']['hits']

    return render_template('results.html', songs=songs, artists=artists ,term=term, isJSON=True)

@app.route('/songs/<int:song_key>', methods=['GET'])
def show_song(song_key):
    """Show song, along with song recomendations. 404 if song not found."""

    song = get_song(song_key)

    if not song:
        return abort(404, description='Song not found. Try searching instead.')

    recom_req = requests.get(api.SONG_RECOMMENDATIONS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    recom_songs = recom_req.json()
    
    return render_template('song.html', song=song, songs=recom_songs ,isJSON=True)

@app.route('/artists/<int:artist_id>', methods=['GET'])
def show_artist(artist_id):
    """Show artist and artist top songs."""
    
    top_songs = requests.get(api.ARTISTS_TOP_TRACKS_URL, headers=api.API_HEADERS, params=dict(id=artist_id))

    if not top_songs:
        return abort(404, 'Artist not found. Try the searching instead.')

    return render_template('artist.html', songs=top_songs.json(), isJSON=True)

@app.route('/sign-up', methods=['GET','POST'])
def signup():
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
    """Show sign in page and sign in on POST."""

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
    """Sign out."""

    if not g.user:
        flash("You're not signed in.", 'dark')
        return redirect('/')
    
    session.pop('USER_ID')

    return redirect('/')

@app.route('/favorite', methods=['POST'])
def favorite():
    """Favorite a song."""

    user = g.user

    if not user:
        flash('Sign in or sign up to favorite.', 'dark')
        return redirect('/sign-up')

    song_key = request.json['key']
    song_fav = Favorite(user_id=user.id, song_key=song_key)

    add_to_songs(song_key)

    user.favorites.append(song_fav)

    try:
        db.session.commit()

        return jsonify(action='favorited')

    except (IntegrityError, FlushError):
        db.session.rollback()

        song_fav = Favorite.query.filter_by(user_id=user.id, song_key=song_key)
        song_fav.delete()

        db.session.commit()

        return jsonify(action='unfavorited')

@app.route('/favorites')
def show_favorites():
    """Show user's favorite songs."""

    if not g.user:
        flash('Sign up to favorite songs', 'light')

        return redirect('/sign-up')

    fav_songs = db.session.query(Song).join((Favorite, Favorite.song_key==Song.external_song_key)).filter(Favorite.user_id==g.user.id).all()

    return render_template('user/favorites.html', songs=fav_songs)

@app.route('/u/<username>', methods=['GET', 'POST'])
def profile(username):
    """Show user profile page and upadate profile on POST."""

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

    return render_template('user/profile.html', user=user, form=form)

@app.route(f'/u/<username>/playlists', methods=['GET', 'POST'])
def playlists(username):
    """Show playlists and create playlists."""
    user = User.query.filter_by(username=username).first()

    if not user: abort(404, f"{username} not found.")

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

    return render_template('playlist/playlists.html', form=form, user=user)

@app.route('/u/<username>/playlists/<int:playlist_id>')
def show_playlist(username, playlist_id):
    """Show a playlist."""
    
    user = db.session.query(User.id).filter_by(username=username).first()

    if user:
        playlist = Playlist.query.filter_by(user_id=user.id, id=playlist_id).first()

        return render_template('playlist/playlist.html', playlist=playlist, songs=playlist.songs)

    return abort(404, 'User not found.')

@app.route('/u/<username>/playlists/<int:playlist_id>/delete', methods=['POST'])
def delete_playlist(playlist_id, username):
    """Delete playlist."""
    
    user_id = db.session.query(User.id).filter(User.username==username).first()[0]
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=user_id)

    if not g.user or user_id is not g.user.id:
        flash('You do not have permission to delete this playlist.', 'dark')

        return redirect(f'/u/{username}/playlists/{playlist_id}')
    elif not playlist:
        flash('Playlist does not exist.', 'dark')

        return redirect('/')

    playlist.delete()
    db.session.commit()

    flash('Deleted playlist.', 'dark')

    return redirect(f'/u/{g.user.username}/playlists')

@app.route('/playlists/<int:playlist_id>/add/<song_key>', methods=["POST"])
def playlist(playlist_id, song_key):
    """Add or remove song from playlist with AJAX."""
    
    if not g.user: abort(401, "Sign up to favorite songs.") 

    # user_id = db.session.query(User.id).filter(User.username==username).first()
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=g.user.id).first()

    if not playlist: 
        return abort(404, "Playlist not found.")
    elif playlist.user.id is not g.user.id:
        return jsonify(message="Not yours!")
    
    song = Song.query.filter_by(external_song_key=song_key).first()
    playlist_song_keys = [key for (key,) in db.session.query(Song.external_song_key).join(Playlist.songs).filter(Playlist.id==playlist.id).all()]

    if song and song.external_song_key in playlist_song_keys:
        
        db.session.delete(song)
        db.session.commit()

        return jsonify(action="removed")

    song = add_to_songs(song_key=song_key, playlist_id=playlist.id) # 404s if not found

    playlist.songs.append(song)
    db.session.commit()
    
    return jsonify(action="added")

@app.route('/api/add-play', methods=["POST"])
def add_play():
    """Add song play to plays."""

    if not g.user: abort(401, "Sign up to add play.")

    song_key = request.json['key']
    song = add_to_songs(song_key)

    if not song:
        song = Song.query.filter_by(external_song_key=song_key).first()

    play = Play(user_id=g.user.id, song_id=song.id)
    
    db.session.add(play)
    db.session.commit()
    
    return jsonify(action="added")

@app.errorhandler(404)
def show_not_found(e):
    default_desc = "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."

    if e.description == default_desc:
        e.description = "It seems we can't find what you're looking for, sorry."

    return render_template('404.html', error=e), 404

@app.errorhandler(405)
def show_not_found(e):

    return redirect('/')

def get_song(song_key):
    """Returns JSON of API request. 404 if song isn't found."""
    req = requests.get(api.SONG_DETAILS_URL, headers=api.API_HEADERS, params=dict(key=song_key))
    
    if req.status_code is not 200 or not req.json():

        return abort(404, "Song not found.")

    return req.json()

def add_to_songs(song_key, playlist_id=None):
    """Add song to songs if the song doesn't already exist.
    Add song anyway if it's a playlist entry, return song."""

    if not playlist_id and not Song.query.filter_by(external_song_key=song_key).count():
        song = get_song(song_key) # 404 if song not found
        song = Song(external_song_key=song_key, song_title=song["title"], song_artist=song["subtitle"], 
            song_genre=song.get("genres").get("primary"), song_year = song["sections"][0]["metadata"][2].get("text"), 
            cover_url=song["images"]["coverarthq"], preview_url=song["hub"]["actions"][1].get("uri"))

        db.session.add(song)
        db.session.commit()

        return song
    elif playlist_id:
        song = get_song(song_key)
        song = Song(playlist_id=playlist_id, external_song_key=song_key, song_title=song["title"], song_artist=song["subtitle"], 
            song_genre=song.get("genres").get("primary"), song_year = song["sections"][0]["metadata"][2].get("text"), 
            cover_url=song["images"]["coverarthq"], preview_url=song["hub"]["actions"][1].get("uri"))

        db.session.add(song)
        db.session.commit()

        return song
    
    return None