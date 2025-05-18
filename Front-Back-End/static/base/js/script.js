document.addEventListener("DOMContentLoaded", function () {
  const navbar = document.querySelector(".navbar");

  // Create hamburger
  const hamburger = document.createElement("div");
  hamburger.classList.add("hamburger");

  for (let i = 0; i < 3; i++) {
    const bar = document.createElement("span");
    hamburger.appendChild(bar);
  }

  navbar.insertBefore(hamburger, navbar.firstChild);

  hamburger.addEventListener("click", () => {
    navbar.classList.toggle("active");
  });
});
