import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.3/firebase-app.js' 
import {getDatabase, ref , child , get , query , orderByChild , equalTo ,push, set} from 'https://www.gstatic.com/firebasejs/9.6.3/firebase-database.js'
// TODO: Replace the following with your app's Firebase project configuration
const firebaseConfig = {
    apiKey: "AIzaSyDrUZ7SdmGYarxvIN7ikrUr5AzKeDIScW8",
    authDomain: "cultureapp-a1c9c.firebaseapp.com",
    databaseURL: "https://cultureapp-a1c9c-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "cultureapp-a1c9c",
    storageBucket: "cultureapp-a1c9c.appspot.com",
    messagingSenderId: "885088600367",
    appId: "1:885088600367:web:2b5d6f33e92435849fe1da",
    measurementId: "G-PQ7DPJJJFT"
  };
  
  // Initialize Firebase
  const app = initializeApp(firebaseConfig)
  var liste_lieux=document.getElementById("row")
  var database = getDatabase(app)
    liste_lieux.innerHTML=""
    var lieuxRef = ref(database,"sites_culturels")
    get((lieuxRef))
    .then( (snapshot)=>{
            snapshot.forEach(childSnapshot => {
            var place = childSnapshot.val()
            var id = childSnapshot.key
            ajouter_element_liste(place,id)

            
        });

    })
     



function ajouter_element_liste(place,id){
    let new_Elementmd4=document.createElement("div")
    new_Elementmd4.className="col-md-4"
    let new_Elementmb4box=document.createElement("div")
    new_Elementmb4box.className="card mb-4 box-shadow"
    let img_place=document.createElement("img")
    img_place.className="card-img-top"
    let new_Elementcardbody=document.createElement("div")
    new_Elementcardbody.className="card-body"
    let nom_place=document.createElement("h5")
    nom_place.innerText=place.nom_etablissement
    let description_place=document.createElement("p")
    description_place.innerText=place.description
    description_place.className="card-text"
    let new_Elementjustifycontent=document.createElement("div")
    new_Elementjustifycontent.className="d-flex justify-content-between align-items-center"
    let new_Elementbtngrp=document.createElement("div")
    new_Elementbtngrp.className="btn-group"
    let btn_voirplus=document.createElement("button")
    btn_voirplus.className="btn btn-sm btn-outline-secondary"
    let btn_interesse=document.createElement("button")
    
    let place_link =document.createElement("a")
    place_link.setAttribute("href","lieubis2.html?id="+encodeURI(id))
    place_link.textContent="Voir plus"
    
    img_place.setAttribute("src",place.image)
    img_place.setAttribute("alt",place.description_image)
    btn_voirplus.append(place_link)
    new_Elementbtngrp.append(btn_voirplus)
  
    new_Elementjustifycontent.append(new_Elementbtngrp)
    new_Elementcardbody.append(nom_place)
    new_Elementcardbody.append(description_place)
    new_Elementcardbody.append(new_Elementbtngrp)
    new_Elementmb4box.append(img_place)
    new_Elementmb4box.append(new_Elementcardbody)
    new_Elementmd4.append(new_Elementmb4box)
    liste_lieux.append(new_Elementmd4)
    
   /* let place_link =document.createElement("a")
    place_link.setAttribute("href","lieu.html?id="+encodeURI(id))
    place_link.textContent=place.nom_etablissement
    liste_lieux.append(new_Element)
    new_Element.append(place_link)
    
*/
}




