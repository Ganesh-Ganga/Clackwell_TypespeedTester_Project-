from datetime import datetime, date, timedelta

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Cumulative XP needed to reach each rank. Rank is the "profile progress" track
# and is deliberately separate from level unlocks, which are skill-gated.
RANKS = [
    (0, "Novice"),
    (600, "Apprentice"),
    (1600, "Adept"),
    (3200, "Specialist"),
    (5600, "Virtuoso"),
    (9000, "Legend"),
]


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    avatar = db.Column(db.String(8), default="K")          # single glyph shown in the badge
    tagline = db.Column(db.String(120), default="")
    current_level = db.Column(db.Integer, default=1)       # highest level unlocked
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    last_practice = db.Column(db.Date)

    results = db.relationship(
        "TypingResult", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    badges = db.relationship(
        "UserBadge", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    # ---- progress helpers -------------------------------------------------

    @property
    def rank(self):
        label = RANKS[0][1]
        for threshold, name in RANKS:
            if self.xp >= threshold:
                label = name
        return label

    @property
    def rank_progress(self):
        """Returns (xp_into_rank, xp_needed_for_next, percent)."""
        floor_xp, ceil_xp = RANKS[0][0], None
        for threshold, _ in RANKS:
            if self.xp >= threshold:
                floor_xp = threshold
            elif ceil_xp is None:
                ceil_xp = threshold
        if ceil_xp is None:  # maxed out
            return (self.xp - floor_xp, self.xp - floor_xp, 100)
        span = ceil_xp - floor_xp
        into = self.xp - floor_xp
        return (into, span, round(into / span * 100))

    def touch_streak(self, today=None):
        """Called once per saved result. Returns True if the streak grew today."""
        today = today or date.today()
        if self.last_practice == today:
            return False
        if self.last_practice == today - timedelta(days=1):
            self.streak += 1
        else:
            self.streak = 1
        self.last_practice = today
        self.best_streak = max(self.best_streak or 0, self.streak)
        return True

    def stats(self):
        rows = self.results.all()
        if not rows:
            return {
                "tests": 0, "best_wpm": 0, "avg_wpm": 0, "best_accuracy": 0,
                "avg_accuracy": 0, "best_score": 0, "total_seconds": 0,
            }
        return {
            "tests": len(rows),
            "best_wpm": max(r.wpm for r in rows),
            "avg_wpm": round(sum(r.wpm for r in rows) / len(rows), 1),
            "best_accuracy": round(max(r.accuracy for r in rows), 1),
            "avg_accuracy": round(sum(r.accuracy for r in rows) / len(rows), 1),
            "best_score": max(r.score for r in rows),
            "total_seconds": int(sum(r.time_taken for r in rows)),
        }


class TypingResult(db.Model):
    __tablename__ = "typing_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    level = db.Column(db.Integer, default=1)
    mode = db.Column(db.String(20), default="time")
    wpm = db.Column(db.Float, default=0)
    cpm = db.Column(db.Float, default=0)
    accuracy = db.Column(db.Float, default=0)
    correct_words = db.Column(db.Integer, default=0)
    incorrect_words = db.Column(db.Integer, default=0)
    correct_characters = db.Column(db.Integer, default=0)
    incorrect_characters = db.Column(db.Integer, default=0)
    max_combo = db.Column(db.Integer, default=0)
    stage_reached = db.Column(db.Integer, default=0)   # survival mode only
    score = db.Column(db.Integer, default=0)
    xp_earned = db.Column(db.Integer, default=0)
    time_taken = db.Column(db.Float, default=0)
    passed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def total_characters(self):
        return self.correct_characters + self.incorrect_characters


class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(160), nullable=False)
    icon = db.Column(db.String(40), nullable=False)      # bootstrap icon name
    requirement = db.Column(db.String(120), nullable=False)
    sort_order = db.Column(db.Integer, default=0)


class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    badge = db.relationship("Badge")

    __table_args__ = (db.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)
