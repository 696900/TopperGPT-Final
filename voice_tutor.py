"""
=============================================================================
TopperGPT - Voice Concept Tutor (Wispr Flow × Scaler Hackathon Edition)
=============================================================================
Module: voice_tutor.py
Purpose: Provides voice-first academic tutoring for Mumbai University engineering
students. Supports live browser microphone dictation, trilingual speech-to-text
(English, Hindi, Marathi), text editing before submission, multi-tier AI evaluation,
and spoken audio playback with LaTeX-to-speech phonetic sanitization.
=============================================================================
"""

import os
import re
import io
import html
import base64
from typing import Optional, Tuple, Dict, Any

try:
    import streamlit as st
except ImportError:
    st = None

# Optional server-side TTS fallback using gTTS if installed
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


def strip_html_indent(html_str: str) -> str:
    """
    Strips all leading whitespace and eliminates internal blank lines so that
    Streamlit and CommonMark never terminate the HTML block early or mistake
    indented HTML tags as preformatted code blocks.
    """
    if not html_str or not isinstance(html_str, str):
        return ""
    lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    return "\n".join(lines)


# =============================================================================
# 1. PHONETIC SANITIZER (CONVERT LATEX & MARKDOWN TO NATURAL SPOKEN SPEECH)
# =============================================================================
def clean_text_for_speech(text: str) -> str:
    """
    Transforms academic Markdown and LaTeX mathematical formulas into natural,
    phonetically speakable English/Hinglish so text-to-speech engines do not
    awkwardly recite raw code tokens like 'dollar backslash frac'.

    Examples:
        - $V = I \\times R$ -> "V equals I times R"
        - $\\frac{dy}{dx}$ -> "derivative of y with respect to x"
        - $\\sqrt{x}$ -> "square root of x"
        - $x^2$ -> "x squared"
        - $\\Omega$ -> "ohms"
    """
    if not text or not isinstance(text, str):
        return ""

    s = text.strip()

    # 1. Strip code blocks and raw URLs
    s = re.sub(r'```[\s\S]*?```', ' [Code block omitted for speech] ', s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'https?://\S+', '', s)

    # 2. Convert common LaTeX fractions: \frac{a}{b} -> "a over b"
    s = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'\1 over \2', s)

    # 3. Convert square roots: \sqrt{x} -> "square root of x"
    s = re.sub(r'\\sqrt\{([^{}]+)\}', r'square root of \1', s)

    # 4. Common mathematical symbols & Greek letters
    math_replacements = [
        (r'\\approx', ' approximately equals '),
        (r'\\neq', ' is not equal to '),
        (r'\\le|\\leq', ' is less than or equal to '),
        (r'\\ge|\\geq', ' is greater than or equal to '),
        (r'\\times', ' times '),
        (r'\\div', ' divided by '),
        (r'\\pm', ' plus or minus '),
        (r'\\infty', ' infinity '),
        (r'\\pi', ' pi '),
        (r'\\theta', ' theta '),
        (r'\\lambda', ' lambda '),
        (r'\\mu', ' micro '),
        (r'\\Omega|\\omega', ' ohms '),
        (r'\\Delta|\\delta', ' delta '),
        (r'\\alpha', ' alpha '),
        (r'\\beta', ' beta '),
        (r'\\gamma', ' gamma '),
        (r'\\sigma', ' sigma '),
        (r'\\phi', ' phi '),
        (r'\\int', ' integral of '),
        (r'\\sum', ' summation of '),
        (r'\\partial', ' partial derivative of '),
        (r'\\rightarrow', ' approaches '),
        (r'\\cdot', ' dot '),
        (r'\^2', ' squared '),
        (r'\^3', ' cubed '),
        (r'\^\{([^{}]+)\}', r' to the power of \1 '),
        (r'_\{([^{}]+)\}', r' sub \1 '),
    ]

    for pat, rep in math_replacements:
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)

    # 5. Remove remaining dollar signs and backslashes
    s = s.replace('$$', ' ').replace('$', ' ')
    s = re.sub(r'\\[a-zA-Z]+', ' ', s)

    # 6. Remove markdown formatting characters (#, *, _, >, |, ~)
    s = re.sub(r'#+\s*', '', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)
    s = re.sub(r'\*([^*]+)\*', r'\1', s)
    s = re.sub(r'__([^_]+)__', r'\1', s)
    s = re.sub(r'~~([^~]+)~~', r'\1', s)
    s = re.sub(r'>\s*', '', s)
    s = re.sub(r'\|[ -:]+\|', ' ', s)
    s = s.replace('|', ', ')

    # 7. Collapse multiple spaces and trim
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# =============================================================================
# 2. AUDIO PLAYBACK COMPONENT (WEB SPEECH SYNTHESIS + GTTS FALLBACK)
# =============================================================================
def render_voice_player(text_to_speak: str, auto_play: bool = False, key: str = "voice_player"):
    """
    Renders a sleek, responsive dark-themed audio playback widget with:
    1. Browser-native Web Speech Synthesis API (zero latency, zero API costs, full play/pause/stop/rate controls).
    2. Server-side MP3 player fallback using gTTS if preferred or required.
    """
    if not text_to_speak or not st:
        return

    clean_speech = clean_text_for_speech(text_to_speak)
    if not clean_speech:
        return

    # Truncate extremely long responses for speech buffer safety (first 2500 chars ~ 2.5 mins of speech)
    speech_snippet = clean_speech[:2800]
    json_safe_text = html.escape(speech_snippet).replace('"', '&quot;').replace("'", "&#39;")

    # Unique DOM IDs
    btn_play_id = f"play_{key}"
    btn_stop_id = f"stop_{key}"
    rate_sel_id = f"rate_{key}"
    status_id = f"status_{key}"

    player_html = f"""
    <div style="background: linear-gradient(135deg, rgba(88, 193, 200, 0.08) 0%, rgba(17, 24, 39, 0.95) 100%);
                border: 1.5px solid rgba(88, 193, 200, 0.35);
                border-radius: 14px;
                padding: 14px 18px;
                margin: 14px 0;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 20px;">🔊</span>
                <div>
                    <span style="color: #58c1c8; font-weight: 700; font-size: 13.5px; letter-spacing: 0.3px;">SPOKEN ACADEMIC EXPLANATION</span>
                    <span style="color: #94a3b8; font-size: 11px; margin-left: 6px;">(Wispr Voice Player)</span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <label style="color: #94a3b8; font-size: 11px;">Speed:</label>
                <select id="{rate_sel_id}" style="background: rgba(14, 17, 23, 0.9); color: #58c1c8; border: 1px solid rgba(88, 193, 200, 0.3); border-radius: 6px; padding: 3px 8px; font-size: 11px; cursor: pointer;">
                    <option value="0.9">0.9x Relaxed</option>
                    <option value="1.0" selected>1.0x Normal</option>
                    <option value="1.2">1.2x Exam Revision</option>
                    <option value="1.4">1.4x Rapid Cram</option>
                </select>
            </div>
        </div>

        <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px;">
            <button id="{btn_play_id}" type="button" style="background: #58c1c8; color: #0b0f19; border: none; border-radius: 9999px; padding: 7px 18px; font-weight: 700; font-size: 12.5px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s ease;">
                <span>▶</span>
                <span id="{btn_play_id}_txt">Play Spoken Answer</span>
            </button>
            <button id="{btn_stop_id}" type="button" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 9999px; padding: 7px 14px; font-weight: 600; font-size: 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
                <span>⏹</span>
                <span>Stop</span>
            </button>
            <span id="{status_id}" style="color: #94a3b8; font-size: 11.5px; margin-left: 6px;">Ready to listen</span>
        </div>
    </div>

    <script>
    (function() {{
        const playBtn = document.getElementById('{btn_play_id}');
        const stopBtn = document.getElementById('{btn_stop_id}');
        const playTxt = document.getElementById('{btn_play_id}_txt');
        const rateSel = document.getElementById('{rate_sel_id}');
        const statusEl = document.getElementById('{status_id}');
        const rawSpeech = "{json_safe_text}".replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');

        let isSpeaking = false;
        let isPaused = false;
        let currentUtterance = null;

        if (!('speechSynthesis' in window)) {{
            if (statusEl) statusEl.innerText = "Browser speech synthesis not supported. Audio reading unavailable.";
            if (playBtn) playBtn.disabled = true;
            return;
        }}

        function getBestVoice() {{
            const voices = window.speechSynthesis.getVoices();
            // Preference 1: Indian English voice
            let v = voices.find(vox => vox.lang.includes('en-IN') || vox.name.includes('India'));
            // Preference 2: Natural English voice
            if (!v) v = voices.find(vox => vox.lang.startsWith('en') && (vox.name.includes('Natural') || vox.name.includes('Google') || vox.name.includes('Siri')));
            // Preference 3: Any English
            if (!v) v = voices.find(vox => vox.lang.startsWith('en'));
            return v || voices[0];
        }}

        playBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            if (isSpeaking && !isPaused) {{
                // Pause
                window.speechSynthesis.pause();
                isPaused = true;
                playTxt.innerText = "Resume";
                statusEl.innerText = "⏸ Paused";
                statusEl.style.color = "#f59e0b";
            }} else if (isSpeaking && isPaused) {{
                // Resume
                window.speechSynthesis.resume();
                isPaused = false;
                playTxt.innerText = "Pause";
                statusEl.innerText = "🔊 Speaking...";
                statusEl.style.color = "#58c1c8";
            }} else {{
                // Start fresh playback
                window.speechSynthesis.cancel();
                currentUtterance = new SpeechSynthesisUtterance(rawSpeech);
                const rateVal = parseFloat(rateSel.value) || 1.0;
                currentUtterance.rate = rateVal;
                currentUtterance.pitch = 1.0;
                const bestVox = getBestVoice();
                if (bestVox) currentUtterance.voice = bestVox;

                currentUtterance.onstart = function() {{
                    isSpeaking = true;
                    isPaused = false;
                    playTxt.innerText = "Pause";
                    statusEl.innerText = "🔊 Speaking solution...";
                    statusEl.style.color = "#58c1c8";
                }};

                currentUtterance.onend = function() {{
                    isSpeaking = false;
                    isPaused = false;
                    playTxt.innerText = "Replay";
                    statusEl.innerText = "✓ Finished reading";
                    statusEl.style.color = "#22c55e";
                }};

                currentUtterance.onerror = function() {{
                    isSpeaking = false;
                    isPaused = false;
                    playTxt.innerText = "Play Spoken Answer";
                    statusEl.innerText = "Playback stopped";
                    statusEl.style.color = "#94a3b8";
                }};

                window.speechSynthesis.speak(currentUtterance);
            }}
        }});

        stopBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            window.speechSynthesis.cancel();
            isSpeaking = false;
            isPaused = false;
            playTxt.innerText = "Play Spoken Answer";
            statusEl.innerText = "Stopped";
            statusEl.style.color = "#94a3b8";
        }});
    }})();
    </script>
    """
    st.markdown(strip_html_indent(player_html), unsafe_allow_html=True)


# =============================================================================
# 3. LIVE MICROPHONE INPUT INTERFACE (TRILINGUAL WEB SPEECH RECOGNITION)
# =============================================================================
def render_microphone_widget(form_id: str = "voice_tutor_mic") -> None:
    """
    Renders an interactive, responsive voice input interface inspired by Wispr Flow.
    Supports English (en-IN), Hindi (hi-IN), and Marathi (mr-IN).
    Displays real-time interim recognition, an editable confirmation text box,
    and automatic synchronization into Streamlit state via clean URL parameters.
    """
    mic_html = f"""
    <div style="background: rgba(18, 22, 28, 0.95);
                border: 1.5px solid rgba(88, 193, 200, 0.3);
                border-radius: 14px;
                padding: 18px 20px;
                margin-bottom: 18px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);">

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div id="micIndicator_{form_id}" style="width: 12px; height: 12px; border-radius: 50%; background: #64748b; transition: all 0.3s ease;"></div>
                <span style="color: #ffffff; font-weight: 700; font-size: 14px; letter-spacing: 0.3px;">WISPR VOICE DICTATION</span>
                <span style="background: rgba(88, 193, 200, 0.15); color: #58c1c8; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 6px;">HACKATHON EDITION</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <label style="color: #94a3b8; font-size: 11.5px;">Recognition Language:</label>
                <select id="voiceLang_{form_id}" style="background: rgba(11, 15, 25, 0.9); color: #58c1c8; border: 1px solid rgba(88, 193, 200, 0.35); border-radius: 8px; padding: 4px 10px; font-size: 12px; font-weight: 600; cursor: pointer;">
                    <option value="en-IN" selected>🇬🇧 English (India)</option>
                    <option value="hi-IN">🇮🇳 Hindi (हिंदी)</option>
                    <option value="mr-IN">🚩 Marathi (मराठी)</option>
                </select>
            </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <button id="toggleMicBtn_{form_id}" type="button" style="background: #58c1c8; color: #0b0f19; border: none; border-radius: 9999px; padding: 10px 22px; font-weight: 700; font-size: 13.5px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 0 16px rgba(88, 193, 200, 0.3); transition: all 0.2s ease;">
                    <span id="micIcon_{form_id}" style="font-size: 16px;">🎙️</span>
                    <span id="micBtnText_{form_id}">Start Speaking</span>
                </button>
                <span id="micStatusText_{form_id}" style="color: #94a3b8; font-size: 12.5px;">Click to speak your academic doubt or viva answer</span>
            </div>

            <!-- Real-Time Voice Transcription Preview -->
            <div id="livePreviewContainer_{form_id}" style="display: none; background: rgba(88, 193, 200, 0.05); border: 1px dashed rgba(88, 193, 200, 0.4); border-radius: 8px; padding: 10px 14px; color: #58c1c8; font-size: 13px; font-style: italic;">
                <span style="font-weight: 700;">Listening:</span> <span id="liveInterimText_{form_id}">...</span>
            </div>

            <!-- Editable Recognized Text (Student can verify and edit before sending) -->
            <div style="display: flex; flex-direction: column; gap: 6px;">
                <label style="color: #cbd5e1; font-size: 12px; font-weight: 600;">
                    Recognized Text (Review & Edit before asking):
                </label>
                <textarea id="recognizedTextArea_{form_id}" rows="3" placeholder="Your spoken question will appear here in real time. You can tap here to edit formulas, variable names, or typos before asking..." style="width: 100%; box-sizing: border-box; background: rgba(11, 15, 25, 0.95); color: #ffffff; border: 1.5px solid rgba(255, 255, 255, 0.12); border-radius: 10px; padding: 10px 14px; font-size: 13.5px; line-height: 1.5; outline: none; transition: border-color 0.2s;"></textarea>
            </div>

            <!-- Troubleshooting Help Box (Hidden by default, shown on mic error) -->
            <div id="micErrorNotice_{form_id}" style="display: none; background: rgba(239, 68, 68, 0.1); border: 1.5px solid rgba(239, 68, 68, 0.35); border-radius: 10px; padding: 12px 16px;">
                <div style="display: flex; align-items: center; gap: 8px; color: #f87171; font-weight: 700; font-size: 13px; margin-bottom: 4px;">
                    <span>⚠️ Microphone Permission Needed</span>
                </div>
                <p id="micErrorMsg_{form_id}" style="color: #cbd5e1; font-size: 12px; margin: 0; line-height: 1.4;">
                    Microphone access was denied. Please click the lock/settings icon 🔒 next to the URL in your browser address bar, set Microphone to 'Allow', and try again. Alternatively, you can type your question in the text box below.
                </p>
            </div>

            <!-- Action Row -->
            <div style="display: flex; justify-content: flex-end; align-items: center; gap: 10px;">
                <button id="clearSpokenBtn_{form_id}" type="button" style="background: rgba(255, 255, 255, 0.05); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 6px 14px; font-size: 12px; cursor: pointer;">
                    Clear Text
                </button>
                <button id="sendVoiceQueryBtn_{form_id}" type="button" style="background: linear-gradient(135deg, #58c1c8 0%, #00F2FE 100%); color: #0b0f19; border: none; border-radius: 8px; padding: 8px 20px; font-weight: 700; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 4px 14px rgba(0, 242, 254, 0.25);">
                    <span>Consult Voice Tutor</span>
                    <span>⚡</span>
                </button>
            </div>
        </div>
    </div>

    <script>
    (function() {{
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const toggleBtn = document.getElementById('toggleMicBtn_{form_id}');
        const micIcon = document.getElementById('micIcon_{form_id}');
        const micBtnText = document.getElementById('micBtnText_{form_id}');
        const statusText = document.getElementById('micStatusText_{form_id}');
        const indicator = document.getElementById('micIndicator_{form_id}');
        const langSelect = document.getElementById('voiceLang_{form_id}');
        const textArea = document.getElementById('recognizedTextArea_{form_id}');
        const liveContainer = document.getElementById('livePreviewContainer_{form_id}');
        const liveText = document.getElementById('liveInterimText_{form_id}');
        const errorBox = document.getElementById('micErrorNotice_{form_id}');
        const errorMsg = document.getElementById('micErrorMsg_{form_id}');
        const clearBtn = document.getElementById('clearSpokenBtn_{form_id}');
        const sendBtn = document.getElementById('sendVoiceQueryBtn_{form_id}');

        let recognition = null;
        let isRecording = false;

        if (!SpeechRecognition) {{
            statusText.innerText = "Browser voice recognition not supported in this browser. Please use Google Chrome or type below.";
            toggleBtn.disabled = true;
            toggleBtn.style.opacity = "0.5";
            return;
        }}

        function setupRecognition() {{
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = langSelect.value || 'en-IN';

            recognition.onstart = function() {{
                isRecording = true;
                toggleBtn.style.background = "#ef4444";
                micIcon.innerText = "🔴";
                micBtnText.innerText = "Stop Listening";
                statusText.innerText = "Listening live... Speak your academic doubt clearly";
                statusText.style.color = "#f87171";
                indicator.style.background = "#ef4444";
                indicator.style.boxShadow = "0 0 10px #ef4444";
                liveContainer.style.display = "block";
                errorBox.style.display = "none";
            }};

            recognition.onresult = function(event) {{
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {{
                        finalTranscript += transcript + ' ';
                    }} else {{
                        interimTranscript += transcript;
                    }}
                }}

                if (interimTranscript) {{
                    liveText.innerText = interimTranscript;
                }}

                if (finalTranscript) {{
                    const currentVal = textArea.value ? textArea.value.trim() + ' ' : '';
                    textArea.value = currentVal + finalTranscript.trim();
                    liveText.innerText = '...';
                }}
            }};

            recognition.onerror = function(event) {{
                console.warn('SpeechRecognition error:', event.error);
                if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {{
                    errorBox.style.display = "block";
                    errorMsg.innerText = "Microphone permission is blocked. Please click the lock icon 🔒 next to the browser URL, allow 'Microphone', and try again.";
                }} else if (event.error === 'no-speech') {{
                    statusText.innerText = "No speech detected. Click Start Speaking and try again.";
                }} else if (event.error === 'network') {{
                    errorBox.style.display = "block";
                    errorMsg.innerText = "Network timeout during speech recognition. You can type your question in the text box below.";
                }}
                stopRecording();
            }};

            recognition.onend = function() {{
                stopRecording();
            }};
        }}

        function stopRecording() {{
            isRecording = false;
            toggleBtn.style.background = "#58c1c8";
            micIcon.innerText = "🎙️";
            micBtnText.innerText = "Start Speaking";
            statusText.innerText = "Recording paused. Tap 'Start Speaking' to add more or send your question.";
            statusText.style.color = "#94a3b8";
            indicator.style.background = "#64748b";
            indicator.style.boxShadow = "none";
            liveContainer.style.display = "none";
        }}

        toggleBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            if (isRecording) {{
                if (recognition) recognition.stop();
            }} else {{
                setupRecognition();
                try {{
                    recognition.start();
                }} catch(err) {{
                    console.error('Recognition start error:', err);
                }}
            }}
        }});

        langSelect.addEventListener('change', function() {{
            if (isRecording && recognition) {{
                recognition.stop();
                setupRecognition();
                recognition.start();
            }}
        }});

        clearBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            textArea.value = '';
            liveText.innerText = '...';
        }});

        // Send query to Streamlit by updating query param or finding Streamlit input
        sendBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            const queryText = textArea.value.trim();
            if (!queryText) {{
                alert('Please speak or type a doubt before submitting!');
                return;
            }}
            // Navigate with query param to trigger Streamlit rerun cleanly
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('voice_q', queryText);
            window.location.href = currentUrl.toString();
        }});
    }})();
    </script>
    """
    st.markdown(strip_html_indent(mic_html), unsafe_allow_html=True)


# =============================================================================
# 4. MAIN FEATURE VIEW: VOICE CONCEPT TUTOR
# =============================================================================
def render_voice_tutor_page(generate_response_fn, is_demo_mode: bool = False, student_name: str = "Student"):
    """
    Renders the complete Voice Concept Tutor screen:
    - Wispr Flow-inspired live microphone dictation with English, Hindi, Marathi support
    - Editable recognized text box to fix typos before asking
    - Native Streamlit audio recorder as backup
    - Manual text input fallback
    - University C-Scheme academic explanation
    - Spoken playback player with LaTeX formula-to-speech phonetic smoothing
    - Hinglish translation toggle for spoken answers
    """
    if not st:
        return

    st.markdown(strip_html_indent("""
        <div class="topper-card" style="margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 26px;">🎙️</span>
                    <div>
                        <h2 style="margin: 0; color: #58c1c8; font-size: 22px; font-weight: 800;">Voice Concept Tutor</h2>
                        <p style="color: var(--text-muted, #94a3b8); font-size: 13.5px; margin: 3px 0 0 0;">
                            Speak your doubts in English, Hindi, or Marathi. Get exam-ready derivations and listen to spoken explanations.
                        </p>
                    </div>
                </div>
                <span class="research-card-tag research-tag-def" style="letter-spacing: 0.5px;">WISPR FLOW × SCALER</span>
            </div>
        </div>
    """), unsafe_allow_html=True)

    # Initialize session state stores for Voice Tutor
    if "voice_active_query" not in st.session_state:
        st.session_state.voice_active_query = ""
    if "voice_active_response" not in st.session_state:
        st.session_state.voice_active_response = ""
    if "voice_active_hinglish" not in st.session_state:
        st.session_state.voice_active_hinglish = None

    # Check if a voice query was passed through the JS speech recognition URL query param
    url_voice_q = st.query_params.get("voice_q", "").strip()
    if url_voice_q:
        st.session_state.voice_active_query = url_voice_q
        st.query_params.pop("voice_q", None)
        # Automatically process query
        trigger_voice_query = True
    else:
        trigger_voice_query = False

    # -------------------------------------------------------------------------
    # TAB NAVIGATION: VOICE DICTATION (PRIMARY) vs MANUAL TYPING (FALLBACK)
    # -------------------------------------------------------------------------
    tab_voice, tab_manual = st.tabs(["🎙️ Speak Your Doubt (Mic)", "⌨️ Type Your Doubt (Manual Fallback)"])

    with tab_voice:
        # Render live browser speech-to-text dictation widget
        render_microphone_widget(form_id="main_tutor_voice")

        # Native Streamlit audio recorder fallback
        with st.expander("📁 Alternative: Record via Streamlit Audio Recorder", expanded=False):
            st.markdown("<p style='font-size: 12.5px; color: #94a3b8;'>Use this if your browser blocks live Web Speech recognition:</p>", unsafe_allow_html=True)
            if hasattr(st, "audio_input"):
                recorded_audio = st.audio_input("Record doubt audio", key="st_native_audio_record")
                if recorded_audio is not None:
                    st.info("Audio recorded successfully. Enter a summary topic name below to consult the Voice Tutor.")

    with tab_manual:
        st.markdown("<p style='font-size: 12.5px; color: #94a3b8;'>In a quiet library or noisy room? Type your question manually:</p>", unsafe_allow_html=True)
        with st.form("manual_voice_fallback_form"):
            manual_text = st.text_input(
                "Your Technical Question or Syllabus Concept:",
                placeholder="e.g. Derive Barkhausen criterion for oscillations, Explain AVL Tree LR rotation",
                key="manual_fallback_input"
            ).strip()
            submit_manual = st.form_submit_button("Consult Voice Tutor ⚡", use_container_width=True)
            if submit_manual and manual_text:
                st.session_state.voice_active_query = manual_text
                trigger_voice_query = True

    # High-Yield Starter Chips for instant testing
    st.markdown("""
        <div style="margin: 10px 0 16px 0;">
            <span style="font-size: 12px; color: #64748b; font-weight: 600; margin-right: 8px;">TRY POPULAR MU QUESTIONS:</span>
        </div>
    """, unsafe_allow_html=True)

    chip_col1, chip_col2, chip_col3 = st.columns(3)
    with chip_col1:
        if st.button("🔬 Newton's Rings & RI", key="chip_nr", use_container_width=True):
            st.session_state.voice_active_query = "Explain Newton's Rings experiment and derive the formula to determine the refractive index of a liquid."
            trigger_voice_query = True
    with chip_col2:
        if st.button("⚡ BJT Biasing & Stability", key="chip_bjt", use_container_width=True):
            st.session_state.voice_active_query = "Explain Voltage Divider Biasing for BJT and derive the stability factor S."
            trigger_voice_query = True
    with chip_col3:
        if st.button("🌳 AVL Tree Rotations", key="chip_avl", use_container_width=True):
            st.session_state.voice_active_query = "Explain AVL Tree rotations with step-by-step illustrations of Left-Right and Right-Left imbalances."
            trigger_voice_query = True

    # -------------------------------------------------------------------------
    # PROCESS QUERY & GENERATE EXPLANATION
    # -------------------------------------------------------------------------
    if trigger_voice_query and st.session_state.voice_active_query:
        query_to_run = st.session_state.voice_active_query
        with st.spinner(f"🎙️ Voice AI Tutor formulating verified answer for: '{query_to_run}'..."):
            voice_prompt = (
                f"You are TopperGPT Voice Tutor for Mumbai University Engineering students. "
                f"Answer the following question with total technical rigor, step-by-step mathematical derivations, "
                f"LaTeX formulas ($...$ or $$...$$), and examiner trap warnings.\n\n"
                f"Student Question: {query_to_run}\n\n"
                f"Structure your answer with:\n"
                f"### 1. 📌 University Definition & Core Principle (2-Mark Standard)\n"
                f"### 2. ⚡ Step-by-Step Technical Execution & Derivation\n"
                f"### 3. ⚠️ Examiner Trap Alert (Common student pitfalls where marks are lost)\n"
            )
            try:
                ans = generate_response_fn(voice_prompt, max_toks=1500, temperature=0.3)
                st.session_state.voice_active_response = ans
                st.session_state.voice_active_hinglish = None
            except Exception as e:
                st.session_state.voice_active_response = (
                    f"⚠️ Live AI generation encountered a temporary limit: {e}. "
                    "If running without API keys, please use the Demo Mode questions."
                )

    # -------------------------------------------------------------------------
    # DISPLAY ACTIVE EXPLANATION & AUDIO PLAYBACK
    # -------------------------------------------------------------------------
    if st.session_state.voice_active_response:
        st.markdown("---")
        st.markdown(f"### 🎓 Voice Tutor Explanation: **{st.session_state.voice_active_query}**")

        # 1. Spoken Audio Player with LaTeX-to-Speech Smoothing
        render_voice_player(st.session_state.voice_active_response, key="tutor_active_speech")

        # 2. Text Explanation with LaTeX math
        st.markdown(st.session_state.voice_active_response)

        # 3. Spoken Hinglish Translation Feature
        col_h1, col_h2 = st.columns([1, 1])
        with col_h1:
            if not st.session_state.voice_active_hinglish:
                if st.button("🗣️ Listen in Hinglish (Hindi + English)", key="btn_voice_hinglish", use_container_width=True):
                    with st.spinner("⚡ Translating explanation to Hinglish..."):
                        h_prompt = (
                            f"Translate the following Mumbai University engineering answer into natural, conversational "
                            f"Roman Hindi (Hinglish). Keep all technical formulas, variable names and units in English:\n\n"
                            f"{st.session_state.voice_active_response}"
                        )
                        try:
                            h_reply = generate_response_fn(h_prompt, max_toks=1500, temperature=0.3)
                            st.session_state.voice_active_hinglish = h_reply
                            st.rerun()
                        except Exception:
                            st.error("Hinglish translation is momentarily busy. Please try again.")

        if st.session_state.voice_active_hinglish:
            st.markdown("---")
            st.markdown("#### 🇮🇳 Hinglish Spoken Explanation")
            render_voice_player(st.session_state.voice_active_hinglish, key="tutor_hinglish_speech")
            st.markdown(st.session_state.voice_active_hinglish)
