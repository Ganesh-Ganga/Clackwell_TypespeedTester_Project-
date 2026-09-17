/* Client-side helpers for the auth forms. These are conveniences only —
   every rule here is enforced again in utils/security.py before anything
   touches the database. */

(function () {
  document.querySelectorAll('.pw-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.toggle);
      if (!input) return;
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      btn.innerHTML = showing ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
      btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
    });
  });

  const pw = document.getElementById('password');
  const fill = document.getElementById('strengthFill');
  const label = document.getElementById('strengthLabel');

  const LEVELS = [
    { at: 0, text: 'At least 8 characters, with a letter and a number.', colour: '#e2e2dc', width: 0 },
    { at: 1, text: 'Weak — add length and a number.', colour: '#cf2f45', width: 25 },
    { at: 2, text: 'Fair — one more character type would help.', colour: '#f0a500', width: 50 },
    { at: 3, text: 'Good — this will hold up.', colour: '#11805b', width: 75 },
    { at: 4, text: 'Strong.', colour: '#11805b', width: 100 }
  ];

  function score(value) {
    if (!value) return 0;
    let s = 0;
    if (value.length >= 8) s++;
    if (value.length >= 12) s++;
    if (/[A-Z]/.test(value) && /[a-z]/.test(value)) s++;
    if (/\d/.test(value)) s++;
    if (/[^A-Za-z0-9]/.test(value)) s++;
    return Math.min(4, s);
  }

  if (pw && fill && label) {
    pw.addEventListener('input', () => {
      const state = LEVELS[score(pw.value)];
      fill.style.width = state.width + '%';
      fill.style.background = state.colour;
      label.textContent = state.text;
    });
  }

  const confirm = document.getElementById('confirm_password');
  const matchErr = document.getElementById('matchErr');
  if (pw && confirm && matchErr) {
    const check = () => {
      const mismatch = confirm.value.length > 0 && confirm.value !== pw.value;
      matchErr.style.display = mismatch ? 'block' : 'none';
      confirm.closest('.field').classList.toggle('invalid', mismatch);
    };
    confirm.addEventListener('input', check);
    pw.addEventListener('input', check);
  }
})();
