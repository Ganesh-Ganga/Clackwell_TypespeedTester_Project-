# Clackwell

A typing range built with Flask. Seven levels, four game modes, XP and badges, and an
analytics page that reads every run you've made.

---

## Run it

Open the folder in VS Code, then in the terminal:

**Windows**

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>.

The SQLite database and the badge table are created automatically on first run —
there is no migration step.

### Optional: demo data

Charts look empty on a brand new account. To fill one account with eight weeks of
realistic runs for a presentation:

```bash
python seed_demo.py
```

Sign in as **demo / demo1234**. It only ever touches that one account.

---

## Project layout

```
Clackwell/
├── app.py                 application factory, error handlers, entry point
├── config.py              settings (swap one line for MySQL/Postgres)
├── models.py              User, TypingResult, Badge, UserBadge
├── requirements.txt
├── seed_demo.py           optional demo data
│
├── routes/
│   ├── auth.py            register, login, logout, password reset
│   ├── main.py            pages: landing, levels, test, result, dashboard…
│   └── api.py             JSON: practice text, result submission, chart data
│
├── utils/
│   ├── levels.py          level definitions + the text corpus
│   ├── text_engine.py     builds the material for each mode
│   ├── scoring.py         WPM, accuracy, score, XP  (server-side only)
│   ├── badges.py          badge catalogue and award conditions
│   ├── analytics.py       chart series, activity grid, written insights
│   └── security.py        session auth, CSRF, validation
│
├── templates/             base + 12 pages
├── static/css/            style, home, auth, typing, dashboard
├── static/js/             main, typing, dashboard, animations, auth
└── database/database.db   created on first run
```

---

## How the pieces fit

**Scoring is server-side.** The browser counts keystrokes and seconds, nothing else.
`routes/api.py` recomputes WPM, accuracy, score and XP through `utils/scoring.py`, so a
tampered page can't put a fake number on the leaderboard.

- `WPM = (correct characters ÷ 5) ÷ minutes`
- `Accuracy = correct keystrokes ÷ total keystrokes × 100`
- Score = base + speed + accuracy + combo bonuses, multiplied by the level's difficulty,
  then scaled down by an accuracy gate below 90% so speed alone never wins.

**Levels unlock on skill.** A level opens when one run clears its WPM target, its accuracy
target and its score threshold together. Difficulty comes from the material — word length,
punctuation, digits, casing, then raw source code — never from a shorter clock.

**XP feeds a separate rank track** (Novice → Legend), so the two progressions don't fight
each other.

**Every badge has a real condition**, checked against stored rows in `utils/badges.py`
the moment a run is saved.

**Insights are derived, not canned.** `utils/analytics.py` compares this week to last,
finds your strongest mode, spots endurance gaps and your fastest hour of the day.

---

## Security notes

- Passwords hashed with Werkzeug (`generate_password_hash`) — never stored as text.
- Session-based auth with a `@login_required` decorator.
- CSRF token minted per session, injected into every form and every `fetch` header, and
  verified on every unsafe request in `app.before_request`.
- Server-side validation on registration, login, profile edits and result submission.
- `HttpOnly` and `SameSite=Lax` cookies; set `SECRET_KEY` in the environment for deployment.
- Results are ORM-parameterised — no string-built SQL anywhere.
- A user can only read their own results; the result page returns 403 for anyone else's.
- The leaderboard selects username, speed, accuracy and level. Email is never queried.

## Moving off SQLite

Change `SQLALCHEMY_DATABASE_URI` in `config.py` (or set `DATABASE_URL`) and install the
matching driver. No model or query changes are needed.
