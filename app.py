"""
YouTube Video Summarizer & Interactive Q&A
Built with Streamlit + Gemini Interactions API
"""

import os
import re
from urllib.parse import urlparse, parse_qs

import streamlit as st
from dotenv import load_dotenv
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

# Upgraded to the latest Gemini Flash model as per Interactions API guidelines
GEMINI_MODEL = "gemini-3.7-flash"

SUMMARY_PROMPT = """\
You are an expert content analyst. Given the transcript of a YouTube video, \
produce a structured summary in **exactly** this format:

## Executive Overview
Provide 2-3 concise sentences capturing the video's core message and purpose.

## Key Takeaways
- **Takeaway 1**: …
- **Takeaway 2**: …
- **Takeaway 3**: …
- **Takeaway 4**: …
- **Takeaway 5**: …

## Notable Quotes & Timestamps
List any memorable or impactful quotes from the transcript. If approximate \
timestamps are available in the transcript data, include them in \
`[MM:SS]` format. If none are clearly identifiable, write \
"No notable quotes with timestamps detected."

---
Transcript:
{transcript}
"""

QA_SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions **strictly** based on the \
YouTube video transcript provided below. If the answer is not in the transcript, \
say "I couldn't find information about that in the video transcript."

Transcript:
{transcript}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def extract_video_id(url: str) -> str | None:
    """Extract a YouTube video ID from standard or shortened URLs."""
    url = url.strip()
    if not url:
        return None

    # Direct video ID (11 chars, alphanumeric + _ -)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        vid = parsed.path.lstrip("/").split("/")[0]
        return vid if vid else None

    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            return qs.get("v", [None])[0]
        for prefix in ("/embed/", "/v/", "/shorts/"):
            if parsed.path.startswith(prefix):
                return parsed.path[len(prefix):].split("/")[0]

    return None


def fetch_transcript(video_id: str) -> tuple[str, list[dict]]:
    """Return (plain_text, raw_segments) for a video ID."""
    ytt_api = YouTubeTranscriptApi()
    raw = ytt_api.fetch(video_id)
    formatter = TextFormatter()
    plain = formatter.format_transcript(raw)
    segments = [{"text": s.text, "start": s.start, "duration": s.duration} for s in raw]
    return plain, segments


def get_gemini_client():
    """Configure and return a Gemini GenAI Client."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.error(
            "🔑 **GEMINI_API_KEY not found.** "
            "Create a `.env` file with your key (see `.env.example`)."
        )
        st.stop()
    return genai.Client(api_key=api_key)


def generate_summary(client, transcript_text: str) -> str:
    """Generate a structured summary from transcript text."""
    prompt = SUMMARY_PROMPT.format(transcript=transcript_text[:60_000])
    response = client.interactions.create(
        model=GEMINI_MODEL,
        input=prompt
    )
    return response.output_text


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="YouTube Summarizer & Q&A",
        page_icon="🎬",
        layout="wide",
    )

    st.title("🎬 YouTube Video Summarizer & Q&A")
    st.caption("Paste a YouTube link → get an AI summary → ask follow-up questions")

    # ---- Session state init ------------------------------------------------
    for key, default in {
        "video_id": None,
        "transcript_text": None,
        "transcript_segments": None,
        "summary": None,
        "chat_history": [],
        "last_interaction_id": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # ---- Sidebar -----------------------------------------------------------
    with st.sidebar:
        st.header("⚙️ Settings")
        st.markdown(f"**Model:** `{GEMINI_MODEL}`")
        if st.button("🗑️ Clear session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ---- URL Input ---------------------------------------------------------
    url = st.text_input(
        "🔗 YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=...",
    )

    col1, col2 = st.columns([1, 3])
    summarize_clicked = col1.button("📝 Summarize", type="primary", use_container_width=True)

    # ---- Process URL -------------------------------------------------------
    if summarize_clicked and url:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("❌ Could not extract a valid video ID. Please check your URL.")
            st.stop()

        # Show thumbnail
        st.image(
            f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            caption=f"Video ID: {video_id}",
            width=480,
        )

        # Fetch transcript
        with st.spinner("📄 Fetching transcript…"):
            try:
                text, segments = fetch_transcript(video_id)
            except Exception as e:
                st.error(f"❌ **Transcript unavailable.** {e}")
                st.stop()

        st.session_state.video_id = video_id
        st.session_state.transcript_text = text
        st.session_state.transcript_segments = segments
        st.session_state.summary = None
        st.session_state.chat_history = []
        st.session_state.last_interaction_id = None

        # Generate summary
        client = get_gemini_client()
        with st.spinner("🤖 Generating summary with Gemini…"):
            try:
                summary = generate_summary(client, text)
            except Exception as e:
                st.error(f"❌ **Gemini API error.** {e}")
                st.stop()

        st.session_state.summary = summary

    # ---- Display Summary ---------------------------------------------------
    if st.session_state.summary:
        st.divider()
        st.subheader("📋 Video Summary")
        st.markdown(st.session_state.summary)

        with st.expander("📄 Raw Transcript", expanded=False):
            st.text_area(
                "Full transcript",
                value=st.session_state.transcript_text,
                height=300,
                disabled=True,
                label_visibility="collapsed",
            )

    # ---- Chat Q&A ----------------------------------------------------------
    if st.session_state.transcript_text:
        st.divider()
        st.subheader("💬 Ask Questions About the Video")

        # Render chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if question := st.chat_input("Ask anything about the video…"):
            # Show user message
            with st.chat_message("user"):
                st.markdown(question)

            client = get_gemini_client()
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        system_instruction = QA_SYSTEM_PROMPT.format(
                            transcript=st.session_state.transcript_text[:60_000]
                        )
                        
                        kwargs = {
                            "model": GEMINI_MODEL,
                            "input": question,
                            "system_instruction": system_instruction,
                        }
                        
                        # Use the stateful Interactions API if we have an ongoing chat
                        if st.session_state.last_interaction_id:
                            kwargs["previous_interaction_id"] = st.session_state.last_interaction_id
                            
                        response = client.interactions.create(**kwargs)
                        answer = response.output_text
                        
                        # Save interaction ID for next turn
                        st.session_state.last_interaction_id = response.id
                        
                    except Exception as e:
                        answer = f"⚠️ Error generating answer: {e}"
                        
                    st.markdown(answer)

            # Persist to local display state
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
