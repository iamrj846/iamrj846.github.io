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
  fetch("/assets/head.html")
      .then(response => response.text())
      .then(data => {
          document.getElementById("head-placeholder").innerHTML = data;
      })
      .catch(error => console.error("Error loading head:", error));
}

document.addEventListener("DOMContentLoaded", loadHead);

function loadBlogList() {
  fetch("/docker-blog-list.html")  // Make sure the path is correct
      .then(response => response.text())
      .then(data => {
          document.getElementById("docker-blog-list-placeholder").innerHTML = data;
      })
      .catch(error => console.error("Error loading blog list:", error));
}

// Run the function once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", loadBlogList);