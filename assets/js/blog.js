"use strict";

function loadHeader() {
  fetch("/assets/header.html")  // Ensure correct path to header.html
      .then(response => response.text())
      .then(data => {
          document.getElementById("header-placeholder").innerHTML = data;
      })
      .catch(error => console.error("Error loading header:", error));
}

// Ensure the function runs once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", loadHeader);

function loadFooter() {
  fetch("/assets/footer.html")  // Ensure correct path to header.html
      .then(response => response.text())
      .then(data => {
          document.getElementById("footer-placeholder").innerHTML = data;
      })
      .catch(error => console.error("Error loading footer:", error));
}

// Ensure the function runs once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", loadFooter);

function loadHead() {
    fetch('/assets/head.html')
    .then(response => response.text())
    .then(data => {
        document.head.innerHTML += data; // Ensure it goes inside <head>
    }).catch(error => console.error("Error loading head:", error));
}

document.addEventListener("DOMContentLoaded", loadHead);

$(document).ready(function() {
    $('.job-card a').click(function (event) {
        event.preventDefault();
        console.log('Clicked job card link');
        // Example: window.open($(this).attr('href'), '_blank'); 
    });

    $('.job-card button').click(function () {
        console.log('Clicked job card button');
    });
});