"""All score maths lives server-side.

The browser only reports raw counts (characters, words, seconds, combo).
WPM, accuracy, score and XP are recomputed here so a tampered client can't
mint a leaderboard entry.
"""

from .levels import get_level

MAX_PLAUSIBLE_WPM = 260


def _clamp(value, low, high):
    return max(low, min(value, high))


def compute_metrics(correct_chars, incorrect_chars, seconds):
    """Standard net-WPM convention: 5 characters = 1 word."""
    correct_chars = max(0, int(correct_chars))
    incorrect_chars = max(0, int(incorrect_chars))
    seconds = _clamp(float(seconds or 0), 0.5, 3600)

    typed = correct_chars + incorrect_chars
    minutes = seconds / 60.0

    wpm = round((correct_chars / 5.0) / minutes, 1) if minutes else 0.0
    cpm = round(correct_chars / minutes, 1) if minutes else 0.0
    accuracy = round((correct_chars / typed) * 100, 1) if typed else 0.0

    return {
        "wpm": _clamp(wpm, 0, MAX_PLAUSIBLE_WPM),
        "cpm": _clamp(cpm, 0, MAX_PLAUSIBLE_WPM * 5),
        "accuracy": _clamp(accuracy, 0, 100),
        "typed_characters": typed,
    }


def compute_score(metrics, level_number, correct_words, incorrect_words, max_combo, mode):
    """Base + speed + accuracy + combo + level, with an accuracy gate.

    The gate is the important bit: below 90% accuracy the whole score is scaled
    down, so machine-gunning the keyboard never beats typing carefully.
    """
    level = get_level(level_number)
    wpm = metrics["wpm"]
    accuracy = metrics["accuracy"]

    base = correct_words * 10
    speed_bonus = wpm * 4
    accuracy_bonus = max(0, (accuracy - 70)) * 6      # nothing below 70%
    combo_bonus = max_combo * 5
    penalty = incorrect_words * 6

    raw = base + speed_bonus + accuracy_bonus + combo_bonus - penalty
    raw *= level["multiplier"]

    # Accuracy gate: 100% -> x1.0, 90% -> x1.0, 80% -> x0.8, 60% -> x0.4
    gate = 1.0 if accuracy >= 90 else max(0.2, (accuracy - 50) / 40)
    raw *= gate

    if mode == "survival":
        raw *= 1.15      # survival runs are all-or-nothing, so they pay a little more

    return int(max(0, round(raw)))


def compute_xp(metrics, level_number, passed, is_personal_best, streak_extended):
    """Returns (total_xp, breakdown list of (label, amount))."""
    accuracy = metrics["accuracy"]
    lines = [("Test completed", 50)]

    if accuracy >= 100:
        lines.append(("Flawless run — 100% accuracy", 100))
    elif accuracy >= 95:
        lines.append(("95%+ accuracy", 50))
    elif accuracy >= 90:
        lines.append(("90%+ accuracy", 25))

    if is_personal_best:
        lines.append(("New personal best", 100))
    if passed:
        lines.append((f"Level {level_number} target met", get_level(level_number)["xp_reward"]))
    if streak_extended:
        lines.append(("Daily streak kept alive", 50))

    return sum(amount for _, amount in lines), lines


def level_passed(metrics, level_number, score):
    level = get_level(level_number)
    return (
        metrics["wpm"] >= level["target_wpm"]
        and metrics["accuracy"] >= level["target_accuracy"]
        and score >= level["required_score"]
    )
