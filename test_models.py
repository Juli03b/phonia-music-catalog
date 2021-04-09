from unittest import TestCase
from app import db, connect_db, app
from models import User, Favorite, Song, Playlist, Play
from info.api_samples import SONG_JSON

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///phonia_music_test'
app.config['SQLALCHEMY_ECHO'] = False

connect_db(app)
db.drop_all()
db.create_all()

class UserTestCase(TestCase):

    def setUp(self):
        User.query.delete()
        Favorite.query.delete()
        db.session.commit()
        
        self.user_password = '123TESTING'
        self.user_username = 'THISISATEST'
        self.user = User.signup(username=self.user_username, password=self.user_password, full_name='TEST A TEST')

        db.session.add(self.user)
        db.session.commit()

        self.user_id = self.user.id

    def tearDown(self):
        db.session.rollback()

    def test_signup(self):
        """Test signup method."""

        user = User.signup(username="TEST", password="TESTING", full_name="TESTSATEST")
        
        db.session.commit()

        self.assertIsInstance(user, User)
        self.assertIsInstance(user.id, int)
        self.assertEqual(user.username, "TEST")
        self.assertNotEqual(user.password, "TESTING")
        self.assertEqual(user.full_name, "TESTSATEST")

    def test_authenticate(self):
        """Test authentication."""

        user = User.authenticate(username=self.user_username, password=self.user_password)

        self.assertEqual(user, self.user)

        user = User.authenticate(username=self.user_username, password="WRONG PASS")

        self.assertNotEqual(user, self.user)
        self.assertFalse(user)

    def test_favorite_keys(self):
        """Test that user's favorite song keys are returned"""
        
        favorite = Favorite(user_id=self.user_id, song_key=SONG_JSON["key"])

        db.session.add(favorite)
        db.session.commit()

        self.assertIn(int(SONG_JSON['key']), self.user.favorites_keys())

    def test_favorite_genres(self):
        """Test favorite genres."""

        song = Song(external_song_key=SONG_JSON['key'], song_genre=SONG_JSON['genres']['primary'])
        favorite = Favorite(user_id=self.user_id, song_key=SONG_JSON['key'])

        db.session.add_all((song, favorite))
        db.session.commit()

        self.assertIn(SONG_JSON['genres']['primary'], self.user.favorite_genres())

    def test_most_played_songs(self):
        """Test that the most played song's object is returned"""
        
        song = Song(external_song_key=SONG_JSON['key'], song_genre=SONG_JSON['genres']['primary'])

        db.session.add(song)
        db.session.commit()

        play = Play(user_id=self.user.id, song_id=song.id)

        db.session.add(play)
        db.session.commit()

        self.assertIn(song, self.user.most_played_songs())

class FavoriteTestCase(TestCase):
    """Test basic functionality"""

    def setUp(self):
        User.query.delete()
        db.session.commit()
        
        self.user_id = 1
        self.user = User(id=1, username="TEST2", password="TESTSAGAIN", full_name='TEST AGAIN TEST')

        db.session.add(self.user)

        self.song_key = 1
        self.favorite = Favorite(user_id=self.user_id, song_key=self.song_key)
        
        db.session.add(self.favorite)

        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_favorite(self):
        self.assertEqual(self.favorite.song_key, self.song_key)
        self.assertEqual(self.favorite.user_id, self.user_id)
        self.assertEqual(self.user, self.favorite.user)

class PlaylistTestCase(TestCase):
    """Test basic functionality and song relationship."""

    def setUp(self):

        User.query.delete()
        Playlist.query.delete()
        db.session.commit()

        self.user_id = 1
        self.user = User(id=1, username="TEST3", password="TESTSAGAINAGAIN2", full_name='TEST AGAIN2 TEST')

        db.session.add(self.user)

        self.playlist_description = "TEST PLAYLIST"
        self.playlist_name = "TESTING"
        self.playlist_id = 1
        self.playlist = Playlist(id=self.playlist_id, user_id=self.user_id, name=self.playlist_name, description=self.playlist_description)

        db.session.add_all((self.user, self.playlist))
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_playlist(self):
        playlist = Playlist.query.filter_by(user_id=self.user_id).first()

        self.assertEqual(self.playlist, playlist)
        self.assertEqual(self.playlist_name, playlist.name)
        self.assertEqual(self.playlist_description, playlist.description)

    def test_playlist_songs(self):
        song = Song(playlist_id=self.playlist_id)

        db.session.add(song)
        db.session.commit()

        self.assertIn(song, self.playlist.songs)