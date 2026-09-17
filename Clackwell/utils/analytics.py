"""Turns stored results into chart series, the activity grid, and the
written insights shown on the dashboard.

Every sentence produced by build_insights() is derived from real rows.
"""

from collections import defaultdict
from datetime import date, timedelta

from models import TypingResult
from .levels import get_level

MODE_LABELS = {
    "time": "Time Attack",
    "sentence": "Sentence Challenge",
    "rush": "Word Rush",
    "survival": "Survival",
}


def _rows(user, days=None):
    q = user.results.order_by(TypingResult.created_at.asc())
    if days:
        cutoff = date.today() - timedelta(days=days)
        q = q.filter(TypingResult.created_at >= cutoff)
    return q.all()


def progress_series(user, limit=30):
    """WPM and accuracy for the most recent runs, oldest first."""
    rows = user.results.order_by(TypingResult.created_at.desc()).limit(limit).all()[::-1]
    return {
        "labels": [r.created_at.strftime("%d %b") for r in rows],
        "wpm": [r.wpm for r in rows],
        "accuracy": [r.accuracy for r in rows],
    }


def weekday_series(user):
    """Average performance per weekday across the last 8 weeks."""
    rows = _rows(user, days=56)
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    buckets = defaultdict(list)
    for r in rows:
        buckets[order[r.created_at.weekday()]].append(r)

    return {
        "labels": order,
        "tests": [len(buckets[d]) for d in order],
        "wpm": [round(sum(x.wpm for x in buckets[d]) / len(buckets[d]), 1) if buckets[d] else 0
                for d in order],
        "accuracy": [round(sum(x.accuracy for x in buckets[d]) / len(buckets[d]), 1) if buckets[d] else 0
                     for d in order],
    }


def level_series(user):
    rows = _rows(user)
    buckets = defaultdict(list)
    for r in rows:
        buckets[r.level].append(r.wpm)
    levels = sorted(buckets)
    return {
        "labels": [f"L{n} · {get_level(n)['title']}" for n in levels],
        "wpm": [round(sum(buckets[n]) / len(buckets[n]), 1) for n in levels],
    }


def mode_distribution(user):
    """Minutes spent in each mode."""
    rows = _rows(user)
    buckets = defaultdict(float)
    for r in rows:
        buckets[MODE_LABELS.get(r.mode, r.mode)] += r.time_taken
    return {
        "labels": list(buckets.keys()),
        "minutes": [round(v / 60, 1) for v in buckets.values()],
    }


def activity_grid(user, weeks=12):
    """Daily buckets for the contribution-style grid, oldest week first."""
    rows = _rows(user, days=weeks * 7 + 7)
    by_day = defaultdict(list)
    for r in rows:
        by_day[r.created_at.date()].append(r)

    today = date.today()
    start = today - timedelta(days=weeks * 7 - 1)
    start -= timedelta(days=start.weekday())     # align to a Monday

    days = []
    cursor = start
    while cursor <= today:
        items = by_day.get(cursor, [])
        seconds = sum(i.time_taken for i in items)
        days.append({
            "date": cursor.isoformat(),
            "label": cursor.strftime("%d %B %Y"),
            "tests": len(items),
            "wpm": round(sum(i.wpm for i in items) / len(items), 1) if items else 0,
            "accuracy": round(sum(i.accuracy for i in items) / len(items), 1) if items else 0,
            "minutes": round(seconds / 60, 1),
            "intensity": _intensity(len(items)),
        })
        cursor += timedelta(days=1)
    return days


def _intensity(count):
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def build_insights(user):
    """Short, specific observations. Returns a list of {title, body} dicts."""
    rows = _rows(user)
    if len(rows) < 3:
        return [{
            "title": "Not enough runs yet",
            "body": "Finish three tests and Clackwell starts comparing your weeks, "
                    "modes and levels here.",
        }]

    out = []
    today = date.today()

    this_week = [r for r in rows if r.created_at.date() >= today - timedelta(days=7)]
    last_week = [r for r in rows
                 if today - timedelta(days=14) <= r.created_at.date() < today - timedelta(days=7)]

    if this_week and last_week:
        a = sum(r.wpm for r in this_week) / len(this_week)
        b = sum(r.wpm for r in last_week) / len(last_week)
        if b > 0:
            delta = (a - b) / b * 100
            if abs(delta) < 2:
                out.append({
                    "title": "Speed is holding steady",
                    "body": f"You averaged {a:.0f} WPM this week against {b:.0f} last week. "
                            "A flat week after a climb is normal — it usually means the gain is setting in.",
                })
            elif delta > 0:
                out.append({
                    "title": f"Up {delta:.0f}% on last week",
                    "body": f"Your average moved from {b:.0f} to {a:.0f} WPM across "
                            f"{len(this_week)} runs. Keep the same session length for another week "
                            "before pushing for more.",
                })
            else:
                out.append({
                    "title": f"Down {abs(delta):.0f}% on last week",
                    "body": f"You averaged {a:.0f} WPM against {b:.0f} the week before. "
                            "Dips usually follow a jump in difficulty — try a level below your "
                            "current one to reset your rhythm.",
                })

    by_mode = defaultdict(list)
    for r in rows:
        by_mode[r.mode].append(r)
    scored = {m: sum(x.accuracy for x in v) / len(v) for m, v in by_mode.items() if len(v) >= 2}
    if len(scored) >= 2:
        best = max(scored, key=scored.get)
        worst = min(scored, key=scored.get)
        out.append({
            "title": f"{MODE_LABELS.get(best, best)} is your strongest mode",
            "body": f"You hold {scored[best]:.0f}% accuracy there, against "
                    f"{scored[worst]:.0f}% in {MODE_LABELS.get(worst, worst)}. "
                    f"A few deliberate {MODE_LABELS.get(worst, worst)} runs would close that gap fastest.",
        })

    short_runs = [r for r in rows if r.time_taken <= 35]
    long_runs = [r for r in rows if r.time_taken >= 60]
    if len(short_runs) >= 2 and len(long_runs) >= 2:
        s = sum(r.accuracy for r in short_runs) / len(short_runs)
        l = sum(r.accuracy for r in long_runs) / len(long_runs)
        if s - l >= 3:
            out.append({
                "title": "Accuracy fades on longer runs",
                "body": f"Short tests sit at {s:.0f}% accuracy but 60-second runs drop to {l:.0f}%. "
                        "That's an endurance gap, not a speed one — add one 120-second run per session.",
            })
        elif l - s >= 3:
            out.append({
                "title": "You settle in as you go",
                "body": f"Long runs hold {l:.0f}% accuracy while short bursts sit at {s:.0f}%. "
                        "Type a warm-up line before starting a timed test and the gap should close.",
            })

    worst_hour = defaultdict(list)
    for r in rows:
        worst_hour[r.created_at.hour].append(r.wpm)
    if len(worst_hour) >= 3:
        best_hour = max(worst_hour, key=lambda h: sum(worst_hour[h]) / len(worst_hour[h]))
        avg = sum(worst_hour[best_hour]) / len(worst_hour[best_hour])
        out.append({
            "title": f"Your fastest hour is around {best_hour:02d}:00",
            "body": f"Runs started then average {avg:.0f} WPM. If you can move practice into "
                    "that window, you'll set personal bests more often.",
        })

    return out[:4]
