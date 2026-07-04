function searchFood(){

let input=document.getElementById("searchFood");

let filter=input.value.toUpperCase();

let cards=document.getElementsByClassName("food-card");

for(let i=0;i<cards.length;i++){

let title=cards[i].getElementsByTagName("h2")[0];

if(title.innerHTML.toUpperCase().indexOf(filter)>-1){

cards[i].style.display="";

}

else{

cards[i].style.display="none";

}

}

}