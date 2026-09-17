"""Optional: fills one demo account with eight weeks of realistic runs so the
dashboard, charts and activity grid have something to show during a demo.

    python seed_demo.py

Sign in afterwards as  demo / demo1234

Nothing here touches real accounts — it only creates or refills 'demo'.
"""

import random
from datetime import datetime, timedelta

from app import create_app
from models import db, User, TypingResult
from utils import scoring
from utils.badges import check_badges

app = create_app()


def run():
    with app.app_context():
        user = User.query.filter_by(username="demo").first()
        if not user:
            user = User(name="Demo Typist", username="demo", email="demo@clackwell.local",
                        avatar="D", tagline="Seeded account for the project walkthrough")
            user.set_password("demo1234")
            db.session.add(user)
            db.session.commit()
        else:
            TypingResult.query.filter_by(user_id=user.id).delete()
            user.xp, user.current_level, user.streak, user.best_streak = 0, 1, 0, 0
            db.session.commit()

        modes = ["time", "time", "sentence", "rush", "survival"]
        skill = 28.0          # starting WPM, drifts upward over the weeks
        today = datetime.utcnow()

        for days_ago in range(56, -1, -1):
            if random.random() < 0.3:           # rest days
                continue
            day = today - timedelta(days=days_ago)
            skill += random.uniform(-0.25, 0.65)

            for _ in range(random.randint(1, 4)):
                mode = random.choice(modes)
                level = min(7, 1 + int((skill - 26) / 6))
                level = max(1, min(level, 7))

                wpm_raw = max(12, random.gauss(skill, 4))
                accuracy = min(100, max(72, random.gauss(93, 4)))
                seconds = {"time": random.choice([15, 30, 60, 120]),
                           "sentence": random.uniform(18, 45),
                           "rush": random.uniform(35, 60),
                           "survival": random.uniform(40, 110)}[mode]

                correct_chars = int((wpm_raw * 5) * (seconds / 60))
                wrong_chars = int(correct_chars * (100 - accuracy) / 100)

                metrics = scoring.compute_metrics(correct_chars, wrong_chars, seconds)
                correct_words = int(correct_chars / 5.5)
                wrong_words = max(0, int(wrong_chars / 5))
                combo = random.randint(0, 22) if mode == "rush" else 0
                score = scoring.compute_score(metrics, level, correct_words, wrong_words, combo, mode)
                passed = scoring.level_passed(metrics, level, score)

                row = TypingResult(
                    user_id=user.id, level=level, mode=mode,
                    wpm=metrics["wpm"], cpm=metrics["cpm"], accuracy=metrics["accuracy"],
                    correct_words=correct_words, incorrect_words=wrong_words,
                    correct_characters=correct_chars, incorrect_characters=wrong_chars,
                    max_combo=combo, stage_reached=random.randint(1, 5) if mode == "survival" else 0,
                    score=score, xp_earned=60, time_taken=round(seconds, 1), passed=passed,
                    created_at=day.replace(hour=random.randint(7, 22), minute=random.randint(0, 59)),
                )
                db.session.add(row)
                user.xp += 60
                if passed and level == user.current_level and level < 7:
                    user.current_level = level + 1

            user.touch_streak(day.date())

        db.session.commit()
        last = user.results.order_by(TypingResult.created_at.desc()).first()
        check_badges(user, last)

        print(f"Seeded {user.results.count()} runs for 'demo'. Password: demo1234")


if __name__ == "__main__":
    run()
