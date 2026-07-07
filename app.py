"""
app.py
Streamlit UI for the Language Detection & Translation Pipeline.

Run with:
    streamlit run app.py
"""

import os
import io
import streamlit as st

from preprocess import clean_text, is_effectively_empty
from detect import detect_language, detect_mixed_language, LANGUAGE_NAMES
from translate import get_backend, TranslationError
import database as db

st.set_page_config(page_title="Language Detection & Translation Pipeline", page_icon="🌍", layout="centered")

os.makedirs("data", exist_ok=True)
db.init_db()

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #14182280 100%);
    }
    h1 {
        background: linear-gradient(90deg, #A78BFA, #7C5CFC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    div[data-testid="stMetric"] {
        background-color: #1B1F2A;
        border: 1px solid #2A2F3D;
        border-radius: 10px;
        padding: 12px;
    }
    .stButton > button {
        background-color: #7C5CFC;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #6A4CE0;
        color: white;
    }
    div[data-testid="stExpander"] {
        background-color: #1B1F2A;
        border-radius: 8px;
        border: 1px solid #2A2F3D;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌍 Language Detection & Translation Pipeline")
st.caption("Detects the language of your text, then translates it into the language you choose.")

# --- Sidebar: backend + target language selection ---------------------------
with st.sidebar:
    st.header("Settings")

    target_lang_code = st.selectbox(
        "Translate into",
        options=list(LANGUAGE_NAMES.keys()),
        format_func=lambda c: f"{LANGUAGE_NAMES[c]} ({c})",
        index=list(LANGUAGE_NAMES.keys()).index("en"),
    )

    st.divider()
    if st.button("🗑️ Clear history"):
        db.clear_history()
        st.success("History cleared.")

# --- Main input ---------------------------------------------------------------
text_input = st.text_area("Enter text to detect & translate", height=160,
                           placeholder="Type or paste text in any language...")

check_mixed = st.checkbox("Also check for mixed-language / code-switching", value=False)

if st.button("Translate", type="primary"):
    cleaned = clean_text(text_input)

    if is_effectively_empty(cleaned):
        st.warning("Please enter some text first.")
    else:
        detection = detect_language(cleaned)

        if detection is None:
            st.error("Couldn't confidently detect a language for this text. Try entering more text.")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Detected language", f"{detection['name']} ({detection['code']})")
            col2.metric("Confidence", f"{detection['confidence'] * 100:.1f}%")

            if check_mixed:
                segments = detect_mixed_language(cleaned)
                distinct_langs = {s["code"] for s in segments}
                if len(distinct_langs) > 1:
                    st.info("⚠️ This text looks like it mixes multiple languages:")
                    for s in segments:
                        st.write(f"- **{s['name']}** ({s['confidence']*100:.0f}%): {s['segment']}")

            backend = get_backend()
            try:
                with st.spinner("Translating..."):
                    translated = backend.translate(cleaned, detection["code"], target_lang_code)

                st.subheader("Translation")
                st.text_area("Original", cleaned, height=100, disabled=True, key="orig_display")
                st.text_area("Translated", translated, height=100, disabled=True, key="trans_display")

                db.save_translation(
                    original_text=cleaned,
                    detected_lang=detection["code"],
                    detected_confidence=detection["confidence"],
                    target_lang=target_lang_code,
                    translated_text=translated,
                    backend="google",
                )

                # --- Export options ---
                st.download_button(
                    "⬇️ Download as TXT",
                    data=f"Original ({detection['name']}):\n{cleaned}\n\nTranslated ({LANGUAGE_NAMES.get(target_lang_code, target_lang_code)}):\n{translated}",
                    file_name="translation.txt",
                    mime="text/plain",
                )

                try:
                    from fpdf import FPDF

                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Helvetica", size=12)
                    pdf.multi_cell(0, 8, f"Original ({detection['name']}):\n{cleaned}\n")
                    pdf.ln(4)
                    pdf.multi_cell(0, 8, f"Translated ({LANGUAGE_NAMES.get(target_lang_code, target_lang_code)}):\n{translated}")
                    pdf_bytes = bytes(pdf.output(dest="S"))

                    st.download_button(
                        "⬇️ Download as PDF",
                        data=pdf_bytes,
                        file_name="translation.pdf",
                        mime="application/pdf",
                    )
                except Exception:
                    st.caption("(PDF export needs non-Latin fonts for some scripts; TXT export always works.)")

            except TranslationError as e:
                st.error(f"Translation failed: {e}")

# --- History -------------------------------------------------------------
st.divider()
st.subheader("📜 Translation history")
history = db.get_history()
if not history:
    st.caption("No translations yet.")
else:
    for row in history:
        with st.expander(f"{row['detected_lang']} → {row['target_lang']}  |  {row['created_at']}"):
            st.write("**Original:**", row["original_text"])
            st.write("**Translated:**", row["translated_text"])
            st.caption(f"Backend: {row['backend']} · Confidence: {row['detected_confidence']}")
