
function navbar() {
  // Obtient l'élément avec l'identifiant "myTopnav" et le stocke dans la variable x
  
  var x=document.getElementById("myTopnav");
  console.log(x);
  // Vérifie si le nom de classe de l'élément est "topnav"
  if (x.className === "topnav") {
    // Si c'est le cas, ajoute la classe "responsive" à la liste des classes de l'élément
    x.className += "responsive";
  } else {
    // Si le nom de classe n'est pas "topnav", remplace le nom de classe par "topnav"
    x.className = "topnav";
  }
}



