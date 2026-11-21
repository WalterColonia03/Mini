// Keep the entire focused link, including its focus ring, in the mobile menu.
document.addEventListener("focusin", (event) => {
  if (event.target instanceof Element &&
      event.target.matches(".sidebar-nav .nav-item") &&
      window.matchMedia("(max-width: 680px)").matches) {
    event.target.scrollIntoView({block: "nearest", inline: "nearest", behavior: "instant"});
  }
});
