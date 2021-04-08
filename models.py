from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
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

    favorites = db.relationship('Favorite', backref='user', passive_deletes=True)
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

    def favorites_keys(self):
        """Use a SQL query to retrieve favorite song keys."""
        fav_keys = [key[0] for key in db.session.query(Favorite.song_key).join(User.favorites).filter(User.id==self.id).all()]

        return fav_keys

    def favorite_genres(self):
        """Query top 3 genres."""

        fav_genres = db.session.query(Song.song_genre).\
            join(Favorite, Favorite.song_key==Song.external_song_key).\
            group_by(Song.song_genre).\
            order_by(desc(func.count(Song.song_genre))).\
            filter(Favorite.user_id==self.id)

        return [genre for (genre,) in fav_genres.all()]
        
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
    name = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(120), nullable=True)

    songs = db.relationship('Song', backref='playlists', passive_deletes=True)
    
    def __repr__(self):
        
        return f'<Playlist id={self.id} user_id={self.user_id} song_key={self.name} description={self.description}>'


class Song(db.Model):

    __tablename__ = 'songs'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    playlist_id = db.Column(db.Integer(), db.ForeignKey('playlists.id', ondelete='CASCADE'))
    external_song_key = db.Column(db.Integer())
    song_title = db.Column(db.String(50))
    song_artist = db.Column(db.String(50))
    song_genre = db.Column(db.String(50))
    song_year = db.Column(db.String(50))
    cover_url = db.Column(db.String())
    preview_url = db.Column(db.String())
    
    def __repr__(self):
        return f'<Song song_title={self.song_title} song_artist={self.song_artist} song_key={self.external_song_key}>'
