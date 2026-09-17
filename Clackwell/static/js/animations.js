/* Small, dependency-free motion helpers shared across pages.
   Everything here checks prefers-reduced-motion before doing anything showy. */

(function () {
  const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- one-time entrance reveal ----------------------------------------- */

  function initReveal() {
    const items = document.querySelectorAll('[data-reveal]');
    if (!items.length) return;
    if (calm) { items.forEach(el => el.style.opacity = 1); return; }

    items.forEach((el, i) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(12px)';
      el.style.transition = `opacity .5s ease ${i * 70}ms, transform .5s cubic-bezier(.2,.8,.2,1) ${i * 70}ms`;
    });
    requestAnimationFrame(() => items.forEach(el => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    }));
  }

  /* --- number that counts up -------------------------------------------- */

  function countTo(el, target, decimals = 0, ms = 900) {
    const end = Number(target) || 0;
    if (calm) { el.textContent = end.toFixed(decimals); return; }
    const start = performance.now();
    function frame(now) {
      const t = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = (end * eased).toFixed(decimals);
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  function initCounters(root = document) {
    root.querySelectorAll('[data-count]').forEach(el => {
      countTo(el, el.dataset.count, Number(el.dataset.decimals || 0));
    });
  }

  /* --- transient toast --------------------------------------------------- */

  let toastEl, toastTimer;
  function toast(message, variant = 'dark', ms = 1200) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'game-toast';
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = message;
    toastEl.className = 'game-toast show' + (variant === 'mark' ? ' mark' : '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), ms);
  }

  /* --- confetti (canvas, ~60 pieces, stops itself) ----------------------- */

  function confetti(duration = 2200) {
    if (calm) return;
    const layer = document.getElementById('confetti-layer');
    if (!layer) return;

    const canvas = document.createElement('canvas');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    canvas.style.cssText = 'position:absolute;inset:0;';
    layer.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    const colours = ['#ffd23f', '#14161a', '#11805b', '#cf2f45', '#2331a8'];
    const pieces = Array.from({ length: 70 }, () => ({
      x: Math.random() * canvas.width,
      y: -20 - Math.random() * canvas.height * 0.4,
      w: 6 + Math.random() * 6,
      h: 9 + Math.random() * 8,
      vy: 2 + Math.random() * 3,
      vx: -1.2 + Math.random() * 2.4,
      rot: Math.random() * Math.PI,
      vr: -0.1 + Math.random() * 0.2,
      colour: colours[Math.floor(Math.random() * colours.length)]
    }));

    const started = performance.now();
    function frame(now) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pieces.forEach(p => {
        p.x += p.vx; p.y += p.vy; p.rot += p.vr;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.colour;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      });
      if (now - started < duration) requestAnimationFrame(frame);
      else canvas.remove();
    }
    requestAnimationFrame(frame);
  }

  /* --- progress bar fill -------------------------------------------------- */

  function fillBars(root = document) {
    root.querySelectorAll('[data-fill]').forEach(el => {
      const pct = Math.max(0, Math.min(100, Number(el.dataset.fill) || 0));
      requestAnimationFrame(() => { el.style.width = pct + '%'; });
    });
  }

  window.CWAnim = { initReveal, initCounters, countTo, toast, confetti, fillBars, calm };

  document.addEventListener('DOMContentLoaded', () => {
    initReveal();
    initCounters();
    fillBars();
  });
})();
