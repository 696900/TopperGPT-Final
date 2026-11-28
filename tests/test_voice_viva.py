import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import voice_tutor
import viva_examiner
import demo_knowledge

# 1. Test phonetic sanitization
raw_latex = r"At contact, path difference is $\Delta = 2\mu t \cos(r) + \frac{\lambda}{2}$. Since $t=0$, we get $\sqrt{x}$ and $\Omega$."
clean_speech = voice_tutor.clean_text_for_speech(raw_latex)
print("Phonetic Cleaned Speech:\n", clean_speech)
assert "backslash" not in clean_speech.lower(), "Raw backslash remains in speech!"
assert "over 2" in clean_speech, "Fraction failed to convert!"
assert "square root" in clean_speech, "Square root failed to convert!"
assert "ohms" in clean_speech, "Omega failed to convert!"

# 2. Test demo knowledge retrieval
ans = demo_knowledge.find_demo_answer("Explain Newton rings and refractive index")
assert ans is not None and "Newton" in ans, "Newton rings lookup failed!"
print("Demo Answer Lookup: PASS")

# 3. Test viva question loading
pools = viva_examiner.load_all_viva_questions()
for subj, q_list in pools.items():
    print(f"Subject [{subj}]: {len(q_list)} questions loaded")
    assert len(q_list) > 0, f"No questions for {subj}"

# 4. Test viva local evaluation
test_q = demo_knowledge.VIVA_QUESTION_BANK[0]
good_ans = "A metastable state has an excited lifetime of 10^-3 seconds allowing population inversion and stimulated emission to take place."
eval_good = demo_knowledge.evaluate_viva_answer_locally(test_q, good_ans)
print("Viva Evaluation (Good Ans): Score", eval_good["score"], "/ 5, Matched:", eval_good["matched_keywords"])
assert eval_good["score"] >= 4, f"Expected score >= 4, got {eval_good['score']}"

bad_ans = "Laser is bright light."
eval_bad = demo_knowledge.evaluate_viva_answer_locally(test_q, bad_ans)
print("Viva Evaluation (Bad Ans): Score", eval_bad["score"], "/ 5, Missing:", eval_bad["missing_keywords"])
assert eval_bad["score"] <= 2, f"Expected score <= 2, got {eval_bad['score']}"

# 5. Test zero-key fallback generator
fallback = demo_knowledge.generate_fallback_academic_response("Explain Barkhausen Criterion")
assert "Barkhausen" in fallback or "University Definition" in fallback, "Fallback generation failed!"
print("Zero-Key Fallback Generation: PASS")

# 6. Test voice widget rendering functions (mock st / components)
class MockComponents:
    def __init__(self):
        self.html_calls = []
    def html(self, html_str, height=None, scrolling=False):
        self.html_calls.append({"html": html_str, "height": height, "scrolling": scrolling})

orig_comp = voice_tutor.components
orig_fn = voice_tutor._voice_component_fn
mock_comp = MockComponents()
voice_tutor.components = mock_comp
voice_tutor._voice_component_fn = None

voice_tutor.render_voice_player("Test speech for Laser operation with $\\lambda$ wavelength", key="test_audio")
assert len(mock_comp.html_calls) == 1, "render_voice_player failed to call components.html"
assert "SPOKEN ACADEMIC EXPLANATION" in mock_comp.html_calls[0]["html"]
assert "SpeechSynthesisUtterance" in mock_comp.html_calls[0]["html"]

voice_tutor.render_microphone_widget(form_id="test_mic", submit_label="Submit Voice Doubt ⚡")
assert len(mock_comp.html_calls) == 2, "render_microphone_widget failed to call components.html"
assert "Start Speaking" in mock_comp.html_calls[1]["html"]
assert "SpeechRecognition" in mock_comp.html_calls[1]["html"]
assert "clearSpokenBtn_test_mic" in mock_comp.html_calls[1]["html"]

voice_tutor.components = orig_comp
voice_tutor._voice_component_fn = orig_fn
print("Voice Widgets (components.html): PASS")

print("\n>>> ALL STAGE 1, 2, AND 3 TESTS PASSED PERFECTLY! <<<")
