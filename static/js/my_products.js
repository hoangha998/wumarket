const editDivs = document.getElementsByClassName("edit");
const deleteDivs = document.getElementsByClassName("delete");

editDivs.forEach((button) => {
  button.addEventListener('click', () => {
    console.log('clicked:' + button.parentNode.parentNode.id)
    toEditForm(button.parentNode.parentNode.id)
  })
})

// deleteDivs.addEventListener('click', toDeleteForm);

function toEditForm(id) {
  window.location.pathname = "/edit" + "/" + id
}