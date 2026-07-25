import os
import sys
import json
import contextlib
import streamlit as st
from dotenv import load_dotenv

# Load existing environment
load_dotenv()

import shorts_generator.config as config
from shorts_generator import generate_shorts

# Set page configuration
st.set_page_config(
    page_title="AI YouTube Shorts Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        background: linear-gradient(135deg, #FF0000 0%, #FF6B6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #dee2e6;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #FF0000;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #495057;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Helper context manager to redirect stdout/stderr to Streamlit
class StreamlitStdoutRedirector:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.buffer = []
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, data):
        self.original_stdout.write(data)
        self.buffer.append(data)
        text = "".join(self.buffer)
        lines = text.splitlines()[-40:]  # Show last 40 lines of log
        self.placeholder.code("\n".join(lines))

    def flush(self):
        self.original_stdout.flush()

@contextlib.contextmanager
def redirect_stdout_to_streamlit(placeholder):
    redirector = StreamlitStdoutRedirector(placeholder)
    sys.stdout = redirector
    sys.stderr = redirector
    try:
        yield redirector
    finally:
        sys.stdout = redirector.original_stdout
        sys.stderr = redirector.original_stderr

# Title Area
st.markdown("<h1 class='main-title'>🎬 AI YouTube Shorts Generator</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>An open-source alternative to Opus Clip, Vidyo.ai, and Klap. Drop a YouTube URL, extract viral highlights, and auto-crop to 9:16!</p>", unsafe_allow_html=True)

# Sidebar for Configuration & API Keys
st.sidebar.image("https://img.shields.io/badge/Powered%20by-MuAPI-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMSAxNHYtNGgtMnYtMmg0djZoLTJ6bTAtOFY2aDJ2MmgtMnoiLz48L3N2Zz4=")
st.sidebar.header("🔑 API Keys & Settings")

# Retrieve values from active environment or fallback to empty
env_muapi_key = os.getenv("MUAPI_API_KEY", "")
env_openai_key = os.getenv("OPENAI_API_KEY", "")
env_gemini_key = os.getenv("GEMINI_API_KEY", "")
env_provider = os.getenv("LLM_PROVIDER", "openai")

muapi_key = st.sidebar.text_input("MuAPI API Key (API Mode)", value=env_muapi_key, type="password", help="Required for API mode.")
llm_provider = st.sidebar.selectbox("LLM Provider (Local Mode)", options=["OpenAI", "Gemini"], index=0 if env_provider.lower() == "openai" else 1)

openai_key = st.sidebar.text_input("OpenAI API Key (Local OpenAI Mode)", value=env_openai_key, type="password", help="Required for Local Mode if using OpenAI.")
gemini_key = st.sidebar.text_input("Gemini API Key (Local Gemini Mode)", value=env_gemini_key, type="password", help="Required for Local Mode if using Gemini.")

# Button to save configuration back to .env
if st.sidebar.button("💾 Save to .env"):
    try:
        # Write keys to .env
        with open(".env", "w") as f:
            f.write(f"MUAPI_API_KEY={muapi_key}\n")
            f.write(f"LLM_PROVIDER={llm_provider.lower()}\n")
            f.write(f"OPENAI_API_KEY={openai_key}\n")
            f.write(f"OPENAI_MODEL={os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}\n")
            f.write(f"GEMINI_API_KEY={gemini_key}\n")
            f.write(f"GEMINI_MODEL={os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}\n")
            f.write(f"LOCAL_WHISPER_MODEL={os.getenv('LOCAL_WHISPER_MODEL', 'base')}\n")
            f.write(f"LOCAL_WHISPER_DEVICE={os.getenv('LOCAL_WHISPER_DEVICE', 'auto')}\n")
            f.write(f"LOCAL_OUTPUT_DIR={os.getenv('LOCAL_OUTPUT_DIR', 'output')}\n")
            f.write(f"LOCAL_WHISPER_VAD_FILTER={os.getenv('LOCAL_WHISPER_VAD_FILTER', 'false')}\n")

        # Reload env
        os.environ["MUAPI_API_KEY"] = muapi_key
        os.environ["LLM_PROVIDER"] = llm_provider.lower()
        os.environ["OPENAI_API_KEY"] = openai_key
        os.environ["GEMINI_API_KEY"] = gemini_key

        st.sidebar.success("Settings saved to .env!")
    except Exception as e:
        st.sidebar.error(f"Failed to save to .env: {e}")

# Main Form Layout
col_main, col_options = st.columns([2, 1])

with col_main:
    st.markdown("### 📽️ Video Source")
    video_url = st.text_input(
        "YouTube Video URL or Local Video Path",
        placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        help="Input a YouTube link or a direct path to a local MP4 file (Local mode only)."
    )

with col_options:
    st.markdown("### ⚙️ Generation Options")
    mode = st.selectbox(
        "Execution Mode",
        options=["API (MuAPI Cloud)", "Local (Self-Hosted)"],
        index=0,
        help="API mode uses MuAPI cloud servers (faster, no GPU/local resources needed). Local mode runs entirely on your machine."
    )

    num_clips = st.slider("Number of Shorts to Generate", min_value=1, max_value=10, value=3)
    aspect_ratio = st.selectbox("Output Aspect Ratio", options=["9:16", "1:1", "16:9"], index=0)
    download_format = st.selectbox("Download Format Quality", options=["720", "1080", "480", "360"], index=0)
    language = st.text_input("Language Code (Optional)", placeholder="auto", help="e.g. 'en', 'es', 'ar'. Fallback is auto-detection.")

st.markdown("---")

# Processing and output
if st.button("🚀 Generate Shorts ⚡", type="primary", use_container_width=True):
    if not video_url:
        st.error("Please provide a valid YouTube URL or video path.")
    else:
        # Override config variables at runtime
        config.MUAPI_API_KEY = muapi_key
        config.OPENAI_API_KEY = openai_key
        config.GEMINI_API_KEY = gemini_key
        config.LLM_PROVIDER = llm_provider.lower()

        # Map modes
        selected_mode = "api" if "API" in mode else "local"

        st.info(f"Starting {selected_mode.upper()} mode generation pipeline for: {video_url}")

        # Console logs area
        st.markdown("### 📊 Console & Processing Logs")
        log_placeholder = st.empty()
        log_placeholder.code("Initializing pipeline...")

        # Error / result container
        result = None
        error_msg = None

        with redirect_stdout_to_streamlit(log_placeholder):
            try:
                result = generate_shorts(
                    youtube_url=video_url,
                    num_clips=num_clips,
                    aspect_ratio=aspect_ratio,
                    download_format=download_format,
                    language=language if language else None,
                    mode=selected_mode
                )
            except Exception as e:
                error_msg = str(e)

        if error_msg:
            st.error(f"❌ Generation Failed: {error_msg}")
        elif result:
            st.success("🎉 Shorts generation completed successfully!")

            # Show summary stats
            st.markdown("### 📈 Generation Summary")
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.markdown(f"<div class='metric-card'><div class='metric-value'>{result.get('mode', selected_mode).upper()}</div><div class='metric-label'>Pipeline Mode</div></div>", unsafe_allow_html=True)
            with stat_col2:
                st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(result.get('highlights', []))}</div><div class='metric-label'>Highlight Candidates Found</div></div>", unsafe_allow_html=True)
            with stat_col3:
                st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(result.get('shorts', []))}</div><div class='metric-label'>Top Clips Kept</div></div>", unsafe_allow_html=True)

            # Resulting Shorts Grid
            st.markdown("### 🎥 Generated Shorts")

            shorts = result.get("shorts", [])
            for idx, short in enumerate(shorts, 1):
                with st.container():
                    st.markdown(f"#### 🎥 Clip #{idx}: {short.get('title', 'No Title')}")

                    col_clip_info, col_clip_player = st.columns([1, 1])

                    with col_clip_info:
                        st.markdown(f"**🔥 Virality Score:** `{short.get('score', 0)}/100`")
                        st.markdown(f"**⏰ Timestamp Range:** `{short.get('start_time', 0.0):.1f}s` to `{short.get('end_time', 0.0):.1f}s`")
                        st.markdown(f"**💬 Hook:** *\"{short.get('hook_sentence', 'N/A')}\"*")
                        st.markdown(f"**💡 Why it's viral:** {short.get('virality_reason', 'N/A')}")

                        clip_url = short.get("clip_url")
                        if clip_url:
                            if clip_url.startswith("http"):
                                st.markdown(f"[📥 Download Short Clip]({clip_url})")
                            else:
                                # Local path file helper
                                if os.path.exists(clip_url):
                                    with open(clip_url, "rb") as f:
                                        st.download_button(
                                            label="📥 Download Local MP4 File",
                                            data=f,
                                            file_name=os.path.basename(clip_url),
                                            mime="video/mp4",
                                            key=f"dl_btn_{idx}"
                                        )
                        else:
                            st.warning("No clip URL generated. Rendering might have failed.")

                    with col_clip_player:
                        clip_url = short.get("clip_url")
                        if clip_url:
                            if clip_url.startswith("http"):
                                st.video(clip_url)
                            elif os.path.exists(clip_url):
                                st.video(clip_url)
                            else:
                                st.info(f"Local file: {clip_url}")
                        else:
                            st.info("No media player available.")

                    st.markdown("---")

            # Raw JSON result accordion
            with st.expander("📄 View Raw JSON Output"):
                st.json(result)
