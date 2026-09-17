from datetime import date

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort, session,
)

from models import db, TypingResult, Badge, UserBadge
from utils.security import login_required, current_user
from utils.levels import LEVELS, MAX_LEVEL, get_level
from utils import analytics

main_bp = Blueprint("main", __name__)

MODES = [
    {"key": "time", "name": "Time Attack", "icon": "stopwatch",
     "blurb": "Type as much as you can before the clock runs out."},
    {"key": "sentence", "name": "Sentence Challenge", "icon": "quote",
     "blurb": "One sentence, typed exactly. No timer pressure."},
    {"key": "rush", "name": "Word Rush", "icon": "lightning",
     "blurb": "One word at a time. Chain them for a combo multiplier."},
    {"key": "survival", "name": "Survival", "icon": "shield-exclamation",
     "blurb": "Five stages, harder each time. Three mistakes and you're out."},
]


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/levels")
@login_required
def levels():
    user = current_user()
    cleared = {r.level for r in user.results.filter_by(passed=True).all()}
    best_by_level = {}
    for r in user.results.all():
        prev = best_by_level.get(r.level)
        if not prev or r.score > prev["score"]:
            best_by_level[r.level] = {"score": r.score, "wpm": r.wpm, "accuracy": r.accuracy}

    cards = []
    for lvl in LEVELS:
        cards.append({
            **lvl,
            "unlocked": lvl["number"] <= user.current_level,
            "cleared": lvl["number"] in cleared,
            "best": best_by_level.get(lvl["number"]),
        })
    return render_template("levels.html", cards=cards, modes=MODES)


@main_bp.route("/test")
@login_required
def test():
    user = current_user()
    level_number = request.args.get("level", type=int) or user.current_level
    if level_number > user.current_level:
        flash(f"Level {level_number} is still locked. Clear Level {user.current_level} first.",
              "warning")
        return redirect(url_for("main.levels"))

    mode = request.args.get("mode", "time")
    if mode not in {m["key"] for m in MODES}:
        mode = "time"
    duration = request.args.get("duration", type=int) or 60
    if duration not in (15, 30, 60, 120):
        duration = 60

    return render_template(
        "test.html",
        level=get_level(level_number),
        mode=mode,
        modes=MODES,
        duration=duration,
    )


@main_bp.route("/result/<int:result_id>")
@login_required
def result(result_id):
    user = current_user()
    row = TypingResult.query.get_or_404(result_id)
    if row.user_id != user.id:
        abort(403)

    previous = (
        user.results
        .filter(TypingResult.id != row.id, TypingResult.mode == row.mode)
        .order_by(TypingResult.wpm.desc())
        .first()
    )
    level = get_level(row.level)
    next_level = get_level(row.level + 1) if row.level < MAX_LEVEL else None

    unlocked = session.pop("unlocked_level", None)
    new_badges = session.pop("new_badges", [])
    xp_lines = session.pop("xp_lines", [])
    all_done = session.pop("finished_everything", False)

    return render_template(
        "result.html",
        r=row, level=level, next_level=next_level,
        previous_best=previous.wpm if previous else 0,
        unlocked=unlocked, new_badges=new_badges, xp_lines=xp_lines,
        all_done=all_done,
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    stats = user.stats()
    recent = user.results.order_by(TypingResult.created_at.desc()).limit(6).all()

    earned = {ub.badge_id: ub for ub in user.badges.all()}
    badges = []
    for badge in Badge.query.order_by(Badge.sort_order).all():
        badges.append({
            "badge": badge,
            "earned": badge.id in earned,
            "earned_at": earned[badge.id].earned_at if badge.id in earned else None,
        })

    welcome = session.pop("just_registered", False)
    into, span, percent = user.rank_progress
    cleared = {r.level for r in user.results.filter_by(passed=True).all()}

    return render_template(
        "dashboard.html",
        stats=stats, recent=recent, badges=badges,
        insights=analytics.build_insights(user),
        activity=analytics.activity_grid(user),
        xp_into=into, xp_span=span, xp_percent=percent,
        level=get_level(user.current_level),
        first_visit=welcome,
        cleared_all=all(n in cleared for n in range(1, MAX_LEVEL + 1)),
    )


@main_bp.route("/leaderboard")
def leaderboard():
    scope = request.args.get("scope", "all")
    rows = _leaderboard_rows(scope)
    return render_template("leaderboard.html", rows=rows, scope=scope)


def _leaderboard_rows(scope):
    """Best run per user inside the window. Emails are never selected."""
    from datetime import datetime, timedelta
    from models import User

    q = db.session.query(TypingResult, User).join(User, User.id == TypingResult.user_id)
    windows = {"daily": 1, "weekly": 7, "monthly": 30}
    if scope in windows:
        cutoff = datetime.utcnow() - timedelta(days=windows[scope])
        q = q.filter(TypingResult.created_at >= cutoff)

    best = {}
    for result, user in q.all():
        held = best.get(user.id)
        if not held or result.wpm > held["wpm"]:
            best[user.id] = {
                "username": user.username,
                "avatar": user.avatar or user.username[0].upper(),
                "wpm": result.wpm,
                "accuracy": result.accuracy,
                "level": user.current_level,
                "rank_name": user.rank,
            }
    ordered = sorted(best.values(), key=lambda x: (-x["wpm"], -x["accuracy"]))
    for i, row in enumerate(ordered, start=1):
        row["rank"] = i
    return ordered[:50]


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        tagline = (request.form.get("tagline") or "").strip()[:120]
        avatar = (request.form.get("avatar") or "").strip()[:2]

        if not name:
            flash("Your name can't be empty.", "danger")
        else:
            user.name = name
            user.tagline = tagline
            user.avatar = avatar or name[0].upper()
            db.session.commit()
            flash("Profile updated.", "success")
        return redirect(url_for("main.profile"))

    stats = user.stats()
    earned = user.badges.order_by(UserBadge.earned_at.desc()).all()
    into, span, percent = user.rank_progress
    return render_template(
        "profile.html", stats=stats, earned=earned,
        total_badges=Badge.query.count(),
        xp_into=into, xp_span=span, xp_percent=percent,
        level=get_level(user.current_level),
        member_since=user.created_at.strftime("%d %B %Y") if user.created_at else "",
    )


@main_bp.route("/analytics")
@login_required
def analytics_page():
    user = current_user()
    return render_template(
        "analytics.html",
        stats=user.stats(),
        insights=analytics.build_insights(user),
        activity=analytics.activity_grid(user),
        has_data=user.results.count() > 0,
    )
