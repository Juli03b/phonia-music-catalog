// Do favorite song request
async function submitSongFav(key){
    const res = await axios.post('/favorite', {key});

    return res;
}

// Do signout request
async function signOut(){
    const res = await axios.post('/sign-out')
}


// Handle favorite button. Grab song_id from button
// Send request and add or remove class
$('li #fav-song-btn, #fav-song-btn').on('click', async function(evt){
    const songKey = $(evt.target).data('song-key');
    const res = await submitSongFav(songKey);

    if (res.data.action === 'favorited'){
        $(evt.target).removeClass('far').addClass('fas');
    }else{
        $(evt.target).removeClass('fas').addClass('far');

    }
});

// Handle signout link. Request signout and refresh page
$('#sign-out-anchor').on('click', async function(evt){
    evt.preventDefault()
    await signOut()
    window.location.reload()
});

$(function() {
    let as = audiojs.createAll();
});