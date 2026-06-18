import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import pandas as pd

from modules.explainer import explain_concept
from modules.summarizer import extract_text, summarize_notes
from modules.quizzes import generate_quiz, check_answers
from modules.flashcards import generate_flashcards, generate_flashcards_from_notes
from modules.progress import (
    load_progress, save_attempt, delete_all_progress, get_topic_stats, get_overall_stats,
    log_activity, get_streak_stats, get_streak_calendar
)
from modules.styling import get_custom_css
from modules.auth import signup, login

# ── Load environment and configure Gemini ─────────────────────────────────────
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key or api_key == "your_gemini_api_key_here":
    st.error("No Gemini API key found. Please add your key to the .env file.")
    st.stop()

client = genai.Client(api_key=api_key)
MODEL = "gemini-2.5-flash"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Study Buddy",
    page_icon="🖋️",
    layout="centered"
)

st.markdown(get_custom_css(), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN / SIGNUP GATE — nothing below this runs until the user is logged in
# ══════════════════════════════════════════════════════════════════════════════
if "username" not in st.session_state:
    st.session_state["username"] = None

if not st.session_state["username"]:
    st.markdown(
        """
        <div class="page-hero">
            <span class="eyebrow">Welcome</span>
            <h1>Study Buddy</h1>
            <div class="subtitle">Log in or create an account to track your own progress.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log In", type="primary"):
            ok, message = login(login_username, login_password)
            if ok:
                st.session_state["username"] = login_username.strip()
                st.rerun()
            else:
                st.error(message)

    with tab_signup:
        signup_username = st.text_input("Choose a username", key="signup_username")
        signup_password = st.text_input("Choose a password", type="password", key="signup_password")
        if st.button("Create Account", type="primary"):
            ok, message = signup(signup_username, signup_password)
            if ok:
                st.success(message + " Switch to the Log In tab to continue.")
            else:
                st.error(message)

    st.stop()

# From here on, the user is logged in.
username = st.session_state["username"]


def hero(eyebrow: str, title: str, subtitle: str):
    """Renders a consistent styled header for each page."""
    st.markdown(
        f"""
        <div class="page-hero">
            <span class="eyebrow">{eyebrow}</span>
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def score_stamp(percentage: int):
    """Renders an animated ink-stamp style result badge."""
    result_class = "pass" if percentage >= 60 else "fail"
    label = "PASS" if percentage >= 60 else "RETRY"

    st.markdown(
        f"""
        <div class="score-stamp-wrap">
            <div class="score-stamp {result_class}">
                <span class="pct">{percentage}%</span>
                <span class="label">{label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="padding: 4px 0 14px 0;">
        <span class="eyebrow">Your learning companion</span>
        <h1 style="font-size:1.6rem; margin:0;">Study Buddy</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(f"Logged in as **{username}**")
if st.sidebar.button("Log Out"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Mini streak badge — quick glance, full detail lives in Progress Tracker
_streak = get_streak_stats(username)
_flame_class = "" if _streak["current_streak"] > 0 else "cold"
_streak_word = "day" if _streak["current_streak"] == 1 else "days"
st.sidebar.markdown(
    f"""
    <div class="streak-sidebar-mini">
        <span class="flame-mini">🔥</span>
        <div>
            <span class="num">{_streak["current_streak"]}</span>
            <span class="txt">{_streak_word} streak</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

page = st.sidebar.radio(
    "Choose a feature",
    [
        "💡 Explain a Concept",
        "📄 Summarize Notes",
        "🧠 Generate Quiz",
        "🃏 Flashcards",
        "📊 Progress Tracker"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")



# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Explain a Concept
# ══════════════════════════════════════════════════════════════════════════════
if page == "💡 Explain a Concept":
    hero("Concept explainer", "Explain a Concept", "Type any topic and get a clear explanation tailored to your level.")

    topic = st.text_input("Enter a topic", placeholder="e.g. Gradient Descent, Newton's Laws, Photosynthesis")
    level = st.selectbox(
        "Your understanding level",
        ["Beginner", "Intermediate", "Advanced"],
        help="Beginner = simple language, Intermediate = some technical terms, Advanced = deep dive"
    )

    if st.button("Explain", type="primary"):
        if not topic.strip():
            st.warning("Please enter a topic first.")
        else:
            with st.spinner(f"Generating explanation for '{topic}'..."):
                result = explain_concept(topic, level.lower(), client, MODEL)
            log_activity(username, "explain")
            st.markdown(f'<div class="notebook-page">{result}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Summarize Notes
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Summarize Notes":
    hero("Notes summarizer", "Summarize Your Notes", "Upload study material and get a clean, structured summary.")

    uploaded = st.file_uploader(
        "Upload your notes",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, Word document (.docx), plain text (.txt)"
    )

    if uploaded:
        st.success(f"File uploaded: {uploaded.name}")

        if st.button("Summarize Notes", type="primary"):
            with st.spinner("Reading your file and summarizing..."):
                text = extract_text(uploaded)
                if text.startswith("Error") or not text.strip():
                    st.error("Could not extract text from the file. Try a different file.")
                else:
                    result = summarize_notes(text, client, MODEL)
            if not text.startswith("Error") and text.strip():
                log_activity(username, "summarize")
                st.markdown(f'<div class="notebook-page">{result}</div>', unsafe_allow_html=True)

                with st.expander("View extracted raw text"):
                    st.text(text[:2000] + ("..." if len(text) > 2000 else ""))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Generate Quiz
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧠 Generate Quiz":
    hero("Knowledge check", "Generate a Quiz", "Test your knowledge with AI-generated questions on any topic.")

    topic = st.text_input("Topic to quiz on", placeholder="e.g. Machine Learning, World War 2, Python basics")
    num_q = st.slider("Number of questions", min_value=3, max_value=10, value=5)

    if st.button("Generate Quiz", type="primary"):
        if not topic.strip():
            st.warning("Please enter a topic first.")
        else:
            with st.spinner(f"Creating {num_q} questions on '{topic}'..."):
                questions = generate_quiz(topic, num_q, client, MODEL)

            if not questions:
                st.error("Failed to generate quiz. Please try again.")
            else:
                log_activity(username, "quiz")
                st.session_state["quiz_questions"] = questions
                st.session_state["quiz_answers"] = {}
                st.session_state["quiz_submitted"] = False
                st.session_state["quiz_topic"] = topic
                st.success(f"Generated {len(questions)} questions!")

    # Display quiz if questions are ready
    if "quiz_questions" in st.session_state and not st.session_state.get("quiz_submitted", False):
        st.markdown("### Answer the questions below")

        for i, q in enumerate(st.session_state["quiz_questions"]):
            st.markdown(f'<div class="notebook-page"><strong>Q{i+1}. {q["question"]}</strong></div>', unsafe_allow_html=True)
            choice = st.radio(
                label=f"Select answer for Q{i+1}",
                options=q["options"],
                key=f"quiz_q_{i}",
                index=None,
                label_visibility="collapsed"
            )
            st.session_state["quiz_answers"][i] = choice

        if st.button("Submit Quiz", type="primary"):
            unanswered = [i for i, a in st.session_state["quiz_answers"].items() if a is None]
            if unanswered:
                st.warning(f"You have not answered question(s): {[u+1 for u in unanswered]}")
            else:
                st.session_state["quiz_submitted"] = True
                st.rerun()

    # Show results after submission
    if st.session_state.get("quiz_submitted", False):
        st.markdown("### Quiz Results")

        results = check_answers(
            st.session_state["quiz_questions"],
            st.session_state["quiz_answers"]
        )

        score = results["score"]
        total = results["total"]
        percentage = int((score / total) * 100)

        # Save to progress tracker (only once per submission)
        if not st.session_state.get("progress_saved", False):
            wrong_qs = [r["question"] for r in results["results"] if not r["is_correct"]]
            save_attempt(
                username=username,
                topic=st.session_state.get("quiz_topic", "Unknown"),
                score=score,
                total=total,
                wrong_questions=wrong_qs
            )
            st.session_state["progress_saved"] = True

        score_stamp(percentage)
        st.markdown(
            f'<p style="text-align:center; opacity:0.7; margin-top:-10px;">{score} out of {total} correct</p>',
            unsafe_allow_html=True
        )

        st.markdown("---")
        for i, r in enumerate(results["results"]):
            if r["is_correct"]:
                st.success(f"**Q{i+1}. {r['question']}**\n\nYour answer: {r['user_answer']} ✅")
            else:
                st.error(f"**Q{i+1}. {r['question']}**\n\nYour answer: {r['user_answer']} ❌\n\nCorrect answer: **{r['correct_answer']}**")
            st.caption(f"Explanation: {r['explanation']}")

        if st.button("Retake Quiz"):
            del st.session_state["quiz_questions"]
            del st.session_state["quiz_answers"]
            st.session_state["quiz_submitted"] = False
            st.session_state["progress_saved"] = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Flashcards
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🃏 Flashcards":
    hero("Active recall", "Flashcard Maker", "Generate flashcards from a topic name or from your uploaded notes.")

    mode = st.radio("Generate from", ["Topic name", "Uploaded notes"], horizontal=True)
    num_cards = st.slider("Number of flashcards", min_value=5, max_value=20, value=10)

    if mode == "Topic name":
        topic = st.text_input("Enter a topic", placeholder="e.g. Neural Networks, French Revolution")
        if st.button("Generate Flashcards", type="primary"):
            if not topic.strip():
                st.warning("Please enter a topic first.")
            else:
                with st.spinner(f"Creating {num_cards} flashcards on '{topic}'..."):
                    cards = generate_flashcards(topic, num_cards, client, MODEL)
                if not cards:
                    st.error("Failed to generate flashcards. Please try again.")
                else:
                    log_activity(username, "flashcards")
                    st.session_state["flashcards"] = cards
                    st.session_state["card_index"] = 0
                    st.session_state["show_back"] = False

    else:
        uploaded = st.file_uploader("Upload notes", type=["pdf", "docx", "txt"])
        if uploaded and st.button("Generate Flashcards from Notes", type="primary"):
            with st.spinner("Reading notes and creating flashcards..."):
                text = extract_text(uploaded)
                cards = generate_flashcards_from_notes(text, num_cards, client, MODEL)
            if not cards:
                st.error("Failed to generate flashcards. Please try again.")
            else:
                log_activity(username, "flashcards")
                st.session_state["flashcards"] = cards
                st.session_state["card_index"] = 0
                st.session_state["show_back"] = False

    # Display flashcards
    if "flashcards" in st.session_state and st.session_state["flashcards"]:
        all_cards = st.session_state["flashcards"]
        idx = st.session_state["card_index"]
        card = all_cards[idx]
        flipped_class = "flipped" if st.session_state["show_back"] else ""

        # Dot progress indicator
        dots_html = "".join(
            f'<div class="dot {"active" if i == idx else ""}"></div>' for i in range(len(all_cards))
        )
        st.markdown(f'<div class="card-progress-dots">{dots_html}</div>', unsafe_allow_html=True)

        # Animated flip card
        st.markdown(
            f"""
            <div class="card-stack-wrap">
                <div class="index-card {flipped_class}">
                    <div class="index-face index-face-front">
                        <p>{card['front']}</p>
                    </div>
                    <div class="index-face index-face-back">
                        <p>{card['back']}</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("⬅ Prev") and idx > 0:
                st.session_state["card_index"] -= 1
                st.session_state["show_back"] = False
                st.rerun()

        with col2:
            if st.button("🔄 Flip Card", type="primary"):
                st.session_state["show_back"] = not st.session_state["show_back"]
                st.rerun()

        with col3:
            if st.button("Next ➡") and idx < len(all_cards) - 1:
                st.session_state["card_index"] += 1
                st.session_state["show_back"] = False
                st.rerun()

        with col4:
            if st.button("🔁 Restart"):
                st.session_state["card_index"] = 0
                st.session_state["show_back"] = False
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Progress Tracker
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Progress Tracker":
    hero("Your journey", "Progress Tracker", "Track your quiz performance over time across all topics.")

    # ── Study Streak Section ────────────────────────────────────────────────
    streak = get_streak_stats(username)
    flame_class = "" if streak["current_streak"] > 0 else "cold"

    if streak["current_streak"] == 0:
        streak_text = "Start a streak — use any feature today to begin."
    elif streak["studied_today"]:
        streak_text = f"You're on fire! Keep it going tomorrow."
    else:
        streak_text = "Don't break the streak — study again today!"

    day_word = "day" if streak["current_streak"] == 1 else "days"

    st.markdown(
        f"""
        <div class="streak-badge-wrap">
            <span class="streak-flame {flame_class}">🔥</span>
            <div>
                <span class="streak-count">{streak["current_streak"]} {day_word}</span>
                <div class="streak-text">{streak_text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_a, col_b = st.columns(2)
    col_a.metric("Longest Streak", f"{streak['longest_streak']} days")
    col_b.metric("Total Active Days", streak["total_active_days"])

    st.markdown("##### Last 35 Days")
    calendar = get_streak_calendar(username, 35)
    cells_html = "".join(
        f'<div class="activity-cell {"studied" if c["studied"] else ""}" title="{c["day_label"]}"></div>'
        for c in calendar
    )
    st.markdown(f'<div class="activity-grid">{cells_html}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="activity-legend">
            <span class="swatch" style="background: var(--line);"></span> No activity
            <span class="swatch" style="background: var(--amber-deep); margin-left:10px;"></span> Studied
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    attempts = load_progress(username)

    if not attempts:
        st.info("No quiz attempts yet. Go to **Generate Quiz**, take a quiz, and your results will appear here automatically.")
    else:
        overall = get_overall_stats(attempts)
        topic_stats = get_topic_stats(attempts)

        st.markdown("### Overall Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Quizzes", overall["total_attempts"])
        col2.metric("Avg Score", f"{overall['avg_score']}%")
        col3.metric("Best Score", f"{overall['best_score']}%")
        col4.metric("Topics Studied", overall["topics_studied"])

        col5, col6 = st.columns(2)
        col5.metric("Passed", overall["passed"], help="Score ≥ 60%")
        col6.metric("Failed", overall["failed"], help="Score < 60%")

        st.markdown("---")

        st.markdown("### Score Trend (All Attempts)")
        chart_data = {
            "Attempt": [f"#{i+1} {a['topic'][:15]}" for i, a in enumerate(attempts)],
            "Score (%)": [a["percentage"] for a in attempts]
        }
        df_trend = pd.DataFrame(chart_data).set_index("Attempt")
        st.line_chart(df_trend, use_container_width=True)

        st.markdown("---")

        st.markdown("### Performance by Topic")
        topic_rows = []
        for topic, s in topic_stats.items():
            topic_rows.append({
                "Topic": topic,
                "Attempts": s["attempts"],
                "Avg Score (%)": s["avg"],
                "Best Score (%)": s["best"],
                "Last Studied": s["last_date"]
            })
        df_topics = pd.DataFrame(topic_rows)
        st.dataframe(df_topics, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.markdown("### Recent Attempts")
        for i, a in enumerate(reversed(attempts[-10:])):
            attempt_num = len(attempts) - i
            passed_label = "✅ Pass" if a["passed"] else "❌ Fail"
            with st.expander(f"#{attempt_num} — {a['topic']} | {a['percentage']}% | {passed_label} | {a['date']} {a['time']}"):
                st.markdown(f"**Score:** {a['score']} / {a['total']} ({a['percentage']}%)")
                st.markdown(f"**Result:** {passed_label}")
                st.markdown(f"**Date:** {a['date']} at {a['time']}")

                if a["wrong_questions"]:
                    st.markdown("**Questions you got wrong:**")
                    for q in a["wrong_questions"]:
                        st.markdown(f"- {q}")
                else:
                    st.markdown("**Perfect score! No wrong answers.** 🎉")

        st.markdown("---")

        st.markdown("### Topics to Improve")
        weak = [(t, s) for t, s in topic_stats.items() if s["avg"] < 60]
        if weak:
            for topic, s in sorted(weak, key=lambda x: x[1]["avg"]):
                st.warning(f"**{topic}** — Avg score: {s['avg']}% over {s['attempts']} attempt(s). Needs more practice.")
        else:
            st.success("You are passing all topics! Keep it up. 🎉")

        st.markdown("---")

        st.markdown("### Reset Progress")
        if st.button("🗑️ Delete All Progress Data", type="secondary"):
            st.session_state["confirm_delete"] = True

        if st.session_state.get("confirm_delete", False):
            st.error("Are you sure? This will permanently delete all your quiz history.")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, delete everything"):
                    delete_all_progress(username)
                    st.session_state["confirm_delete"] = False
                    st.success("All progress deleted.")
                    st.rerun()
            with col_no:
                if st.button("Cancel"):
                    st.session_state["confirm_delete"] = False
                    st.rerun()