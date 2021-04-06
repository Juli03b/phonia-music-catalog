from unittest import TestCase
from app import db, connect_db, app
from models import User, Favorite, Song, Playlist
from info.api_samples import SONG_JSON

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///phonia_music_test'
app.config['SQLALCHEMY_ECHO'] = False
app.config['WTF_CSRF_ENABLED'] = False

connect_db(app)
db.drop_all()
db.create_all()

class UserViewsTestCase(TestCase):

    def setUp(self):
        User.query.delete()
        Favorite.query.delete()
        Song.query.delete()
        db.session.commit()

        self.username = "TESTINGTON"
        self.user_password = "PASSWARD"
        self.user_full_name = "TEST MAN"
        self.user = User.signup(username=self.username, password=self.user_password, full_name=self.user_full_name)

        db.session.add(self.user)
        db.session.commit()

        self.user_id = self.user.id

    def tearDown(self):
        db.session.rollback()

    def test_signup(self):
        """Test sign up page and signing up."""

        with app.test_client() as client:
            res = client.get('/sign-up')
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Sign Up", html)

            # Testing duplicate username
            data = dict(username=self.username, password=self.user_password, full_name=self.user_full_name)
            res = client.post('/sign-up', data=data, follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("That username has been taken.", html)
            self.assertNotIn("Profile", html)

            # Testing good credentials
            data = dict(username="TESTING", password="TESTOPEST0", full_name="SIR TESTALOT")
            res = client.post('/sign-up', data=data, follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(data["username"], html)
            self.assertIn("Profile", html)
    
    def test_sign_in(self):
        """Test sign in page and signing in."""

        with app.test_client() as client:
            res = client.get('/sign-in')
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Sign In", html)

            # Testing wrong password
            data = dict(username=self.username, password='WRONG PASSWORD')
            res = client.post('/sign-in', data=data, follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertNotIn("Profile", html)

            # Testing correct credentials
            data = dict(username=self.username, password=self.user_password)
            res = client.post('/sign-in', data=data, follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(data["username"], html)

    def test_sign_out(self):
        """Test sign out."""

        with app.test_client() as client:
            res = client.post('/sign-out')

            self.assertEqual(res.status_code, 302)
            
            with client.session_transaction() as session:
                session["USER_ID"] = self.user_id
            
            res = client.post('/sign-out', follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertNotIn(self.username, html)

    def test_favorite(self):
        """Test favoriting."""

        with app.test_client() as client:
            with client.session_transaction() as session:
                session["USER_ID"] = self.user_id

        # Testing favorite with invalid key
        data = dict(key=1)
        res = client.post('/favorite', json=data)

        self.assertEqual(res.status_code, 404)

        # Testing favorite with valid key
        data = dict(key=SONG_JSON["key"])
        res = client.post('/favorite', json=data)
        json = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual("favorited", json["action"])

        # Testing unfavorite
        data = dict(key=SONG_JSON["key"])
        res = client.post('/favorite', json=data)
        json = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual("unfavorited", json["action"])
    
    def test_show_favorites(self):
        """Test favorite page."""

        with app.test_client() as client:
            with client.session_transaction() as session:
                session["USER_ID"] = self.user_id
        
        # Without favorites
        res = client.get("/favorites")
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn("You have <b>no</b> favorite songs.", html)
        
        # With favorites
        favorite = Favorite(user_id=self.user_id, song_key=SONG_JSON["key"])
        song = Song(playlist_id=None, external_song_key=SONG_JSON["key"], song_title=SONG_JSON["title"], song_artist=SONG_JSON["subtitle"])

        db.session.add_all((favorite, song))
        db.session.commit()
        
        res = client.get("/favorites")
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(SONG_JSON["title"], html)
    
    def test_profile(self):
        """Test profile page and updating profile."""

        with app.test_client() as client:
            with client.session_transaction() as session:
                session["USER_ID"] = self.user_id
        
        res = client.get(f'/u/{self.username}')

        self.assertEqual(res.status_code, 200)

        # Incorrect password
        data = dict(username="TESTCHANGEZZZ", password="WRONGPASSWORD")
        res = client.post(f'/u/{self.username}', data=data, follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn("Wrong password.", html)

        # Correct password
        data = dict(username="TESTCHANGES", password=self.user_password)
        res = client.post(f'/u/{self.username}', data=data, follow_redirects=True)
        html = res.get_data(as_text=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn("Profile updated.", html)
        self.assertIn(data["username"], html)

class SongViewsTestCase(TestCase):
    """Test routes that have to do with searching and songs."""

    def test_search_song(self):
        with app.test_client() as client:
            res = client.get("/search", query_string=dict(term="The beatles"))
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("The beatles", html)

    def test_show_song(self):
        with app.test_client() as client:
            res = client.get(f"/songs/{SONG_JSON['key']}")
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(SONG_JSON["title"], html)

    def test_show_artist(self):
        with app.test_client() as client:
            res = client.get(f"/artists/{SONG_JSON['artists'][0]['id']}")
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("D&#39;Angelo", html)

class PlaylistViewsTestCase(TestCase):
    """Test creating playlists, deleting playlists,
    and adding and removing songs from playlists."""

    def setUp(self):
        User.query.delete()
        Playlist.query.delete()
        Song.query.delete()
        db.session.commit()

        self.username = "TESTINGTON"
        self.user_password = "PASSWARD"
        self.user_full_name = "TEST ATON"
        self.user = User.signup(username=self.username, password=self.user_password, full_name=self.user_full_name)

        db.session.add(self.user)
        db.session.commit()
        self.user_id = self.user.id

        self.playlist = Playlist(user_id=self.user_id, name="TESTAPLAYLIST", description="ETSTESTSET")

        db.session.add(self.playlist)
        db.session.commit()
        
        self.playlist_id = self.playlist.id

    def tearDown(self):
        db.session.rollback()

    def test_playlists(self):
        """Test playlists page and creating playlists."""

        with app.test_client() as client:
            with client.session_transaction() as session:
                session["USER_ID"] = self.user_id

            # 1 playlist
            res = client.get(f"/u/{self.username}/playlists")
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("You have 1 playlist.", html)

            # Creating a playlist
            data = dict(name="TESTPLAY", description="TESTING A PLAYLIST")
            res = client.post(f'/u/{self.username}/playlists', data=data,  follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("TESTPLAY", html)

    def test_show_playlist(self):
        with app.test_client() as client:
            res = client.get(f"/u/{self.username}/playlists/{self.playlist.id}")
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(self.playlist.name, html)

    def test_delete_playlist(self):
        """Test deleting a playlist."""

        with app.test_client() as client:
            # Not authorized
            res = client.post(f"/u/{self.username}/playlists/{self.playlist_id}/delete", follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("You do not have permission to delete this playlist.", html)

            with client.session_transaction() as session:
                session["USER_ID"] = self.user_id
            
            # Logged in
            res = client.post(f"/u/{self.username}/playlists/{self.playlist_id}/delete", follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Deleted playlist.", html)
    
    def test_playlist(self):
        """Test adding and removing songs from a playlist."""

        with app.test_client() as client:

            # Not authorized
            res = client.post(f"/u/{self.username}/playlists/{self.playlist_id}/add/{SONG_JSON['key']}")

            self.assertEqual(res.status_code, 401)

            with client.session_transaction() as session:
                session["USER_ID"] = self.user_id

            # Logged in
            res = client.post(f"/u/{self.username}/playlists/{self.playlist_id}/add/{SONG_JSON['key']}")
            json = res.get_json()

            self.assertEqual(res.status_code, 200)
            self.assertIn('added', json['action'])