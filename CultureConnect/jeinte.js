var activitesPredefinies = [
    { nom: "Musée du Louvre", photo: "https://media.timeout.com/images/100471869/image.jpg" },
    { nom: "Musée d'Orsay", photo: "https://www.tripsavvy.com/thmb/2puhDfqKvm9vV-fh7vkbp7371aM=/960x0/filters:no_upscale():max_bytes(150000):strip_icc()/TAM_3375-163e8acb0882471880ae1be9009cfe79.jpg" },
    { nom: "Tour Eiffel", photo: "https://evasion-online.com/image-photo/tour+eiffel+photos/Tour%20Eiffel%20depuis%20jardin%20(1)_0.jpg" },
    { nom: "Chateau de Versailles", photo: "https://images.bfmtv.com/Kdt2VS27Ugl77_P2TZhK3sY0BM0=/0x0:2568x1977/2568x0/images/Chateau-de-Versailles-192076.jpg" },
    { nom: "Musée de l'Orangerie", photo: "http://parisdesignagenda.com/wp-content/uploads/2016/03/Orangerie-Museum.jpg" },
    { nom: "Basilique du Sacrée Coeur", photo: "https://th.bing.com/th/id/R.3445076a092259fb7ae9088a0adea4fd?rik=3pU%2fowhuP%2b6tHw&riu=http%3a%2f%2fwww.voyagesbernard.fr%2fwp-content%2fuploads%2fvoyages-bernard-paris-2017-19.jpg&ehk=nxnGrXi9TUjXzz0dS6JgGsK1xia27ZdU8uzU3jBjpiI%3d&risl=&pid=ImgRaw&r=0" },
    { nom: "Musée Rodin", photo: "https://www.sortiraparis.com/images/80/91838/582186-photos-rodin-en-son-jardin-au-musee-rodin-17.jpg" },
    { nom: "Musée d'art Moderne", photo: "https://astelus.com/wp-content/viajes/Musee-d-Art-Moderne-de-la-Ville-de-Paris.jpg" },
    { nom: "Musée Grévin", photo: "https://cdn-static.boursier.com/illustrations/photos/800/grevin2.jpg" },

];

function afficherActivites() {
    var selectedDate = document.getElementById("datePicker").value;

    var activitesMelangees = shuffleArray(activitesPredefinies);
    var nombreActivitesAAfficher = Math.floor(Math.random() * (activitesMelangees.length / 2)) + 1;

    var activitesListe = document.getElementById("activitesListe");
    activitesListe.innerHTML = "";

    var activitesAAfficher = activitesMelangees.slice(0, nombreActivitesAAfficher);

    activitesAAfficher.forEach(function (activitesPredefinies) {
        var listItem = document.createElement("div");
        listItem.className = "list-group-item list-group-item-action";

        var interesses = Math.floor(Math.random() * 20) + 1;

        // Créer un lien avec le nom de l'activité
        var lienActivite = document.createElement("div");
        lienActivite.className = "d-flex w-100 justify-content-between align-items-center";

        var h5 = document.createElement("h5");
        h5.className = "mb-1";
        h5.textContent = activitesPredefinies.nom;
       
        var img = document.createElement("img");
        img.className= "img";
        img.src = activitesPredefinies.photo;
        img.width = "70";
        img.height = "70";
        img.alt = activitesPredefinies.nom;
        
        // Ajouter des icônes de calendrier et de personnes
        var dateIcon = document.createElement("i");
        dateIcon.className = "far fa-calendar-alt";

        var interessesIcon = document.createElement("i");
        interessesIcon.className = "fas fa-users";

       
        lienActivite.appendChild(h5);
       
        // Ajouter la date, le nombre d'intéressés et les icônes
        listItem.appendChild(lienActivite);
        lienActivite.appendChild(img);
        listItem.appendChild(document.createElement("p")).innerHTML = `<span>${selectedDate} - <span>${interesses} personnes intéressés</span>`;

        // Ajouter le bouton "Voir plus"
        var voirPlusButton = document.createElement("button");
        voirPlusButton.className = "openBtn";
        voirPlusButton.textContent = "Intégrer le groupe";
        voirPlusButton.onclick = function () {
            alert(`Plus d'informations sur ${nomActivite}`);
        };

        listItem.appendChild(voirPlusButton);

        activitesListe.appendChild(listItem);
    });

    activitesListe.style.display = "block";
}

function shuffleArray(array) {
    for (var i = array.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
    return array;
}
