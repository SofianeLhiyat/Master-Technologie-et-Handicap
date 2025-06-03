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
  var type=""
  var est_musee=false
  var museecheckbox=document.getElementById("musee")
  var handicap=""
  museecheckbox.addEventListener('change',function(){
    est_musee=this.checked;
    if(est_musee){
        type="musée"

    }
  })
  var est_exposition=false
  var expositioncheckbox=document.getElementById("exposition")

  expositioncheckbox.addEventListener('change',function(){
    est_exposition=this.checked;
    if(est_exposition){
        type="exposition"

    }
  })
  var est_monument=false
  var monumentcheckbox=document.getElementById("monument")

  monumentcheckbox.addEventListener('change',function(){
    est_monument=this.checked;
    if(est_monument){
        type="monument"

    }
  })
  var est_chateau=false
  var chateaucheckbox=document.getElementById("chateaux")

  chateaucheckbox.addEventListener('change',function(){
    est_chateau=this.checked;
    if(est_chateau){
        type="chateau"

    }
  })
  var handicap_auditif=false
  var handicap_auditifcheckbox=document.getElementById("handicap_auditif")

  handicap_auditifcheckbox.addEventListener('change',function(){
    handicap_auditif=this.checked;
    if(handicap_auditif){
        handicap="handicap_auditif"

    }
    else{
        if(handicap=="handicap_auditif"){
            handicap=""
        }
    }
  })

  var handicap_visuel=false
  var handicap_visuelcheckbox=document.getElementById("handicap_visuel")

  handicap_visuelcheckbox.addEventListener('change',function(){
    handicap_visuel=this.checked;
    if(handicap_visuel){
        handicap="handicap_visuel"

    }
    else{
        if(handicap=="handicap_visuel"){
            handicap=""
        }
    }

  })

  var handicap_moteur=false
  var handicap_moteurcheckbox=document.getElementById("handicap_moteur")

  handicap_moteurcheckbox.addEventListener('change',function(){
    handicap_moteur=this.checked;
    if(handicap_moteur){
        handicap="handicap_moteur"

    }
    else{
        if(handicap=="handicap_moteur"){
            handicap=""
        }
    }

  })


  var search = document.getElementById("search")
  search.addEventListener("click",(e)=>{
    e.preventDefault()
    liste_lieux.innerHTML=""
    var code_postal = document.getElementById("code_postal").value
    var lieuxRef = ref(database,"sites_culturels")
    get((lieuxRef))
    .then( (snapshot)=>{
            snapshot.forEach(childSnapshot => {
            var place = childSnapshot.val()
            var id = childSnapshot.key
            if(code_postal!="" && type!=""){
                switch(handicap){
                    case 'handicap_auditif':
                        if(place.code_postal==code_postal && place.type==type && place.handicap_auditif=="Oui"){
                            var placeName = place.nom_etablissement
                            console.log(placeName)
                            console.log(est_musee)
                            console.log(id)
                            ajouter_element_liste(place,id)
            
                        }
                        break
                        case 'handicap_visuel':
                            if(place.code_postal==code_postal && place.type==type && place.handicap_visuel=="Oui"){
                                var placeName = place.nom_etablissement
                                console.log(placeName)
                                console.log(est_musee)
                                console.log(id)
                                ajouter_element_liste(place,id)
                
                            }
                        break
                        case 'handicap_moteur':
                            if(place.code_postal==code_postal && place.type==type && place.handicap_moteur=="Oui"){
                                var placeName = place.nom_etablissement
                                console.log(placeName)
                                console.log(est_musee)
                                console.log(id)
                                ajouter_element_liste(place,id)
                    
                                }
                        break
                        default:
                            if(place.code_postal==code_postal && place.type==type){
                                var placeName = place.nom_etablissement
                                console.log(placeName)
                                console.log(est_musee)
                                console.log(id)
                                ajouter_element_liste(place,id)
                
                            }
                }
                
            }
            else if(code_postal!=""){
                switch(handicap){
                    case 'handicap_auditif':
                        if(place.code_postal==code_postal && place.handicap_auditif=="Oui"){
                            var placeName = place.nom_etablissement
                            console.log(placeName)
                            console.log(est_musee)
                            console.log(id)
                            ajouter_element_liste(place,id)
                        }
                        break
                        case 'handicap_moteur':
                            if(place.code_postal==code_postal && place.handicap_moteur=="Oui"){
                                var placeName = place.nom_etablissement
                                console.log(placeName)
                                console.log(est_musee)
                                console.log(id)
                                ajouter_element_liste(place,id)
                        }
                        break
                        case 'handicap_visuel':
                        if(place.code_postal==code_postal && place.handicap_visuel=="Oui"){
                            var placeName = place.nom_etablissement
                            console.log(placeName)
                            console.log(est_musee)
                            console.log(id)
                            ajouter_element_liste(place,id)
                        }
                        default:
                            if(place.code_postal==code_postal){
                                var placeName = place.nom_etablissement
                                console.log(placeName)
                                console.log(est_musee)
                                console.log(id)
                                ajouter_element_liste(place,id)
                            }
                }
                
                
            }
            
        });

    })
     

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
    btn_interesse.className="btn btn-sm btn-outline-secondary"
    let place_link =document.createElement("a")
    place_link.setAttribute("href","lieubis2.html?id="+encodeURI(id))
    place_link.textContent="Voir plus"
    btn_interesse.textContent="Je suis intéressé"
    img_place.setAttribute("src",place.image)
    img_place.setAttribute("alt",place.description_image)
    btn_voirplus.append(place_link)
    new_Elementbtngrp.append(btn_voirplus)
    new_Elementbtngrp.append(btn_interesse)
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




