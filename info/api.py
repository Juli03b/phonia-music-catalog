from info.secrets import API_KEY

"""API urls and headers. Documentation via rapidapi:    https://rapidapi.com/apidojo/api/shazam 

Auto-complete: Get suggestions by word or phrase
Search: Get search results for songs or artists matching input term
Artist top tracks: Get an artist's top tracks using artist id
Song recommendations: Get similar songs from song_key
Song details: Get details of specific song
List charts: Get list of chart ids for countries, cities, or genres
Charts tracks: Get songs that belong to a chart, via chart id

"""

BASE_API_URL = "https://shazam.p.rapidapi.com"

AUTO_COMPLETE_URL = f"{BASE_API_URL}/auto-complete"
SEARCH_URL = f"{BASE_API_URL}/search"
ARTISTS_TOP_TRACKS_URL = f"{BASE_API_URL}/songs/list-artist-top-tracks"
SONG_RECOMMENDATIONS_URL = f"{BASE_API_URL}/songs/list-recommendations"
SONG_DETAILS_URL = f"{BASE_API_URL}/songs/get-details"
LIST_CHARTS_URL = f"{BASE_API_URL}/charts/list"
CHART_SONGS_URL = f"{BASE_API_URL}/charts/track"

API_HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "shazam.p.rapidapi.com"
}

