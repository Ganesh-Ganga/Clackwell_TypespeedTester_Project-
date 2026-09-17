/* Site-wide behaviour: menu, flash dismissal, activity tooltips, and the
   working typing demo that sits in the landing hero. */

(function () {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';

  window.postJSON = function (url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify(body)
    }).then(async res => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || 'Something went wrong saving that run.');
      return data;
    });
  };

  /* --- mobile nav --------------------------------------------------------- */

  const toggle = document.getElementById('navToggle');
  const wrap = document.getElementById('navWrap');
  if (toggle && wrap) {
    toggle.addEventListener('click', () => {
      const open = wrap.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.innerHTML = open ? '<i class="bi bi-x-lg"></i>' : '<i class="bi bi-list"></i>';
    });
  }

  /* --- flash messages fade after a few seconds ---------------------------- */

  const stack = document.getElementById('flashStack');
  if (stack) {
    setTimeout(() => {
      stack.style.transition = 'opacity .4s ease';
      stack.style.opacity = '0';
      setTimeout(() => stack.remove(), 450);
    }, 4200);
    stack.addEventListener('click', e => e.target.closest('.flash')?.remove());
  }

  /* --- tooltips for the activity grid and anything with data-tip ---------- */

  const tip = document.getElementById('tooltip');
  if (tip) {
    document.addEventListener('mouseover', e => {
      const host = e.target.closest('[data-tip]');
      if (!host) return;
      tip.innerHTML = host.dataset.tip;
      tip.classList.add('show');
      const r = host.getBoundingClientRect();
      tip.style.left = Math.min(window.innerWidth - 220, Math.max(8, r.left - 20)) + 'px';
      tip.style.top = (r.top - tip.offsetHeight - 10) + 'px';
    });
    document.addEventListener('mouseout', e => {
      if (e.target.closest('[data-tip]')) tip.classList.remove('show');
    });
  }

  /* --- hero demo ---------------------------------------------------------- */

  const DEMO_LINE = 'the keyboard is a tool you already own so you may as well be good at it';

  window.initHeroDemo = function () {
    const host = document.getElementById('demo');
    if (!host) return;

    const textEl = document.getElementById('demoText');
    const input = document.getElementById('demoInput');
    const wpmEl = document.getElementById('demoWpm');
    const accEl = document.getElementById('demoAcc');
    const timeEl = document.getElementById('demoTime');
    const statusEl = document.getElementById('demoStatus');

    let startedAt = null, ticker = null;

    const spans = [...DEMO_LINE].map(ch => {
      const s = document.createElement('span');
      s.textContent = ch;
      textEl.appendChild(s);
      return s;
    });
    spans[0].classList.add('at');

    host.addEventListener('click', () => input.focus());
    host.addEventListener('focus', () => input.focus());

    input.addEventListener('input', () => {
      const typed = input.value;

      if (!startedAt && typed.length) {
        startedAt = performance.now();
        host.classList.add('live');
        statusEl.textContent = 'typing';
        ticker = setInterval(update, 100);
      }

      let correct = 0;
      spans.forEach((s, i) => {
        s.className = '';
        if (i < typed.length) {
          const ok = typed[i] === DEMO_LINE[i];
          s.className = ok ? 'ok' : 'bad';
          if (ok) correct++;
        } else if (i === typed.length) {
          s.className = 'at';
        }
      });

      const acc = typed.length ? Math.round((correct / typed.length) * 100) : 100;
      accEl.textContent = acc + '%';

      if (typed.length >= DEMO_LINE.length) {
        clearInterval(ticker);
        statusEl.textContent = 'done';
        update();
        window.CWAnim.toast('Nice line. Make an account to keep the score.', 'mark', 2600);
      }
    });

    function update() {
      if (!startedAt) return;
      const seconds = (performance.now() - startedAt) / 1000;
      const correct = textEl.querySelectorAll('.ok').length;
      timeEl.textContent = seconds.toFixed(1) + 's';
      wpmEl.textContent = Math.round((correct / 5) / (seconds / 60)) || 0;
    }
  };
})();
