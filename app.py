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
from modules.resume_reviewer import review_resume
from modules.resume_builder import polish_bullets, generate_resume_pdf, generate_resume_docx

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
            <div class="subtitle">Log in or create an account through sign up  to track your own progress.</div>
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
        "📊 Progress Tracker",
        "📝 Resume Reviewer",
        "🏗️ Resume Builder",
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

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — Resume Reviewer
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Resume Reviewer":
    hero("AI-Powered", "Resume Reviewer", "Upload your resume and get instant structured feedback with ATS compatibility check.")

    uploaded = st.file_uploader("Upload your resume", type=["pdf", "docx"], help="PDF or Word document (.docx/.pdf)")

    if uploaded:
        st.success(f"Uploaded: {uploaded.name}")

        if st.button("Analyse Resume", type="primary"):
            from modules.summarizer import extract_text
            with st.spinner("Gemini is reviewing your resume..."):
                text = extract_text(uploaded)
                if not text.strip() or text.startswith("Error"):
                    st.error("Could not extract text. Make sure your PDF is not scanned/image-only.")
                    st.stop()
                result = review_resume(text, client, MODEL)

            if "error" in result:
                st.error(f"Review failed: {result['error']}")
            else:
                log_activity(username, "resume_review")

                score = result.get("overall_score", 0)
                color = "#9BC489" if score >= 7 else "#D4A24E" if score >= 5 else "#C16B5E"
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; gap:20px; padding:20px;
                                background:var(--card); border-radius:12px; margin-bottom:20px;
                                border:1px solid var(--line-deep);">
                        <div style="font-size:3rem; font-weight:700; color:{color}; font-family:'Source Serif 4',serif;">
                            {score}/10
                        </div>
                        <div>
                            <div style="font-size:1rem; font-weight:600; color:var(--ink);">Overall Resume Score</div>
                            <div style="color:var(--ink-soft); font-size:0.9rem; margin-top:4px;">
                                {result.get("overall_summary", "")}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                ats = result.get("ats_score", 0)
                ats_color = "#9BC489" if ats >= 7 else "#D4A24E" if ats >= 5 else "#C16B5E"
                st.markdown("### ATS Compatibility")
                col_ats1, col_ats2 = st.columns([1, 3])
                with col_ats1:
                    st.markdown(f'<div style="font-size:2rem; font-weight:700; color:{ats_color};">{ats}/10</div>', unsafe_allow_html=True)
                with col_ats2:
                    issues = result.get("ats_issues", [])
                    if issues:
                        for issue in issues:
                            st.markdown(f"- {issue}")
                    else:
                        st.success("No major ATS issues found!")

                st.markdown("---")
                st.markdown("### Section Feedback")
                section_icons = {"summary": "Summary", "education": "Education", "experience": "Experience", "skills": "Skills", "projects": "Projects"}
                sections = result.get("sections", {})
                for key, label in section_icons.items():
                    sec = sections.get(key, {})
                    present = sec.get("present", False)
                    sec_score = sec.get("score", 0)
                    feedback = sec.get("feedback", "Not evaluated.")
                    sec_color = "#9BC489" if sec_score >= 7 else "#D4A24E" if sec_score >= 5 else "#C16B5E"
                    not_found = "" if present else " (not found)"
                    with st.expander(f"{label}{not_found}  —  {sec_score}/10", expanded=True):
                        st.markdown(f'<span style="color:{sec_color}; font-weight:600;">{sec_score}/10</span>', unsafe_allow_html=True)
                        st.write(feedback)

                st.markdown("---")
                col_s, col_i = st.columns(2)
                with col_s:
                    st.markdown("### Strengths")
                    for s in result.get("strengths", []):
                        st.markdown(f'<div style="padding:10px 14px; background:rgba(155,196,137,0.12); border-left:3px solid var(--sage); border-radius:6px; margin-bottom:8px;">✅ {s}</div>', unsafe_allow_html=True)
                with col_i:
                    st.markdown("### Improvements")
                    for imp in result.get("improvements", []):
                        st.markdown(f'<div style="padding:10px 14px; background:rgba(193,107,94,0.12); border-left:3px solid var(--brick); border-radius:6px; margin-bottom:8px;">🔺 {imp}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — Resume Builder
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Resume Builder":
    hero("AI-Assisted", "Resume Builder", "Fill in your details step by step — Gemini writes polished bullet points for you.")

    if "rb_step" not in st.session_state:
        st.session_state["rb_step"] = 1
    if "rb_data" not in st.session_state:
        st.session_state["rb_data"] = {}

    step = st.session_state["rb_step"]
    total_steps = 5

    st.markdown(
        f'<div style="margin-bottom:20px;"><div style="font-size:0.8rem; color:var(--ink-soft); margin-bottom:6px;">Step {step} of {total_steps}</div>'
        f'<div style="background:var(--line); border-radius:4px; height:6px;">'
        f'<div style="background:var(--amber); width:{int(step/total_steps*100)}%; height:6px; border-radius:4px;"></div></div></div>',
        unsafe_allow_html=True
    )

    if step == 1:
        st.markdown("### Personal Information")
        p = st.session_state["rb_data"].get("personal", {})
        name = st.text_input("Full Name *", value=p.get("name", ""))
        email = st.text_input("Email *", value=p.get("email", ""))
        phone = st.text_input("Phone", value=p.get("phone", ""))
        location = st.text_input("Location", value=p.get("location", ""))
        linkedin = st.text_input("LinkedIn URL (optional)", value=p.get("linkedin", ""))
        summary_raw = st.text_area("Professional Summary (rough notes)", value=st.session_state["rb_data"].get("summary_raw", ""),
            placeholder="e.g. Final year CS student, strong in Python and ML, built 3 projects")
        if st.button("Next →", type="primary"):
            if not name.strip() or not email.strip():
                st.warning("Name and email are required.")
            else:
                st.session_state["rb_data"]["personal"] = {"name": name, "email": email, "phone": phone, "location": location, "linkedin": linkedin}
                st.session_state["rb_data"]["summary_raw"] = summary_raw
                st.session_state["rb_step"] = 2
                st.rerun()

    elif step == 2:
        st.markdown("### Education")
        edu_list = st.session_state["rb_data"].get("education", [{"degree":"","institution":"","year":"","gpa":""}])
        updated_edu = []
        for i, edu in enumerate(edu_list):
            st.markdown(f"**Entry {i+1}**")
            c1, c2 = st.columns(2)
            degree = c1.text_input("Degree", value=edu.get("degree",""), key=f"deg_{i}")
            institution = c2.text_input("Institution", value=edu.get("institution",""), key=f"inst_{i}")
            c3, c4 = st.columns(2)
            year = c3.text_input("Year / Duration", value=edu.get("year",""), key=f"yr_{i}")
            gpa = c4.text_input("CGPA / GPA (optional)", value=edu.get("gpa",""), key=f"gpa_{i}")
            updated_edu.append({"degree":degree,"institution":institution,"year":year,"gpa":gpa})
            st.markdown("---")
        col_add, col_back, col_next = st.columns(3)
        if col_add.button("Add Another"):
            updated_edu.append({"degree":"","institution":"","year":"","gpa":""})
            st.session_state["rb_data"]["education"] = updated_edu
            st.rerun()
        if col_back.button("← Back"):
            st.session_state["rb_data"]["education"] = updated_edu
            st.session_state["rb_step"] = 1
            st.rerun()
        if col_next.button("Next →", type="primary"):
            st.session_state["rb_data"]["education"] = updated_edu
            st.session_state["rb_step"] = 3
            st.rerun()

    elif step == 3:
        st.markdown("### Projects")
        proj_list = st.session_state["rb_data"].get("projects_raw", [{"name":"","tech":"","desc":""}])
        updated_proj = []
        for i, proj in enumerate(proj_list):
            st.markdown(f"**Project {i+1}**")
            c1, c2 = st.columns(2)
            pname = c1.text_input("Project Name", value=proj.get("name",""), key=f"pn_{i}")
            tech = c2.text_input("Tech Stack", value=proj.get("tech",""), key=f"pt_{i}")
            desc = st.text_area("What did you build?", value=proj.get("desc",""), key=f"pd_{i}")
            updated_proj.append({"name":pname,"tech":tech,"desc":desc})
            st.markdown("---")
        col_add, col_back, col_next = st.columns(3)
        if col_add.button("Add Project"):
            updated_proj.append({"name":"","tech":"","desc":""})
            st.session_state["rb_data"]["projects_raw"] = updated_proj
            st.rerun()
        if col_back.button("← Back"):
            st.session_state["rb_data"]["projects_raw"] = updated_proj
            st.session_state["rb_step"] = 2
            st.rerun()
        if col_next.button("Next →", type="primary"):
            st.session_state["rb_data"]["projects_raw"] = updated_proj
            st.session_state["rb_step"] = 4
            st.rerun()

    elif step == 4:
        st.markdown("### Skills")
        sk = st.session_state["rb_data"].get("skills_raw", {})
        languages = st.text_input("Programming Languages (comma separated)", value=sk.get("languages",""), placeholder="Python, Java, JavaScript")
        frameworks = st.text_input("Frameworks & Libraries", value=sk.get("frameworks",""), placeholder="React, TensorFlow, FastAPI")
        tools = st.text_input("Tools & Platforms", value=sk.get("tools",""), placeholder="Git, Docker, AWS")
        soft = st.text_input("Soft Skills (optional)", value=sk.get("soft",""))
        st.markdown("### Experience (optional)")
        exp_list = st.session_state["rb_data"].get("experience_raw", [])
        updated_exp = []
        for i, exp in enumerate(exp_list):
            st.markdown(f"**Role {i+1}**")
            c1, c2 = st.columns(2)
            role = c1.text_input("Role", value=exp.get("role",""), key=f"er_{i}")
            company = c2.text_input("Company", value=exp.get("company",""), key=f"ec_{i}")
            duration = st.text_input("Duration", value=exp.get("duration",""), key=f"ed_{i}")
            desc = st.text_area("What did you do?", value=exp.get("desc",""), key=f"edesc_{i}")
            updated_exp.append({"role":role,"company":company,"duration":duration,"desc":desc})
            st.markdown("---")
        if st.button("Add Experience"):
            updated_exp.append({"role":"","company":"","duration":"","desc":""})
            st.session_state["rb_data"]["experience_raw"] = updated_exp
            st.session_state["rb_data"]["skills_raw"] = {"languages":languages,"frameworks":frameworks,"tools":tools,"soft":soft}
            st.rerun()
        col_back, col_next = st.columns(2)
        if col_back.button("← Back"):
            st.session_state["rb_data"]["experience_raw"] = updated_exp
            st.session_state["rb_data"]["skills_raw"] = {"languages":languages,"frameworks":frameworks,"tools":tools,"soft":soft}
            st.session_state["rb_step"] = 3
            st.rerun()
        if col_next.button("Next →", type="primary"):
            st.session_state["rb_data"]["experience_raw"] = updated_exp
            st.session_state["rb_data"]["skills_raw"] = {"languages":languages,"frameworks":frameworks,"tools":tools,"soft":soft}
            st.session_state["rb_step"] = 5
            st.rerun()

    elif step == 5:
        st.markdown("### Generate Your Resume")
        st.info("Gemini will now polish your bullet points and generate a downloadable PDF.")
        d = st.session_state["rb_data"]
        if st.button("Generate Resume PDF", type="primary"):
            with st.spinner("Gemini is writing your resume..."):
                summary_text = ""
                if d.get("summary_raw", "").strip():
                    b = polish_bullets(d["summary_raw"], "Professional Summary", client, MODEL)
                    summary_text = " ".join(b)
                polished_projects = []
                for proj in d.get("projects_raw", []):
                    if proj.get("name") and proj.get("desc"):
                        b = polish_bullets(proj["desc"], f"Project: {proj['name']}", client, MODEL)
                        polished_projects.append({"name": proj["name"], "tech": proj.get("tech",""), "bullets": b})
                polished_exp = []
                for exp in d.get("experience_raw", []):
                    if exp.get("role") and exp.get("desc"):
                        b = polish_bullets(exp["desc"], f"Role: {exp['role']}", client, MODEL)
                        polished_exp.append({"role": exp["role"], "company": exp.get("company",""), "duration": exp.get("duration",""), "bullets": b})
                sk = d.get("skills_raw", {})
                skills_dict = {}
                if sk.get("languages"): skills_dict["Languages"] = [s.strip() for s in sk["languages"].split(",") if s.strip()]
                if sk.get("frameworks"): skills_dict["Frameworks"] = [s.strip() for s in sk["frameworks"].split(",") if s.strip()]
                if sk.get("tools"): skills_dict["Tools"] = [s.strip() for s in sk["tools"].split(",") if s.strip()]
                if sk.get("soft"): skills_dict["Soft Skills"] = [s.strip() for s in sk["soft"].split(",") if s.strip()]
                final_data = {"personal": d.get("personal", {}), "summary": summary_text, "education": d.get("education", []),
                              "projects": polished_projects, "experience": polished_exp, "skills": skills_dict}
                pdf_bytes = generate_resume_pdf(final_data)
                log_activity(username, "resume_builder")
            st.success("Resume generated!")
            pname = d.get("personal",{}).get("name","resume").replace(" ","_")
            col_pdf, col_word = st.columns(2)
            with col_pdf:
                 st.download_button("📥 Download as PDF", data=pdf_bytes, file_name=f"{pname}_resume.pdf", mime="application/pdf", type="primary")
            with col_word:
                 
                 docx_bytes = generate_resume_docx(final_data)
                 st.download_button("📄 Download as Word", data=docx_bytes, file_name=f"{pname}_resume.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")
        if st.button("← Back"):
            st.session_state["rb_step"] = 4
            st.rerun()
        if st.button("Start Over"):
            for key in ["rb_step","rb_data"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()