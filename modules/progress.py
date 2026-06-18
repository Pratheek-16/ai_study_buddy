import json
from datetime import datetime, timedelta

from modules.db import get_connection


def load_progress(username: str) -> list:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT topic, score, total, percentage, passed, wrong_questions, date, time
            FROM progress
            WHERE username = %s
            ORDER BY id ASC
            """,
            (username,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        return []

    attempts = []
    for topic, score, total, percentage, passed, wrong_questions, date, time in rows:
        attempts.append({
            "date": date,
            "time": time,
            "topic": topic,
            "score": score,
            "total": total,
            "percentage": float(percentage),
            "passed": bool(passed),
            "wrong_questions": json.loads(wrong_questions) if wrong_questions else []
        })
    return attempts


def save_attempt(username: str, topic: str, score: int, total: int, wrong_questions: list):
    percentage = round((score / total) * 100, 1)
    passed = (score / total) >= 0.6
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO progress
                (username, topic, score, total, percentage, passed, wrong_questions, date, time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (username, topic, score, total, percentage, passed,
             json.dumps(wrong_questions), date_str, time_str)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


def delete_all_progress(username: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM progress WHERE username = %s", (username,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


def get_topic_stats(attempts: list) -> dict:
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


def log_activity(username: str, feature: str):
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM activity WHERE username = %s AND date = %s AND feature = %s",
            (username, today, feature)
        )
        already_logged = cur.fetchone() is not None

        if not already_logged:
            cur.execute(
                "INSERT INTO activity (username, date, feature) VALUES (%s, %s, %s)",
                (username, today, feature)
            )
            conn.commit()

        cur.close()
        conn.close()
    except Exception:
        pass


def get_study_dates(username: str) -> set:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT date FROM activity WHERE username = %s", (username,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return set(r[0] for r in rows)
    except Exception:
        return set()


def get_streak_stats(username: str) -> dict:
    dates_str = get_study_dates(username)

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

    longest_streak = 1
    run = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        longest_streak = max(longest_streak, run)

    current_streak = 0
    cursor = today if studied_today else today - timedelta(days=1)

    if cursor in dates or (cursor == today and (today - timedelta(days=1)) in dates):
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


def get_streak_calendar(username: str, days_back: int = 35) -> list:
    studied_dates = get_study_dates(username)
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