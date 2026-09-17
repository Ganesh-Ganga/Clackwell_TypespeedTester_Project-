/* ==========================================================================
   Clackwell typing engine
   One shared core (clock, counters, HUD) with four front-ends:
   time / sentence  -> character stream
   rush             -> single word queue with a combo multiplier
   survival         -> staged stream with three lives
   The browser only counts keystrokes. WPM, accuracy, score and XP are all
   recalculated on the server in utils/scoring.py.
   ========================================================================== */

(function () {
  const S = window.CW_SESSION;
  const el = id => document.getElementById(id);

  const hud = {
    time: el('hudTime'), timeLabel: el('hudTimeLabel'), timeBox: el('hudTimeBox'),
    wpm: el('hudWpm'), acc: el('hudAcc'), words: el('hudWords'),
    wordsLabel: el('hudWordsLabel'), score: el('hudScore')
  };
  const surface = el('surface');
  const veil = el('veil');
  const progressBar = el('progressBar');

  const state = {
    started: false, finished: false, startedAt: 0, elapsed: 0,
    typedKeys: 0, errorKeys: 0,
    correctWords: 0, incorrectWords: 0,
    combo: 0, maxCombo: 0,
    lives: 3, mistakesThisLife: 0,
    stageIndex: 0, stages: [], stageReached: 1,
    text: '', words: [], wordIndex: 0,
    ticker: null
  };

  /* --- boot -------------------------------------------------------------- */

  fetch(S.textUrl)
    .then(r => r.json())
    .then(setup)
    .catch(() => {
      surface.innerHTML = '<p class="muted">The practice text didn\'t load. Refresh the page to try again.</p>';
    });

  function setup(data) {
    if (S.mode === 'rush') {
      state.words = data.words || [];
      setupRush();
    } else if (S.mode === 'survival') {
      state.stages = data.stages || [];
      setupSurvival();
    } else {
      state.text = data.text || '';
      setupStream(state.text);
    }
    buildKeyboard();
    if (S.mode === 'time') { hud.time.textContent = S.duration; }
    else { hud.timeLabel.textContent = 'Time'; hud.time.textContent = '0.0'; }
  }

  /* --- shared clock ------------------------------------------------------ */

  function begin() {
    if (state.started) return;
    state.started = true;
    state.startedAt = performance.now();
    surface.classList.add('live');
    state.ticker = setInterval(tick, 100);
  }

  function tick() {
    state.elapsed = (performance.now() - state.startedAt) / 1000;

    if (S.mode === 'time') {
      const left = Math.max(0, S.duration - state.elapsed);
      hud.time.textContent = left.toFixed(left < 10 ? 1 : 0);
      hud.timeBox.classList.toggle('warn', left <= 10);
      if (left <= 0) return finish();
    } else {
      hud.time.textContent = state.elapsed.toFixed(1);
      if (S.mode === 'rush' && state.elapsed >= 60) return finish();
    }
    refreshHud();
  }

  function metrics() {
    const correctKeys = state.typedKeys - state.errorKeys;
    const minutes = Math.max(state.elapsed, 0.5) / 60;
    return {
      wpm: Math.max(0, Math.round((correctKeys / 5) / minutes)),
      accuracy: state.typedKeys ? Math.round((correctKeys / state.typedKeys) * 100) : 100,
      correctKeys
    };
  }

  function refreshHud() {
    const m = metrics();
    hud.wpm.textContent = m.wpm;
    hud.acc.textContent = m.accuracy + '%';
    hud.words.textContent = S.mode === 'survival' ? state.stageReached : state.correctWords;

    // A live preview only — the server recalculates this on submit.
    const raw = state.correctWords * 10 + m.wpm * 4 +
      Math.max(0, m.accuracy - 70) * 6 + state.maxCombo * 5 - state.incorrectWords * 6;
    const gate = m.accuracy >= 90 ? 1 : Math.max(0.2, (m.accuracy - 50) / 40);
    hud.score.textContent = Math.max(0, Math.round(raw * (S.multiplier || 1) * gate)).toLocaleString();
  }

  /* --- character stream (time, sentence, survival) ----------------------- */

  let stream, inner, capture, spans = [];

  function setupStream(text) {
    stream = el('stream');
    capture = el('capture');
    stream.innerHTML = '';
    inner = document.createElement('div');
    stream.appendChild(inner);

    spans = [...text].map(ch => {
      const s = document.createElement('span');
      s.className = 'pending';
      s.textContent = ch;
      inner.appendChild(s);
      return s;
    });
    if (spans[0]) spans[0].className = 'at';

    capture.value = '';
    lastLength = 0;
    capture.oninput = onStreamInput;   // assignment, not addEventListener: survival
    capture.onclick = null;            // rebuilds this surface once per stage
    surface.onclick = () => capture.focus();
    capture.onpaste = e => e.preventDefault();   // pasting isn't typing
    capture.focus();
    highlightNextKey(text[0]);
  }

  let lastLength = 0;
  function onStreamInput() {
    if (state.finished) return;
    const typed = capture.value;
    const target = state.text;

    if (typed.length > lastLength) {
      begin();
      for (let i = lastLength; i < typed.length; i++) {
        state.typedKeys++;
        if (typed[i] !== target[i]) {
          state.errorKeys++;
          registerMistake();
        }
      }
    }
    lastLength = typed.length;

    for (let i = 0; i < spans.length; i++) {
      const s = spans[i];
      if (i < typed.length) s.className = typed[i] === target[i] ? 'ok' : 'bad';
      else if (i === typed.length) s.className = 'at';
      else s.className = 'pending';
    }

    countWords(typed, target);
    scrollStream(typed.length);
    progressBar.style.width = Math.min(100, (typed.length / target.length) * 100) + '%';
    highlightNextKey(target[typed.length]);
    refreshHud();

    if (typed.length >= target.length) {
      if (S.mode === 'survival') nextStage();
      else finish();
    }
  }

  let cachedLineHeight = 0;
  function scrollStream(index) {
    const cursor = spans[Math.min(index, spans.length - 1)];
    if (!cursor) return;
    // Measured once per run: getComputedStyle on every keystroke is wasteful.
    const lineHeight = cachedLineHeight ||
      (cachedLineHeight = parseFloat(getComputedStyle(stream).lineHeight));
    const line = Math.floor(cursor.offsetTop / lineHeight);
    const shift = Math.max(0, line - 1) * lineHeight;
    inner.style.transform = `translateY(${-shift}px)`;
    inner.style.transition = 'transform .18s ease';
  }

  function countWords(typed, target) {
    const t = typed.split(' ');
    const g = target.split(' ');
    let correct = 0, wrong = 0;
    const complete = typed.endsWith(' ') || typed.length >= target.length ? t.length : t.length - 1;
    for (let i = 0; i < complete; i++) {
      if (!t[i]) continue;
      if (t[i] === g[i]) correct++; else wrong++;
    }
    if (correct > state.correctWords) cheer(correct);
    state.correctWords = correct;
    state.incorrectWords = wrong;
  }

  /* --- survival ---------------------------------------------------------- */

  function setupSurvival() {
    state.stageIndex = 0;
    hud.wordsLabel.textContent = 'Stage';
    state.text = state.stages[0].text;
    renderStageStrip();
    renderLives();
    setupStream(state.text);
  }

  function renderStageStrip() {
    const strip = el('stageStrip');
    if (!strip) return;
    strip.innerHTML = state.stages.map((s, i) => {
      const cls = i < state.stageIndex ? 'cleared' : (i === state.stageIndex ? 'on' : '');
      return `<span class="${cls}">${s.stage}. ${s.label}</span>`;
    }).join('');
  }

  function renderLives() {
    const box = el('lives');
    if (!box) return;
    box.innerHTML = [0, 1, 2].map(i =>
      `<i class="bi bi-heart-fill ${i < state.lives ? '' : 'spent'}"></i>`).join('');
  }

  function registerMistake() {
    if (S.mode !== 'survival') return;
    state.mistakesThisLife++;
    if (state.mistakesThisLife >= 5) {
      state.mistakesThisLife = 0;
      state.lives--;
      renderLives();
      window.CWAnim.toast(state.lives ? `${state.lives} ${state.lives === 1 ? 'life' : 'lives'} left` : 'Out of lives', 'dark');
      if (state.lives <= 0) finish();
    }
  }

  function nextStage() {
    state.stageIndex++;
    state.stageReached = Math.max(state.stageReached, state.stageIndex + 1);
    if (state.stageIndex >= state.stages.length) return finish();

    window.CWAnim.toast(`Stage ${state.stageIndex + 1} — ${state.stages[state.stageIndex].label}`, 'mark');
    state.text = state.stages[state.stageIndex].text;
    renderStageStrip();
    setupStream(state.text);
  }

  /* --- word rush --------------------------------------------------------- */

  let rushInput, rushWord, rushQueue, comboEl;

  function setupRush() {
    rushInput = el('rushInput');
    rushWord = el('rushWord');
    rushQueue = el('rushQueue');
    comboEl = el('combo');
    hud.wordsLabel.textContent = 'Words cleared';

    state.wordIndex = 0;
    drawRush();
    rushInput.onpaste = e => e.preventDefault();
    rushInput.focus();
    surface.onclick = () => rushInput.focus();

    rushInput.addEventListener('input', () => {
      begin();
      const typed = rushInput.value;
      if (typed.endsWith(' ')) return submitWord(typed.trim());
      drawRush(typed);
      rushInput.classList.toggle('wrong', !state.words[state.wordIndex].startsWith(typed));
      highlightNextKey(state.words[state.wordIndex][typed.length]);
    });

    rushInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); submitWord(rushInput.value.trim()); }
    });
  }

  function drawRush(typed = '') {
    const word = state.words[state.wordIndex] || '';
    let html = '';
    for (let i = 0; i < word.length; i++) {
      if (i < typed.length) html += `<span class="${typed[i] === word[i] ? 'ok' : 'bad'}">${escape(word[i])}</span>`;
      else html += `<span class="rest">${escape(word[i])}</span>`;
    }
    rushWord.innerHTML = html;
    rushQueue.innerHTML = state.words.slice(state.wordIndex + 1, state.wordIndex + 5)
      .map(w => `<span>${escape(w)}</span>`).join('');
    progressBar.style.width = (state.wordIndex / state.words.length * 100) + '%';
  }

  function submitWord(typed) {
    if (!typed || state.finished) return;
    const word = state.words[state.wordIndex];

    state.typedKeys += typed.length + 1;
    let matched = 0;
    for (let i = 0; i < typed.length; i++) if (typed[i] === word[i]) matched++;
    state.errorKeys += (typed.length - matched) + (typed === word ? 0 : 1);

    if (typed === word) {
      state.correctWords++;
      state.combo++;
      state.maxCombo = Math.max(state.maxCombo, state.combo);
      cheer(state.correctWords);
    } else {
      state.incorrectWords++;
      state.combo = 0;
      window.CWAnim.toast('Missed — combo reset', 'dark', 800);
    }

    drawCombo();
    rushInput.value = '';
    rushInput.classList.remove('wrong');
    state.wordIndex++;

    if (state.wordIndex >= state.words.length || state.elapsed >= 60) return finish();
    drawRush();
    refreshHud();
  }

  function comboMultiplier() {
    if (state.combo >= 20) return 5;
    if (state.combo >= 10) return 3;
    if (state.combo >= 5) return 2;
    return 1;
  }

  function drawCombo() {
    if (!comboEl) return;
    const x = comboMultiplier();
    comboEl.textContent = `combo ×${x}${state.combo ? ' · ' + state.combo + ' in a row' : ''}`;
    comboEl.classList.toggle('hot', x > 1);
    comboEl.classList.remove('pop');
    void comboEl.offsetWidth;
    comboEl.classList.add('pop');
  }

  /* --- encouragement ----------------------------------------------------- */

  const CHEERS = { 5: 'Nice rhythm', 10: 'Great speed', 25: "You're flying", 50: 'Unstoppable' };
  function cheer(count) {
    if (CHEERS[count]) window.CWAnim.toast(CHEERS[count], 'mark', 900);
  }

  /* --- virtual keyboard --------------------------------------------------- */

  const ROWS = [
    '1234567890'.split(''),
    'qwertyuiop'.split(''),
    'asdfghjkl'.split(''),
    'zxcvbnm,.'.split('')
  ];
  let keyMap = {};

  function buildKeyboard() {
    const host = el('kbd');
    if (!host) return;
    host.innerHTML = '';
    keyMap = {};

    ROWS.forEach(row => {
      const r = document.createElement('div');
      r.className = 'kbd-row';
      row.forEach(k => {
        const key = document.createElement('div');
        key.className = 'kbd-key';
        key.textContent = k;
        r.appendChild(key);
        keyMap[k] = key;
      });
      host.appendChild(r);
    });

    const last = document.createElement('div');
    last.className = 'kbd-row';
    const space = document.createElement('div');
    space.className = 'kbd-key space';
    space.textContent = 'space';
    last.appendChild(space);
    keyMap[' '] = space;
    host.appendChild(last);

    document.addEventListener('keydown', e => flash(e.key, true));
    document.addEventListener('keyup', e => flash(e.key, false));

    el('kbdToggle').addEventListener('click', () => {
      const wrap = el('kbdWrap');
      const hidden = wrap.style.display === 'none';
      wrap.style.display = hidden ? 'grid' : 'none';
      el('kbdToggle').textContent = hidden ? 'Hide keyboard' : 'Show keyboard';
    });
  }

  function flash(key, down) {
    const k = keyMap[String(key).toLowerCase()];
    if (k) k.classList.toggle('down', down);
  }

  let nextKeyEl = null;
  function highlightNextKey(ch) {
    if (nextKeyEl) nextKeyEl.classList.remove('next');
    if (!ch) return;
    nextKeyEl = keyMap[ch.toLowerCase()];
    if (nextKeyEl) nextKeyEl.classList.add('next');
  }

  /* --- finish and save ---------------------------------------------------- */

  function finish() {
    if (state.finished) return;
    state.finished = true;
    clearInterval(state.ticker);
    if (!state.elapsed) state.elapsed = (performance.now() - state.startedAt) / 1000;
    surface.classList.add('done');
    if (capture) capture.blur();
    if (rushInput) rushInput.disabled = true;

    const m = metrics();
    const banner = document.createElement('div');
    banner.className = 'start-veil';
    banner.style.display = 'grid';
    banner.innerHTML = `<strong>${headline()}</strong><span>${m.wpm} wpm · ${m.accuracy}% accuracy — saving your run…</span>`;
    surface.appendChild(banner);

    window.postJSON(S.saveUrl, {
      mode: S.mode,
      level: S.level,
      correct_characters: m.correctKeys,
      incorrect_characters: state.errorKeys,
      correct_words: state.correctWords,
      incorrect_words: state.incorrectWords,
      max_combo: state.maxCombo,
      stage_reached: state.stageReached,
      time_taken: state.elapsed
    })
      .then(data => { window.location.href = data.redirect; })
      .catch(err => {
        banner.innerHTML = `<strong>That run wasn't saved</strong><span>${err.message}</span>`;
      });
  }

  function headline() {
    if (S.mode === 'survival') return state.lives <= 0 ? 'Survival ended' : 'You cleared every stage';
    if (S.mode === 'sentence') return 'Sentence complete';
    if (S.mode === 'rush') return 'Rush over';
    return "Time's up";
  }

  /* --- restart ------------------------------------------------------------ */

  el('restartBtn').addEventListener('click', () => window.location.reload());
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') window.location.reload();
  });

  function escape(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
})();
