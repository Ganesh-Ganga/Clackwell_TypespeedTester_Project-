from flask import Blueprint, jsonify, request, url_for, session

from models import db, TypingResult
from utils.security import login_required, current_user
from utils import text_engine, scoring, analytics
from utils.badges import check_badges
from utils.levels import MAX_LEVEL, get_level

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/text")
@login_required
def text():
    mode = request.args.get("mode", "time")
    level = request.args.get("level", type=int) or current_user().current_level
    level = min(level, current_user().current_level)
    return jsonify(text_engine.build(mode, level))


@api_bp.post("/result")
@login_required
def save_result():
    """Receives raw counts from the browser and derives everything else."""
    user = current_user()
    payload = request.get_json(silent=True) or {}

    mode = payload.get("mode", "time")
    if mode not in ("time", "sentence", "rush", "survival"):
        return jsonify({"error": "Unknown mode."}), 400

    level = int(payload.get("level") or 1)
    if level < 1 or level > user.current_level:
        return jsonify({"error": "That level isn't unlocked."}), 403

    correct_chars = int(payload.get("correct_characters") or 0)
    incorrect_chars = int(payload.get("incorrect_characters") or 0)
    seconds = float(payload.get("time_taken") or 0)

    if seconds < 1 or (correct_chars + incorrect_chars) == 0:
        return jsonify({"error": "That run was too short to score."}), 400

    metrics = scoring.compute_metrics(correct_chars, incorrect_chars, seconds)
    correct_words = max(0, int(payload.get("correct_words") or 0))
    incorrect_words = max(0, int(payload.get("incorrect_words") or 0))
    max_combo = max(0, int(payload.get("max_combo") or 0))

    score = scoring.compute_score(metrics, level, correct_words, incorrect_words, max_combo, mode)
    passed = scoring.level_passed(metrics, level, score)

    previous_best = max([r.wpm for r in user.results.all()] or [0])
    is_personal_best = metrics["wpm"] > previous_best

    streak_extended = user.touch_streak()
    xp, xp_lines = scoring.compute_xp(metrics, level, passed, is_personal_best, streak_extended)

    row = TypingResult(
        user_id=user.id, level=level, mode=mode,
        wpm=metrics["wpm"], cpm=metrics["cpm"], accuracy=metrics["accuracy"],
        correct_words=correct_words, incorrect_words=incorrect_words,
        correct_characters=correct_chars, incorrect_characters=incorrect_chars,
        max_combo=max_combo, stage_reached=int(payload.get('stage_reached') or 0),
        score=score, xp_earned=xp,
        time_taken=round(seconds, 1), passed=passed,
    )
    db.session.add(row)

    user.xp = (user.xp or 0) + xp
    unlocked_level = None
    if passed and level == user.current_level and level < MAX_LEVEL:
        user.current_level = level + 1
        unlocked_level = get_level(user.current_level)

    db.session.commit()

    new_badges = check_badges(user, row)

    cleared = {r.level for r in user.results.filter_by(passed=True).all()}
    finished_everything = all(n in cleared for n in range(1, MAX_LEVEL + 1))

    # Stashed for the result page so it can play the right animations once.
    session["xp_lines"] = xp_lines
    session["new_badges"] = new_badges
    session["unlocked_level"] = (
        {"number": unlocked_level["number"], "title": unlocked_level["title"]}
        if unlocked_level else None
    )
    session["finished_everything"] = finished_everything

    return jsonify({
        "ok": True,
        "redirect": url_for("main.result", result_id=row.id),
        "wpm": metrics["wpm"], "accuracy": metrics["accuracy"], "score": score,
        "xp": xp, "passed": passed, "personal_best": is_personal_best,
    })


@api_bp.get("/analytics")
@login_required
def analytics_data():
    user = current_user()
    return jsonify({
        "progress": analytics.progress_series(user),
        "weekday": analytics.weekday_series(user),
        "levels": analytics.level_series(user),
        "modes": analytics.mode_distribution(user),
        "stats": user.stats(),
    })
