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

document.addEventListener('DOMContentLoaded', function () {
    document.body.addEventListener('click', function (event) {
        // Handle job card link clicks
        if (event.target.matches('.job-card a')) {
            event.preventDefault();
            console.log('Clicked job card link');
            window.open(event.target.href, '_blank'); // Open link in a new tab
        }

        // Handle job card button clicks
        if (event.target.matches('.job-card button')) {
            console.log('Clicked job card button');
            
            // Find the closest job-card and its anchor tag
            let jobCard = event.target.closest('.job-card');
            let link = jobCard ? jobCard.querySelector('a') : null;
            
            if (link) {
                window.open(link.href, '_blank'); // Open the link in a new tab
            } else {
                console.error('No link found inside job-card');
            }
        }
    });
});
