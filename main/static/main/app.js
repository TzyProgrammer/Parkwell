console.log("haziq jomok");
console.log("yang YTTA YTTA aja")

// transfer datepicker into readonly input box
document.addEventListener("DOMContentLoaded", function(){
    const datePickerInput = document.getElementById("default-datepicker")
    const readOnlyInput = document.getElementById("default-date")

    datePickerInput.addEventListener("changeDate", function(event){
        readOnlyInput.value = event.target.value
    })

    datePickerInput.addEventListener("change", function(){
        readOnlyInput.value = datePickerInput.value
    })
});

/*
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('imageUpload').addEventListener('change', function (event) {
        const preview = document.getElementById('preview_image');
        const file = event.target.files[0];

        if (!imageInput) {
            console.error("NO element with ID 'imageUpload' found");
            return;
        }

        if (!preview) {
            console.error("No element with ID 'preview_image' found");
            return;
        }

        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                preview.src = e.target.result;
                preview.classList.remove('hidden');
            }
            reader.readAsDataURL(file)
            console.log("reading file as data URL")
        }
    });
});
*/

// previewing car image
console.log("JS file is loaded")
document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.getElementById('imageUpload');
    const preview = document.getElementById('preview_image');

    if (!imageInput) {
        console.error("❌ No element with ID 'imageUpload' found.");
        return;
    }

    if (!preview) {
        console.error("❌ No element with ID 'preview_image' found.");
        return;
    }

    imageInput.addEventListener('change', function (event) {
        console.log("📷 File input changed");
        const file = event.target.files[0];

        if (!file) {
            console.warn("⚠️ No file selected.");
            return;
        }

        console.log("✅ File selected:", file.name);

        const reader = new FileReader();

        reader.onload = function (e) {
            console.log("📄 FileReader result:", e.target.result.slice(0, 100) + "...");
            preview.src = e.target.result;
            preview.classList.remove('hidden');
            console.log("🖼️ Preview image updated.");
        };

        reader.onerror = function () {
            console.error("❌ Error reading file.");
        };

        reader.readAsDataURL(file);
        console.log("📤 Reading file as data URL...");
    });
});