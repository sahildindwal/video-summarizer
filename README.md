# YouTube Video Summarizer & Interactive Q&A 🎬

A powerful web application built with **Streamlit** and the **Google Gemini API** that instantly extracts transcripts from YouTube videos, generates structured executive summaries, and lets you ask follow-up questions about the video content via an interactive chat interface.

## ✨ Features

- **Instant YouTube Parsing:** Supports standard, shortened (`youtu.be`), embed, and Shorts URLs.
- **Automated Summarization:** Instantly generates a structured summary using Gemini 3.7 Flash, including:
  - 📝 Executive Overview
  - 🎯 Top 5 Key Takeaways
  - 💬 Notable Quotes with approximate timestamps
- **Interactive Q&A Chat:** A multi-turn chat interface grounded strictly in the video's transcript. Ask anything, and the AI will answer based *only* on the video content.
- **Modern API Integration:** Powered by the latest `google-genai` SDK and the stateful Gemini Interactions API.

## 🛠️ Tech Stack

- **Frontend/UI:** [Streamlit](https://streamlit.io/)
- **LLM Engine:** [Google Gemini (gemini-3.7-flash)](https://ai.google.dev/)
- **Transcript Extraction:** `youtube-transcript-api`
- **Environment Management:** `python-dotenv`

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- A free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/youtube-summarizer.git
   cd youtube-summarizer
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .\.venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API Key:**
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and replace `your_gemini_api_key_here` with your actual Google Gemini API key.

### Running the App

Start the Streamlit server:
```bash
python -m streamlit run app.py
```

The app will automatically open in your default browser at `http://localhost:8501`.

## 💡 How to Use

1. **Paste a Link:** Drop any YouTube video URL into the input field.
2. **Summarize:** Click the "📝 Summarize" button. The app will fetch the transcript and generate a structured overview.
3. **Ask Questions:** Scroll down to the chat interface to ask specific questions about the video. The AI maintains conversation history and references the transcript to answer your queries.

## ⚠️ Limitations
- **Disabled Captions:** The app relies on YouTube's subtitle system. If a video creator has disabled captions entirely, the transcript cannot be fetched.
- **Context Limit:** Transcripts are currently capped at 60,000 characters to ensure optimal processing speeds and remain well within the model context limits.

## 📄 License
This project is licensed under the MIT License.
