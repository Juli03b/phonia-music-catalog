// Do favorite song request
async function submitSongFav(key){
    const req = await axios.post('/favorite', {key});

    return req;
}

// Do signout request
async function signOut(){
    await axios.post('/sign-out')
}

// Add song to playlist
async function addSongToPlaylist(playlist_id, song_id){
    const req = await axios.post(`/playlists/${playlist_id}/add/${song_id}`)
    
    return req
}

// Handle favorite button. Grab song_id from button
// Send request and add or remove class
$('li #fav-song-btn, #fav-song-btn').on('click', async function(evt){
    const songKey = $(evt.target).data('song-key');
    const req = await submitSongFav(songKey);

    if (req.data.action === 'favorited'){
        $(evt.target).removeClass('far').addClass('fas');
    }else{
        $(evt.target).removeClass('fas').addClass('far');

    }
});

// Handle signout link. Request signout and refreqh page
$('#sign-out-anchor').on('click', async function(evt){
    evt.preventDefault()
    await signOut()
    window.location.reload()
});

//Handle add song to playlist. Request and toggle classes.
$('li #add-song-playlist').on('click', async function(evt){
    evt.preventDefault()
    const playlistId = $(evt.target).data('playlist-id')
    const songKey = $(evt.target).data('song-key')
    const req = await addSongToPlaylist(playlistId, songKey)
    
    $(evt.target).parent().toggleClass('fas fa-check', () => req.data.action === 'added');

})

feather.replace()

let popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
let popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
  return new bootstrap.Popover(popoverTriggerEl)
})
