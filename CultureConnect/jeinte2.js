function afficherActivites() {
    // Get the selected date from the date picker
    var selectedDate = document.getElementById("datePicker").value;

    // Assume that you have a function to check if activities exist for the selected date
    var activitiesExist = checkActivitiesForDate(selectedDate);

    // Clear the existing activities list
    var activitesListe = document.getElementById("activitesListe");
    activitesListe.innerHTML = "";

    // Always set the activity name to "football"
    var nomActivite = "Visite";

    if (activitiesExist) {
        // Generate a random boolean value to decide whether to display activity details or not
        var displayActivityDetails = Math.random() < 0.5;

        if (displayActivityDetails) {
            // Display activity details
            var listItem = document.createElement("a");
            listItem.href = "#";
            listItem.className = "list-group-item list-group-item-action";

            var lienActivite = document.createElement("div");
            lienActivite.className = "d-flex w-100 justify-content-between align-items-center";

            var h5 = document.createElement("h5");
            h5.className = "mb-1";
            h5.textContent = nomActivite;

            var dateIcon = document.createElement("i");
            dateIcon.className = "far fa-calendar-alt";

            var interessesIcon = document.createElement("i");
            interessesIcon.className = "fas fa-users";

            lienActivite.appendChild(h5);

            listItem.appendChild(lienActivite);
            listItem.appendChild(document.createElement("p")).innerHTML = `<span>${selectedDate}</span> ${dateIcon.outerHTML} - <span>${getRandomInt(20)} Intéressés</span>`;

            var voirPlusButton = document.createElement("button");
            voirPlusButton.className = "openBtn";
            voirPlusButton.textContent = "Rejoindre le Groupe de visite";
            voirPlusButton.onclick = function () {
                window.location.href = "message.html";
            };

            listItem.appendChild(voirPlusButton);

            // Append the created elements to the activities list
            activitesListe.appendChild(listItem);
        } else {
            // Display a message that there is no activity for the selected date
            var noActivityMessage = document.createElement("p");
            noActivityMessage.textContent = "Pas de visite prévue pour cette date. Vous pouvez soit choisir une autre date, soit crée un nouveau groupe. D'autres utilisateurs seront peut être intéressée! ";

            activitesListe.appendChild(noActivityMessage);
        }
    }

    // Always display the button to create a new activity at the bottom
    var creerActiviteButton = document.createElement("button");
    creerActiviteButton.className = "openBtn";
    creerActiviteButton.textContent = "Créer un nouveau groupe de visite";
    creerActiviteButton.onclick = function () {
        // Add logic to handle the creation of a new activity
        window.location.href = "message.html";
    };

    activitesListe.appendChild(creerActiviteButton);

    // Display the activities list
    activitesListe.style.display = "block";
}

// Example function to check if activities exist for the selected date
function checkActivitiesForDate(date) {
    // Add your logic to check if activities exist for the given date
    // For simplicity, let's assume there are activities for all dates
    return true;
}

// Helper function to get a random integer between 0 and max (inclusive)
function getRandomInt(max) {
    return Math.floor(Math.random() * (max + 1));
}
