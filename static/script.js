async function submitSongFav(id){
    const res = await axios.post('/favorite', {id});

    return res;
}

$('li #fav-song-btn').on('click', async function(evt){
    const songId = $(evt.target).data('song-id');
    const res = await submitSongFav(songId);
    console.log(res)

    if (res.data.action === 'favorited'){
        $(evt.target).removeClass('far fa-star').addClass('fas fa-star');
    }else{
        $(evt.target).removeClass('fas fa-star').addClass('far fa-star');

    }
});