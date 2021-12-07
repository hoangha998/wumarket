const favoriteButtons = document.getElementsByClassName("favorite-button")
for (let i=0; i<favoriteButtons.length; i++) {
	favoriteButtons[i].addEventListener('click', () => {
		console.log('clicked:' + favoriteButtons[i].parentNode.parentNode.id)
		toFavorite(favoriteButtons[i].parentNode.parentNode.id)
})
}
function toFavorite(id) {
	window.location.pathname = "/add_favorite" + "/" + id
}



// 
// let sendMessageButtons = document.getElementsByClassName("message-button");
// for (let i=0; i < sendMessageButtons.length; i++) {
// 	let curButton = sendMessageButtons[i];
// 	console.log("adding event listener for ");
// 	console.log(i);
// 	curButton.addEventListener("click", function() {
// 		console.log(curButton.getAttribute('seller_id'));
// 		console.log("send message of item was clicked");
// 		// console.log(curItem.id);
// 	})
// }
