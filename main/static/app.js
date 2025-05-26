console.log("haziq jomok");
console.log("yang YTTA YTTA aja")

document.addEventListener("DOMContentLoaded", function(){
    const datePickerInput = document.getElementById("default-datepicker")
    const readOnlyInput = document.getElementById("default-date")

    datePickerInput.addEventListener("changeDate", function(event){
        readOnlyInput.value = event.target.value
    })

    datePickerInput.addEventListener("change", function(){
        readOnlyInput.value = datePickerInput.value
    })
})