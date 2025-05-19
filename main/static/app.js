console.log("haziq jomok");

function buildStartTime() {
    const dateStr = document.getElementById("default-input").value;
    const hour = document.getElementById("start").value;

    if (!dateStr || !hour) {
        console.log("Missing date or hour.");
        return;
    }

    const parsedDate = new Date(dateStr);
    const year = parsedDate.getFullYear();
    const month = String(parsedDate.getMonth() + 1).padStart(2, '0');
    const day = String(parsedDate.getDate()).padStart(2, '0');
    const paddedHour = hour.padStart(2, '0');

    const datetimeStr = `${year}-${month}-${day}T${paddedHour}:00`;

    console.log("Generated start_time:", datetimeStr); // ← this prints to the browser console

    document.getElementById("start_time_field").value = datetimeStr;
}