from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    db.app = app
    db.init_app(app)

class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    full_name = db.Column(db.String(40), nullable=False)

    favorites = db.relationship('Favorite', backref='users', passive_deletes=True)
    playlists = db.relationship('Playlist', backref='user', passive_deletes=True)
    
    def __repr__(self):
        return f'<User id={self.id} username={self.username}>'

    @classmethod
    def signup(cls, username, password, full_name):
        hashed_pass = bcrypt.generate_password_hash(password).decode('UTF-8')
        user = cls(username=username, password=hashed_pass, full_name=full_name)

        db.session.add(user)

        return user
        
    @classmethod
    def authenticate(cls, username, password):
        """Check password, return user if password matches, return False if not."""
        user = cls.query.filter_by(username=username).first()

        if user:
            if bcrypt.check_password_hash(user.password, password):
                return user

        return False
        
    @property
    def favorites_keys(self):
        favs = [fav.song_key for fav in self.favorites]

        return favs

class Favorite(db.Model):

    __tablename__ = 'favorites'

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    song_key = db.Column(db.Integer(), primary_key=True)

    def __repr__(self):
        return f'<Favorite user_id={self.user_id} song_key={self.song_key}>'

class Playlist(db.Model):

    __tablename__ = 'playlists'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True, unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    description = db.Column(db.String(120), nullable=True)

    songs = db.relationship('Playlist_song', backref='playlist', passive_deletes=True)
    
    def __repr__(self):
        
        return f'<Playlist id={self.id} user_id={self.user_id} song_key={self.name} description={self.description}>'

    @property
    def song_keys(self):
        keys = [song.song_key for song in self.songs]

        return keys

class Playlist_song(db.Model):

    __tablename__ = 'playlist_songs'

    playlist_id = db.Column(db.Integer(), db.ForeignKey('playlists.id', ondelete='CASCADE'), primary_key=True)
    song_key = db.Column(db.Integer(), primary_key=True, unique=True)
    
    def __repr__(self):
        return f'<Playlist_song playlist_id={self.playlist_id} song_key={self.song_key}>'
