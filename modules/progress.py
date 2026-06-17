import json
import os
from datetime import datetime, timedelta


PROGRESS_FILE = "progress.json"
ACTIVITY_FILE = "activity.json"


def load_progress() -> list:
    """
    Loads all saved quiz attempts from progress.json.
    Returns a list of attempt dicts.
    """
    if not os.path.exists(PROGRESS_FILE):
        return []
    try:
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_attempt(topic: str, score: int, total: int, wrong_questions: list):
    """
    Saves a single quiz attempt to progress.json.
    wrong_questions is a list of question strings the user got wrong.
    """
    attempts = load_progress()

    attempt = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "topic": topic,
        "score": score,
        "total": total,
        "percentage": round((score / total) * 100, 1),
        "passed": (score / total) >= 0.6,
        "wrong_questions": wrong_questions
    }

    attempts.append(attempt)

    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(attempts, f, indent=2)
    except Exception as e:
        pass


def delete_all_progress():
    """
    Clears all saved progress by deleting the JSON file.
    """
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)


def get_topic_stats(attempts: list) -> dict:
    """
    Groups attempts by topic and computes per-topic stats.
    Returns a dict: { topic: { attempts, avg_score, best_score, last_date } }
    """
    stats = {}

    for a in attempts:
        topic = a["topic"]
        if topic not in stats:
            stats[topic] = {
                "attempts": 0,
                "percentages": [],
                "best": 0,
                "last_date": ""
            }
        stats[topic]["attempts"] += 1
        stats[topic]["percentages"].append(a["percentage"])
        if a["percentage"] > stats[topic]["best"]:
            stats[topic]["best"] = a["percentage"]
        stats[topic]["last_date"] = a["date"]

    for topic in stats:
        pcts = stats[topic]["percentages"]
        stats[topic]["avg"] = round(sum(pcts) / len(pcts), 1)

    return stats


def get_overall_stats(attempts: list) -> dict:
    """
    Returns overall summary stats across all attempts.
    """
    if not attempts:
        return {}

    total_attempts = len(attempts)
    passed = sum(1 for a in attempts if a["passed"])
    avg_score = round(sum(a["percentage"] for a in attempts) / total_attempts, 1)
    best_score = max(a["percentage"] for a in attempts)
    topics_studied = len(set(a["topic"] for a in attempts))

    return {
        "total_attempts": total_attempts,
        "passed": passed,
        "failed": total_attempts - passed,
        "pass_rate": round((passed / total_attempts) * 100, 1),
        "avg_score": avg_score,
        "best_score": best_score,
        "topics_studied": topics_studied
    }


# ══════════════════════════════════════════════════════════════════════════
# STUDY STREAK TRACKING
# ══════════════════════════════════════════════════════════════════════════
# A "study day" is any day the user used ANY feature: explainer, summarizer,
# quiz, or flashcards. This is tracked separately from quiz scores so the
# streak reflects general engagement, not just quiz-taking.

def log_activity(feature: str):
    """
    Logs that the user used a feature today.
    feature: one of "explain", "summarize", "quiz", "flashcards"
    Only stores one entry per day per feature (no duplicate spam on reruns).
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(ACTIVITY_FILE):
        log = []
    else:
        try:
            with open(ACTIVITY_FILE, "r") as f:
                log = json.load(f)
        except Exception:
            log = []

    # Avoid duplicate entries for the same feature on the same day
    already_logged = any(entry["date"] == today and entry["feature"] == feature for entry in log)
    if not already_logged:
        log.append({"date": today, "feature": feature})
        try:
            with open(ACTIVITY_FILE, "w") as f:
                json.dump(log, f, indent=2)
        except Exception:
            pass


def get_study_dates() -> set:
    """
    Returns a set of unique date strings ("YYYY-MM-DD") on which
    the user did at least one study activity.
    """
    if not os.path.exists(ACTIVITY_FILE):
        return set()
    try:
        with open(ACTIVITY_FILE, "r") as f:
            log = json.load(f)
        return set(entry["date"] for entry in log)
    except Exception:
        return set()


def get_streak_stats() -> dict:
    """
    Computes current streak, longest streak ever, and total active days.
    A streak is broken if there's a gap of more than 1 day between study days.
    """
    dates_str = get_study_dates()

    if not dates_str:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_active_days": 0,
            "studied_today": False
        }

    dates = sorted(datetime.strptime(d, "%Y-%m-%d").date() for d in dates_str)
    today = datetime.now().date()
    studied_today = today in dates

    # ── Longest streak ever (scan all dates for consecutive runs) ──────────
    longest_streak = 1
    run = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        longest_streak = max(longest_streak, run)

    # ── Current streak (count backwards from today or yesterday) ───────────
    current_streak = 0
    cursor = today if studied_today else today - timedelta(days=1)

    if cursor in dates or (cursor == today and (today - timedelta(days=1)) in dates):
        # Walk backwards day by day while consecutive days exist in the set
        check_date = today if studied_today else today - timedelta(days=1)
        date_set = set(dates)
        while check_date in date_set:
            current_streak += 1
            check_date -= timedelta(days=1)
    else:
        current_streak = 0

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_active_days": len(dates),
        "studied_today": studied_today
    }


def get_streak_calendar(days_back: int = 35) -> list:
    """
    Returns a list of dicts for the last `days_back` days, each with
    {date, day_label, studied} — used to render a GitHub-style activity grid.
    """
    studied_dates = get_study_dates()
    today = datetime.now().date()

    calendar = []
    for i in range(days_back - 1, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        calendar.append({
            "date": d_str,
            "day_label": d.strftime("%d %b"),
            "weekday": d.strftime("%a"),
            "studied": d_str in studied_dates
        })

    return calendar