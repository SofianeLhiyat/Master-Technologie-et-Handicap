import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.3/firebase-app.js' 
import { getAuth, onAuthStateChanged ,  createUserWithEmailAndPassword } from 'https://www.gstatic.com/firebasejs/9.6.3/firebase-auth.js'
import {getDatabase, ref , get , child, set} from 'https://www.gstatic.com/firebasejs/9.6.3/firebase-database.js'
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
  
const app = initializeApp(firebaseConfig);
var userUID
const auth = getAuth()
onAuthStateChanged(auth, (user) => {
    if (user) {
      // User is signed in, see docs for a list of available properties
      // https://firebase.google.com/docs/reference/js/auth.user
      userUID = user.uid
        alert("hi ") 
        var interesse = document.getElementById("interesse")
        interesse.addEventListener("click", (e)=>{
            e.preventDefault()
            var interesses_ref = ref(database,'sites_culturels/'+id+'/interesses')
            alert("good..."+userUID)
            var userData = {
              [userUID]:true
            }
            set(interesses_ref,userData)
            .then(()=>{
              alert("it works...")
              alert("data saved")
              
          })
          .catch((error)=>{
            alert("error "+error)
          })
        
        
        } )
    } 
  })

  // Initialize Firebase
  
  const params = new URLSearchParams(window.location.search)
  const id = params.get("id")
  var hi_element = document.getElementById("nom_lieu")
  var liste_info_lieu = document.getElementById("liste_info_lieu")
  const database = getDatabase(app)
  var lieuRef = ref(database)
  get(child(lieuRef,'sites_culturels/'+id))
  .then((snapshot)=>{
        let place = snapshot.val()
        console.log(place.nom_etablissement)
        remplir_lieu_informations(place)

  })
  .catch((error)=>{
    alert("error "+error)
  })



function remplir_lieu_informations(place){
    let nom_etablissement=document.getElementById("nom_etablissement")
    console.log(nom_etablissement)
    nom_etablissement.textContent=place.nom_etablissement
    let img_etablissement=document.getElementById("img_lieu")
    img_etablissement.setAttribute("src",place.image)
    img_etablissement.setAttribute("alt",place.description_image)
    let description=document.getElementById("description")
    let description2=document.getElementById("description2")
    let description3=document.getElementById("description3")
    description.textContent=place.description
    description2.textContent=place.description2
    description3.textContent=place.description3
    let adresse=document.getElementById("adresse")
    adresse.textContent=place.adresse
    let code_postal=document.getElementById("code_postal")
    code_postal.textContent=place.code_postal
    let ville=document.getElementById("ville")
    ville.textContent=place.ville
    let site_web=document.getElementById("site_web")
    site_web.textContent=place.site_internet
    let handicap_visuel_element=document.getElementById("handicap_visuel")
    let handicap_visuel_access=place.handicap_visuel
    if(handicap_visuel_access=="Oui"){
        handicap_visuel_element.className="badge badge-success"
        handicap_visuel_element.textContent="Accessible"
    }
    else{
        handicap_visuel_element.className="badge badge-danger"
        handicap_visuel_element.textContent="Non accessible"

    }
    let handicap_moteur_element=document.getElementById("handicap_moteur")
    let handicap_moteur_access=place.handicap_moteur
    if(handicap_moteur_access=="Oui"){
        handicap_moteur_element.className="badge badge-success"
        handicap_moteur_element.textContent="Accessible"

    }
    else{
        handicap_moteur_element.className="badge badge-danger"
        handicap_moteur_element.textContent="Non accessible"

    }
    let handicap_auditif_element=document.getElementById("handicap_auditif")
    let handicap_auditif_access=place.handicap_auditif
    if(handicap_auditif_access=="Oui"){
        handicap_auditif_element.className="badge badge-success"
        handicap_auditif_element.textContent="Accessible"

    }
    else{
        handicap_auditif_element.className="badge badge-danger"
        handicap_auditif_element.textContent="Non accessible"

    }




}

