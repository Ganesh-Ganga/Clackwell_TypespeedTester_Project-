"""Badge definitions and the checks that award them.

Every badge has a real condition evaluated against stored results — nothing
here is decorative.
"""

from models import db, Badge, UserBadge, TypingResult
from .levels import MAX_LEVEL

BADGE_CATALOGUE = [
    {"code": "first_flight", "name": "First Flight", "icon": "rocket-takeoff",
     "description": "You finished your first run on Clackwell.",
     "requirement": "Complete 1 typing test", "sort_order": 1},
    {"code": "fast_fingers", "name": "Fast Fingers", "icon": "lightning-charge",
     "description": "Crossed 40 words per minute in a single run.",
     "requirement": "Reach 40+ WPM", "sort_order": 2},
    {"code": "speed_demon", "name": "Speed Demon", "icon": "fire",
     "description": "Crossed 60 words per minute in a single run.",
     "requirement": "Reach 60+ WPM", "sort_order": 3},
    {"code": "accuracy_master", "name": "Accuracy Master", "icon": "bullseye",
     "description": "Finished a run at 98% accuracy or better.",
     "requirement": "Hit 98%+ accuracy", "sort_order": 4},
    {"code": "perfect_typist", "name": "Perfect Typist", "icon": "patch-check",
     "description": "A whole run without a single wrong keystroke.",
     "requirement": "Finish a test at 100% accuracy", "sort_order": 5},
    {"code": "consistent", "name": "Steady Hands", "icon": "graph-up",
     "description": "Ten runs in a row, none below 90% accuracy.",
     "requirement": "90%+ accuracy across 10 tests", "sort_order": 6},
    {"code": "streak_7", "name": "Seven Days", "icon": "calendar-check",
     "description": "You showed up every day for a week.",
     "requirement": "Practise 7 days in a row", "sort_order": 7},
    {"code": "streak_30", "name": "Typing Machine", "icon": "calendar-heart",
     "description": "Thirty consecutive days of practice.",
     "requirement": "Practise 30 days in a row", "sort_order": 8},
    {"code": "combo_king", "name": "Combo King", "icon": "stars",
     "description": "Chained 25 correct words without a slip in Word Rush.",
     "requirement": "Reach a 25 word combo", "sort_order": 9},
    {"code": "survivor", "name": "Last One Standing", "icon": "shield-check",
     "description": "Reached the code stage of Survival mode.",
     "requirement": "Survive to stage 5", "sort_order": 10},
    {"code": "champion", "name": "Clackwell Champion", "icon": "trophy",
     "description": "Cleared every level in the ladder.",
     "requirement": "Pass all 7 levels", "sort_order": 11},
    {"code": "legend", "name": "Typing Legend", "icon": "crown",
     "description": "You finished Clackwell. The keyboard works for you now.",
     "requirement": "Clear Level 7", "sort_order": 12},
]


def seed_badges():
    """Insert any badge that isn't in the table yet. Safe to run on every boot."""
    existing = {b.code for b in Badge.query.all()}
    for entry in BADGE_CATALOGUE:
        if entry["code"] not in existing:
            db.session.add(Badge(**entry))
    db.session.commit()


def _award(user, code, earned):
    badge = Badge.query.filter_by(code=code).first()
    if not badge:
        return
    if UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
        return
    db.session.add(UserBadge(user_id=user.id, badge_id=badge.id))
    earned.append({"name": badge.name, "icon": badge.icon, "description": badge.description})


def check_badges(user, result):
    """Run every badge condition after a result is stored. Returns new badges."""
    earned = []
    results = user.results.order_by(TypingResult.created_at.desc()).all()

    _award(user, "first_flight", earned)

    if result.wpm >= 40:
        _award(user, "fast_fingers", earned)
    if result.wpm >= 60:
        _award(user, "speed_demon", earned)
    if result.accuracy >= 98:
        _award(user, "accuracy_master", earned)
    if result.accuracy >= 100:
        _award(user, "perfect_typist", earned)
    if result.max_combo >= 25:
        _award(user, "combo_king", earned)
    if result.mode == "survival" and (result.stage_reached or 0) >= 5:
        _award(user, "survivor", earned)

    last_ten = results[:10]
    if len(last_ten) == 10 and all(r.accuracy >= 90 for r in last_ten):
        _award(user, "consistent", earned)

    if (user.streak or 0) >= 7:
        _award(user, "streak_7", earned)
    if (user.streak or 0) >= 30:
        _award(user, "streak_30", earned)

    cleared = {r.level for r in results if r.passed}
    if all(lvl in cleared for lvl in range(1, MAX_LEVEL + 1)):
        _award(user, "champion", earned)
    if MAX_LEVEL in cleared:
        _award(user, "legend", earned)

    db.session.commit()
    return earned
