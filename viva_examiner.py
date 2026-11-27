"""
=============================================================================
TopperGPT - Voice Mock Viva Voce (Wispr Flow × Scaler Hackathon Edition)
=============================================================================
Module: viva_examiner.py
Purpose: Delivers an interactive, oral exam (Viva Voce) simulation for Mumbai
University engineering students. Uses actual university question papers from
knowledge_base.py, asks questions one at a time with spoken audio playback,
accepts spoken or typed student answers, and grades responses out of 5 marks
with missing keyword detection, examiner trap warnings, and topper model answers.
Supports both Live AI evaluation and Zero-Key Demo Mode.
=============================================================================
"""

import os
import re
import html
import random
from typing import Dict, Any, List, Optional, Tuple

try:
    import streamlit as st
except ImportError:
    st = None

from voice_tutor import clean_text_for_speech, render_voice_player, render_microphone_widget
import demo_knowledge
from demo_knowledge import VIVA_QUESTION_BANK, evaluate_viva_answer_locally


# =============================================================================
# 1. PARSE PYQ PAPERS FROM KNOWLEDGE_BASE.PY INTO VIVA QUESTIONS
# =============================================================================
def load_all_viva_questions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses and merges genuine Mumbai University questions from knowledge_base.py
    and demo_knowledge.py into structured question pools by subject.
    """
    subject_pools: Dict[str, List[Dict[str, Any]]] = {
        "Applied Physics": [],
        "Data Structures": [],
        "Basic Electrical & Electronics": [],
        "Applied Chemistry": [],
        "Applied Mathematics 1": [],
        "Engineering Mechanics": []
    }

    # First add our rich curated questions with full rubrics
    for q in VIVA_QUESTION_BANK:
        subj = q.get("subject", "Applied Physics")
        if subj in subject_pools:
            subject_pools[subj].append(q)

    # Now dynamically extract questions from knowledge_base.py if available
    try:
        import knowledge_base
        raw_sources = []
        if hasattr(knowledge_base, "PYQ_DATA"):
            raw_sources.append(knowledge_base.PYQ_DATA)
        if hasattr(knowledge_base, "PYQ_DATA_SEM2"):
            raw_sources.append(knowledge_base.PYQ_DATA_SEM2)

        mapping = {
            "applied physics": "Applied Physics",
            "data structure": "Data Structures",
            "basic electrical electronics": "Basic Electrical & Electronics",
            "applied chemistry": "Applied Chemistry",
            "applied mathematics 1": "Applied Mathematics 1",
            "engineering mechanics": "Engineering Mechanics"
        }

        q_counter = 100
        for src in raw_sources:
            for raw_k, text in src.items():
                target_subj = mapping.get(raw_k.lower())
                if not target_subj:
                    continue

                for line in text.splitlines():
                    line = line.strip()
                    if line.startswith("-") and ("(3M)" in line or "(5M)" in line or "(6M)" in line or "(8M)" in line):
                        # Extract question text and marks
                        m_match = re.search(r'\((\d+)M\)', line)
                        marks = int(m_match.group(1)) if m_match else 5
                        cleaned_q = re.sub(r'^\s*-\s*', '', line)
                        cleaned_q = re.sub(r'\s*\(\d+M\)\s*$', '', cleaned_q).strip()

                        if len(cleaned_q) >= 15:
                            q_counter += 1
                            # Extract potential keywords from the question line
                            words = [w for w in re.findall(r'[a-zA-Z]{4,}', cleaned_q) if w.lower() not in ["find", "explain", "state", "prove", "what", "with", "from"]]
                            subject_pools[target_subj].append({
                                "id": f"kb_q_{q_counter}",
                                "subject": target_subj,
                                "question": f"Explain: {cleaned_q}",
                                "marks": min(marks, 5),
                                "keywords": words[:5],
                                "model_answer": f"Standard Mumbai University answer covering: {cleaned_q}. Requires formal definition, governing derivation, and standard schematic diagram.",
                                "examiner_trap": "Avoid writing generalized theory without stating the precise governing equation.",
                                "follow_up": f"How is this principle practically tested in university laboratory experiments?"
                            })
    except Exception as e:
        print(f"Notice: Knowledge base extraction: {e}")

    return subject_pools


# =============================================================================
# 2. AI EVALUATION HELPER (LIVE AI WITH RETRY & DEMO FALLBACK)
# =============================================================================
def evaluate_viva_answer_ai(
    generate_fn,
    question_obj: Dict[str, Any],
    student_answer: str
) -> Dict[str, Any]:
    """
    Sends the student's viva response to the live AI engine (Groq/Gemini)
    with a strict academic rubric. Falls back seamlessly to local evaluation
    if the AI is offline or API keys are missing.
    """
    prompt = f"""You are a strict, senior Mumbai University viva-voce external examiner evaluating an engineering student.

EXAM QUESTION:
"{question_obj.get('question')}"
TOTAL MARKS: 5 Marks
TARGET KEYWORDS EXPECTED: {", ".join(question_obj.get('keywords', []))}

STUDENT'S SPOKEN VIVA ANSWER:
"{student_answer}"

EVALUATION INSTRUCTIONS:
1. Award marks strictly out of 5 based on technical accuracy, use of correct engineering terminology, and depth.
2. Identify which expected keywords were MATCHED and which were MISSING.
3. Provide concise, constructive examiner feedback (2-3 sentences).
4. State an Examiner Trap Alert (what external examiners look for to cut marks).
5. State a Topper's Model Answer (3-4 crisp bullet points suitable for a 5-mark viva).
6. State one sharp Examiner Cross-Question (follow-up).

FORMAT YOUR OUTPUT EXACTLY AS:
SCORE: [X]/5
FEEDBACK: [Your feedback]
MATCHED_KEYWORDS: [keyword1, keyword2, ...]
MISSING_KEYWORDS: [keyword1, keyword2, ...]
MODEL_ANSWER: [Topper's model answer]
EXAMINER_TRAP: [Common pitfall]
FOLLOW_UP: [Follow-up question]
"""
    try:
        ai_raw = generate_fn(prompt, max_toks=800, temperature=0.2)
        if ai_raw and "SCORE:" in ai_raw:
            # Parse response
            score_m = re.search(r'SCORE:\s*(\d+)\s*/\s*5', ai_raw)
            score = int(score_m.group(1)) if score_m else 3

            feedback_m = re.search(r'FEEDBACK:\s*([\s\S]*?)(?=MATCHED_KEYWORDS:|$)', ai_raw)
            feedback = feedback_m.group(1).strip() if feedback_m else "Evaluated by AI Examiner."

            matched_m = re.search(r'MATCHED_KEYWORDS:\s*([\s\S]*?)(?=MISSING_KEYWORDS:|$)', ai_raw)
            matched_raw = matched_m.group(1).strip() if matched_m else ""
            matched = [k.strip(" []'\"") for k in matched_raw.split(",") if k.strip(" []'\"")]

            missing_m = re.search(r'MISSING_KEYWORDS:\s*([\s\S]*?)(?=MODEL_ANSWER:|$)', ai_raw)
            missing_raw = missing_m.group(1).strip() if missing_m else ""
            missing = [k.strip(" []'\"") for k in missing_raw.split(",") if k.strip(" []'\"")]

            model_m = re.search(r'MODEL_ANSWER:\s*([\s\S]*?)(?=EXAMINER_TRAP:|$)', ai_raw)
            model_ans = model_m.group(1).strip() if model_m else question_obj.get("model_answer", "")

            trap_m = re.search(r'EXAMINER_TRAP:\s*([\s\S]*?)(?=FOLLOW_UP:|$)', ai_raw)
            trap = trap_m.group(1).strip() if trap_m else question_obj.get("examiner_trap", "")

            follow_m = re.search(r'FOLLOW_UP:\s*([\s\S]*?)$', ai_raw)
            follow_up = follow_m.group(1).strip() if follow_m else question_obj.get("follow_up", "")

            return {
                "score": score,
                "max_marks": 5,
                "matched_keywords": matched,
                "missing_keywords": missing,
                "feedback": feedback,
                "model_answer": model_ans,
                "examiner_trap": trap,
                "follow_up": follow_up,
                "mode": "AI"
            }
    except Exception as e:
        print(f"Notice: AI viva evaluation fallover: {e}")

    # Fallback to local evaluation
    res = evaluate_viva_answer_locally(question_obj, student_answer)
    res["mode"] = "DEMO"
    return res


# =============================================================================
# 3. MAIN UI COMPONENT: MOCK VIVA VOCE EXAMINER
# =============================================================================
def render_viva_examiner_page(generate_response_fn, is_demo_mode: bool = False, student_name: str = "Student"):
    """
    Renders the complete Mock Viva Voce examination page.
    """
    if not st:
        return

    st.markdown("""
        <div class="topper-card" style="margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 26px;">🎯</span>
                    <div>
                        <h2 style="margin: 0; color: #58c1c8; font-size: 22px; font-weight: 800;">Mock Viva Voce Examiner</h2>
                        <p style="color: var(--text-muted, #94a3b8); font-size: 13.5px; margin: 3px 0 0 0;">
                            Oral engineering exams simulated 1-on-1. Listen to questions, answer via voice, and get graded out of 5 marks.
                        </p>
                    </div>
                </div>
                <div style="display: flex; gap: 6px; align-items: center;">
                    <span class="research-card-tag research-tag-def">MU C-SCHEME</span>
                    <span class="research-card-tag research-tag-breakdown">5-MARK RUBRIC</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Load questions pool
    if "viva_question_pools" not in st.session_state:
        st.session_state.viva_question_pools = load_all_viva_questions()

    subject_list = list(st.session_state.viva_question_pools.keys())

    # Subject Selector & Mode Bar
    col_subj, col_mode = st.columns([3, 2])
    with col_subj:
        selected_subject = st.selectbox(
            "Select Engineering Subject for Viva:",
            subject_list,
            index=0,
            key="viva_selected_subj"
        )
    with col_mode:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        is_force_demo = st.checkbox("Force Offline Demo Mode (No API keys needed)", value=is_demo_mode, key="chk_viva_demo")

    active_pool = st.session_state.viva_question_pools.get(selected_subject, [])
    if not active_pool:
        st.warning("No questions available for this subject yet.")
        return

    # Viva session states
    if "viva_q_index" not in st.session_state:
        st.session_state.viva_q_index = 0
    if "viva_curr_subject" not in st.session_state or st.session_state.viva_curr_subject != selected_subject:
        st.session_state.viva_curr_subject = selected_subject
        st.session_state.viva_q_index = 0
        st.session_state.viva_last_eval = None
        st.session_state.viva_student_ans = ""

    # Ensure index in bounds
    if st.session_state.viva_q_index >= len(active_pool):
        st.session_state.viva_q_index = 0

    current_q = active_pool[st.session_state.viva_q_index]

    # Progress Indicator
    q_num = st.session_state.viva_q_index + 1
    total_q = len(active_pool)
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 13px; font-weight: 700; color: #58c1c8; text-transform: uppercase; letter-spacing: 0.5px;">
                EXAMINER QUESTION {q_num} OF {total_q}
            </span>
            <span style="font-size: 12px; color: #64748b;">Subject: {selected_subject}</span>
        </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # EXAMINER QUESTION CARD (WITH SPOKEN AUDIO PLAYBACK)
    # -------------------------------------------------------------------------
    q_text = current_q.get("question", "")
    st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(88, 193, 200, 0.3); border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 28px; line-height: 1;">👨‍🏫</span>
                <div style="flex: 1;">
                    <div style="color: #94a3b8; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">
                        External Viva Examiner Asks:
                    </div>
                    <div style="color: #ffffff; font-size: 17px; font-weight: 700; line-height: 1.45;">
                        "{q_text}"
                    </div>
                    <div style="margin-top: 6px; display: flex; gap: 8px;">
                        <span style="background: rgba(88, 193, 200, 0.15); color: #58c1c8; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">
                            {current_q.get('marks', 5)} Marks
                        </span>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Spoken audio player for the examiner's question
    spoken_q = f"Question {q_num}: {clean_text_for_speech(q_text)}"
    st.markdown("<p style='font-size: 12px; color: #64748b; margin-bottom: 4px;'>🔊 Listen to the examiner ask this question:</p>", unsafe_allow_html=True)
    render_voice_player(spoken_q, key=f"viva_q_audio_{q_num}")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # STUDENT ANSWER INPUT (VOICE OR TYPED)
    # -------------------------------------------------------------------------
    viva_tab_voice, viva_tab_type = st.tabs(["🎙️ Speak Your Answer (Mic)", "⌨️ Type Your Answer (Manual)"])

    ans_submitted = False
    student_final_answer = ""

    with viva_tab_voice:
        st.markdown("<p style='font-size: 12px; color: #94a3b8;'>Click Start Speaking below. Explain your answer as you would in front of an external examiner:</p>", unsafe_allow_html=True)
        render_microphone_widget(form_id=f"viva_mic_{q_num}")

        # Check URL query param from JS speech recognition
        url_voice_q = st.query_params.get("voice_q", "").strip()
        if url_voice_q:
            student_final_answer = url_voice_q
            st.query_params.pop("voice_q", None)
            ans_submitted = True

    with viva_tab_type:
        with st.form(f"viva_manual_form_{q_num}"):
            manual_ans = st.text_area(
                "Your Technical Answer:",
                placeholder="State the core principle, governing formula, key conditions, and conclusion...",
                height=110,
                key=f"viva_manual_text_{q_num}"
            ).strip()
            submit_viva_btn = st.form_submit_button("Submit Answer to Examiner ⚡", use_container_width=True)
            if submit_viva_btn and manual_ans:
                student_final_answer = manual_ans
                ans_submitted = True

    # -------------------------------------------------------------------------
    # EVALUATION PROCESSING
    # -------------------------------------------------------------------------
    if ans_submitted and student_final_answer:
        st.session_state.viva_student_ans = student_final_answer
        with st.spinner("👨‍🏫 External Examiner evaluating your response against MU C-Scheme rubrics..."):
            if is_force_demo or is_demo_mode:
                eval_res = evaluate_viva_answer_locally(current_q, student_final_answer)
                eval_res["mode"] = "DEMO"
            else:
                eval_res = evaluate_viva_answer_ai(generate_response_fn, current_q, student_final_answer)

            st.session_state.viva_last_eval = eval_res

    # -------------------------------------------------------------------------
    # DISPLAY EVALUATION RESULTS & RUBRIC BREAKDOWN
    # -------------------------------------------------------------------------
    if st.session_state.get("viva_last_eval"):
        eval_data = st.session_state.viva_last_eval
        score = eval_data.get("score", 0)
        mode = eval_data.get("mode", "DEMO")

        st.markdown("---")

        # Mode Badge
        if mode == "AI":
            badge_html = '<span style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); color: #22c55e; padding: 4px 10px; border-radius: 6px; font-size: 11.5px; font-weight: 700;">🟢 LIVE AI EVALUATION (GROQ/GEMINI)</span>'
        else:
            badge_html = '<span style="background: rgba(88, 193, 200, 0.15); border: 1px solid rgba(88, 193, 200, 0.4); color: #58c1c8; padding: 4px 10px; border-radius: 6px; font-size: 11.5px; font-weight: 700;">🔵 DEMO MODE EVALUATION (OFFLINE ZERO-KEY)</span>'

        # Score Color
        score_color = "#22c55e" if score >= 4 else ("#eab308" if score >= 3 else "#ef4444")

        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <h3 style="margin: 0; color: #ffffff; font-size: 20px; font-weight: 800;">
                    📊 Viva Assessment Result
                </h3>
                {badge_html}
            </div>

            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 14px;">
                    <div style="background: rgba(0, 0, 0, 0.3); border: 2px solid {score_color}; border-radius: 12px; width: 85px; height: 85px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <span style="font-size: 28px; font-weight: 900; color: {score_color}; line-height: 1;">{score}</span>
                        <span style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">OUT OF 5</span>
                    </div>
                    <div style="flex: 1;">
                        <div style="color: #94a3b8; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 3px;">Examiner Verdict</div>
                        <div style="color: #ffffff; font-size: 15px; font-weight: 600; line-height: 1.4;">
                            {eval_data.get('feedback', '')}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Keyword Analysis Chips
        matched_kw = eval_data.get("matched_keywords", [])
        missing_kw = eval_data.get("missing_keywords", [])

        col_kw1, col_kw2 = st.columns(2)
        with col_kw1:
            st.markdown("<p style='font-size: 12px; font-weight: 700; color: #22c55e;'>✅ KEYWORDS IDENTIFIED IN YOUR ANSWER:</p>", unsafe_allow_html=True)
            if matched_kw:
                chips_m = "".join([f'<span style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.35); color: #86efac; padding: 3px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 600; display: inline-block; margin: 2px 4px 2px 0;">{html.escape(k)}</span>' for k in matched_kw])
                st.markdown(chips_m, unsafe_allow_html=True)
            else:
                st.caption("None of the essential syllabus keywords were articulated.")

        with col_kw2:
            st.markdown("<p style='font-size: 12px; font-weight: 700; color: #ef4444;'>⚠️ MISSING CONCEPTS (DEDUCTION RISK):</p>", unsafe_allow_html=True)
            if missing_kw:
                chips_miss = "".join([f'<span style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); color: #fca5a5; padding: 3px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 600; display: inline-block; margin: 2px 4px 2px 0;">{html.escape(k)}</span>' for k in missing_kw])
                st.markdown(chips_miss, unsafe_allow_html=True)
            else:
                st.caption("None! All critical syllabus keywords were covered.")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Topper's Model Answer & Spoken Feedback Player
        with st.expander("📖 View Topper's 5-Mark Model Viva Answer", expanded=True):
            model_ans = eval_data.get("model_answer", "")
            st.markdown(model_ans)
            st.markdown("<p style='font-size: 11.5px; color: #64748b; margin-top: 6px;'>🔊 Spoken audio of model answer:</p>", unsafe_allow_html=True)
            render_voice_player(model_ans, key=f"viva_model_speech_{q_num}")

        # Examiner Trap Alert
        trap_text = eval_data.get("examiner_trap", "")
        if trap_text:
            st.markdown(f"""
                <div style="background: rgba(234, 179, 8, 0.1); border-left: 4px solid #eab308; padding: 12px 16px; border-radius: 6px; margin: 12px 0;">
                    <div style="color: #fef08a; font-size: 12px; font-weight: 800; text-transform: uppercase;">⚠️ Examiner Cross-Trap Alert:</div>
                    <div style="color: #ffffff; font-size: 13.5px; margin-top: 4px;">{trap_text}</div>
                </div>
            """, unsafe_allow_html=True)

        # Follow-up Cross Question
        follow_up = eval_data.get("follow_up", "")
        if follow_up:
            st.markdown(f"""
                <div style="background: rgba(56, 189, 248, 0.08); border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 6px; margin: 12px 0;">
                    <div style="color: #7dd3fc; font-size: 12px; font-weight: 800; text-transform: uppercase;">🎯 Cross-Question Follow-up:</div>
                    <div style="color: #ffffff; font-size: 14px; font-weight: 600; margin-top: 4px;">"{follow_up}"</div>
                </div>
            """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # NAVIGATION BUTTONS: NEXT QUESTION / RANDOM QUESTION
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])

    with col_nav1:
        if st.button("⬅️ Previous Question", key="viva_prev_btn", use_container_width=True):
            if st.session_state.viva_q_index > 0:
                st.session_state.viva_q_index -= 1
            else:
                st.session_state.viva_q_index = len(active_pool) - 1
            st.session_state.viva_last_eval = None
            st.session_state.viva_student_ans = ""
            st.rerun()

    with col_nav2:
        if st.button("🎲 Random Question", key="viva_random_btn", use_container_width=True):
            st.session_state.viva_q_index = random.randint(0, len(active_pool) - 1)
            st.session_state.viva_last_eval = None
            st.session_state.viva_student_ans = ""
            st.rerun()

    with col_nav3:
        if st.button("Next Question ➡️", key="viva_next_btn", use_container_width=True):
            if st.session_state.viva_q_index < len(active_pool) - 1:
                st.session_state.viva_q_index += 1
            else:
                st.session_state.viva_q_index = 0
            st.session_state.viva_last_eval = None
            st.session_state.viva_student_ans = ""
            st.rerun()
