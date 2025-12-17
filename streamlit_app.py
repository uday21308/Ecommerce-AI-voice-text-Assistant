import streamlit as st
from ecommerce_llm import EcommerceLLM
import numpy as np
import soundfile as sf
from ecom_stt import speech_to_text
from ecom_tts import text_to_speech


st.set_page_config(
    page_title="Ecommerce AI Assistant",
    page_icon="🛒",
    layout="wide"
)

# --- Session state ---
if "llm" not in st.session_state:
    st.session_state.llm = EcommerceLLM()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- UI ---
st.title("🛒 Ecommerce AI Assistant")

mode = st.radio("Select mode", ["Chat", "Voice"], horizontal=True)

st.divider()

# --- Chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Mode ---
if mode == "Chat":
    user_input = st.chat_input("Type your message...")

    if user_input:
        # show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = st.session_state.llm.process(user_input)
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        # Tool panel
        with st.expander("🧠 Tool Activity (MCP-style)"):
            st.json(getattr(st.session_state.llm, "last_tool", None))

        with st.expander("📄 Retrieved Documents"):
            docs = getattr(st.session_state.llm, "last_retrieved", [])
            for d in docs:
                st.markdown(d.page_content[:500])

# --- Voice Mode ---
if mode == "Voice":
    st.info("🎙️ Click record, speak clearly, then wait for transcription.")

    audio = st.audio_input("Record your voice")

    if audio is not None:
        with st.spinner("Transcribing..."):
            # Convert audio to WAV bytes
            audio_bytes = audio.read()

            transcript = speech_to_text(audio_bytes)

        if not transcript:
            st.error("Could not understand audio. Please try again.")
        else:
            # Show transcript
            st.session_state.messages.append(
                {"role": "user", "content": transcript}
            )
            with st.chat_message("user"):
                st.markdown(transcript)

            # LLM response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = st.session_state.llm.process(transcript)
                    st.markdown(reply)
                    reply = st.session_state.llm.process(transcript)
                    st.markdown(reply)

                    # 🔊 Speak reply
                    try:
                        ssml = getattr(st.session_state.llm, "last_ssml", None) or reply
                        audio_bytes = text_to_speech(ssml)
                        st.audio(audio_bytes, format="audio/wav")
                    except Exception:
                        st.warning("Voice output unavailable.")


            st.session_state.messages.append(
                {"role": "assistant", "content": reply}
            )

            # Tool visibility
            with st.expander("🧠 Tool Activity (MCP-style)"):
                st.json(getattr(st.session_state.llm, "last_tool", None))

            with st.expander("📄 Retrieved Documents"):
                docs = getattr(st.session_state.llm, "last_retrieved", [])
                for d in docs:
                    st.markdown(d.page_content[:500])

