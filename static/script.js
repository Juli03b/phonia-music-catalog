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
async function addSongToPlaylist(playlist_id, songKey){
    const req = await axios.post(`/playlists/${playlist_id}/add/${songKey}`)
    
    return req
}

// Add play to plays
async function addPlayerPlay(key){
    await axios.post(`/api/add-play`, {key})
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

// Handle add song to playlist. Request and toggle classes.
$('li #add-song-playlist').on('click', async function(evt){
    evt.preventDefault()

    const playlistId = $(evt.target).data('playlist-id')
    const songKey = $(evt.target).data('song-key')
    const req = await addSongToPlaylist(playlistId, songKey)
    
    $(evt.target).parent().toggleClass('fas fa-check', () => req.data.action === 'added');

})

$(function(){
    const played = [];

    // Handle adding music player clicks
    $('.play').on('click', async function(evt){
        const player_id = $(evt.target).parents().eq(1).attr('id');
        const songKey = $(evt.target).parents().eq(4).children().eq(1).children('#fav-song-btn').data('song-key')

        if(!~played.indexOf(player_id)){
            played.push(player_id);
            await addPlayerPlay(songKey);
        }
    });

    // Activate circleType.js
    document.querySelectorAll('#artist-card-name').forEach(el => {
        const curvedText = new CircleType(el).radius(75);
        let $div = $(curvedText)[0];
        $div = $($div.element).children()[0];
        $($div).css('right', '-180px').css('top', '-13px');
    });
});

feather.replace()

let popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
let popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
  return new bootstrap.Popover(popoverTriggerEl)
})
