"use strict";

// Ensure the function runs once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    fetch("/assets/header.html")  // Ensure correct path to header.html
    .then(response => response.text())
    .then(data => {
        document.getElementById("header-placeholder").innerHTML = data;
    })
    .catch(error => console.error("Error loading header:", error));
});

// Ensure the function runs once the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    fetch("/assets/footer.html")  // Ensure correct path to header.html
      .then(response => response.text())
      .then(data => {
          document.getElementById("footer-placeholder").innerHTML = data;
      })
      .catch(error => console.error("Error loading footer:", error));
});

document.addEventListener("DOMContentLoaded", function () {
    fetch('/assets/head.html')
    .then(response => response.text())
    .then(data => {
        document.head.innerHTML = data + document.head.innerHTML;
    }).catch(error => console.error("Error loading head:", error));
});


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

document.addEventListener("DOMContentLoaded", function () {
    // Check if user has already made a choice
    if (localStorage.getItem("cookieConsent")) return;

    // Create consent banner container
    const banner = document.createElement("div");
    banner.id = "cookie-consent-banner";

    // Create banner content
    banner.innerHTML = `
        <p>We use cookies to enhance your experience. By continuing, you agree to our <a href="/privacy.html" target="_blank">Privacy Policy</a>.</p>
        <button id="accept-cookies">Accept</button>
        <button id="reject-cookies">Reject</button>
    `;

    // Append banner to body
    document.body.appendChild(banner);

    // Handle button clicks
    document.getElementById("accept-cookies").addEventListener("click", function () {
        localStorage.setItem("cookieConsent", "accepted");
        banner.remove();
    });

    document.getElementById("reject-cookies").addEventListener("click", function () {
        localStorage.setItem("cookieConsent", "rejected");
        banner.remove();
    });
});

document.addEventListener('DOMContentLoaded', () => {
  const jobsContainer = document.querySelector('.job-card-container');

  if (jobsContainer) {
    fetch('jobs.json')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(jobData => {
        jobData.forEach(companyData => {
          const article = document.createElement('article');
          article.classList.add('job-card');

          let companyHTML = `
            <div class="company-name"><strong>${companyData["Company Name"]}</strong></div>
            <div class="job-role-container">
          `;

          for (let i = 1; i <= 4; i += 2) {
            const role1 = companyData[`Role ${i}`];
            const location1 = companyData[`Location ${i}`];
            const link1 = companyData[`Link ${i}`];
            const salary1 = companyData[`Salary ${i}`]; // Get salary for role 1

            const role2 = companyData[`Role ${i + 1}`];
            const location2 = companyData[`Location ${i + 1}`];
            const link2 = companyData[`Link ${i + 1}`];
            const salary2 = companyData[`Salary ${i + 1}`]; // Get salary for role 2

            companyHTML += `
              <div class="job-role-row">
                <div class="job-role">
                  <div class="role-title">${role1}</div>
                  <div class="role-details">
                    <div class="detail"><i class="fas fa-map-marker-alt"></i>&nbsp;<strong>Location:</strong>&nbsp;${location1}</div>
                    <div class="detail"><i class="fas fa-dollar-sign"></i>&nbsp;<strong>Salary:</strong>&nbsp;${salary1} (*Glassdoor)</div>
                  </div>
                  <a href="${link1}" target="_blank" rel="noopener noreferrer" class="apply">Apply</a>
                </div>
                <div class="job-role">
                  <div class="role-title">${role2}</div>
                  <div class="role-details">
                    <div class="detail"><i class="fas fa-map-marker-alt"></i>&nbsp;<strong>Location:</strong>&nbsp;${location2}</div>
                    <div class="detail"><i class="fas fa-dollar-sign"></i>&nbsp;<strong>Salary:</strong>&nbsp;${salary2} (*Glassdoor)</div>
                  </div>
                  <a href="${link2}" target="_blank" rel="noopener noreferrer" class="apply">Apply</a>
                </div>
              </div>
            `;
          }

          companyHTML += `</div>`;
          article.innerHTML = companyHTML;
          jobsContainer.appendChild(article);
          jobsContainer.appendChild(document.createElement('br'));
        });
      })
      .catch(error => {
        console.error('Error fetching or parsing JSON:', error);
        if (jobsContainer) {
          jobsContainer.innerHTML = "<p>Error loading job listings.</p>";
        }
      });
  } else {
    console.log("No .job-card-container found on this page. Skipping job listings.");
  }
});
