
let selectedSlotValue;
const selectElement = document.getElementById('slot');

function confirmSelection(value) {
    selectedSlotValue = value;
}

function setSelection() {
    if (selectElement) {
    selectElement.value = selectedSlotValue;
    }
}

window.setSlotDirectly = function (value) {
  const selectElement = document.getElementById('slot');
  if (selectElement) {
    selectElement.value = value;
  }
}

function closeModal() {

}
