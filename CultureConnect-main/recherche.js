// Open the full screen search box
var btn = document.querySelector("input");
function openSearch() {
    document.getElementById("myOverlay").style.display = "block";
    console.log("$btn")
    if (btn.value === "Je suis intéréssé") {
      btn.value = "Je ne suis plus intéressé";
    }
  }
  
  // Close the full screen search box
  function closeSearch() {
    document.getElementById("myOverlay").style.display = "none";
  }

var btn = document.querySelector("input");
var txt = document.querySelector("p");
  
btn.addEventListener("click", updateBtn);
  
function updateBtn() {
  if (btn.value === "Je suis intéréssé") {
      btn.value = "Je ne suis plus intéressé";
  } 
}
  