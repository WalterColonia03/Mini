// Focus only after the server returns validation errors, never on field blur.
(() => {
  const summary = document.getElementById('initial-load-errors');
  if (!summary) return;
  summary.focus();
  summary.addEventListener('click', (event) => {
    const link = event.target.closest('a[href^="#"]');
    if (!link) return;
    const field = document.getElementById(link.getAttribute('href').slice(1));
    if (!field) return;
    event.preventDefault();
    field.focus();
  });
})();
