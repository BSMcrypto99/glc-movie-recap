import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import asyncio
import edge_tts
import os
import re

# Page Configuration
st.set_page_config(page_title="GLC Movie Recap Automation AI", page_icon="🎬", layout="wide")

st.title("🎬 GLC Movie Recap Automation AI Dashboard")
st.caption("YouTube Link မှတစ်ဆင့် Copyright လွတ် မြန်မာ Script၊ AI Prompts နှင့် Voice များ ထုတ်လုပ်ပေးသည့် စနစ် (Advanced Subtitle-Free Mode)")

# Sidebar - API Configuration & Inputs
st.sidebar.header("⚙️ Configuration Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password", value=os.environ.get("GEMINI_API_KEY", ""))

if api_key:
    genai.configure(api_key=api_key)
else:
    if os.environ.get("GEMINI_API_KEY"):
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    else:
        st.sidebar.warning("⚠️ Please enter your Gemini API Key to proceed.")

st.sidebar.markdown("---")
st.sidebar.header("📹 Video & Audio Options")

video_size = st.sidebar.selectbox(
    "Select Video Size (Aspect Ratio):",
    options=["16:9 (YouTube Standard)", "9:16 (TikTok/Shorts/Reels)", "1:1 (Square)"]
)

voice_option = st.sidebar.selectbox(
    "Select AI Voice (Myanmar):",
    options=["မြန်မာအမျိုးသမီးသံ (Thiha)", "မြန်မာအမျိုးသားသံ (Khin)"]
)

voice_mapping = {
    "မြန်မာအမျိုးသမီးသံ (Thiha)": "my-MM-ThihaNeural",
    "မြန်မာအမျိုးသားသံ (Khin)": "my-MM-KhinNeural"
}

def get_video_id(url):
    regex = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/|youtube\.com/live/)([^#\&\?]+)'
    match = re.search(regex, url)
    if match:
        return match.group(4)
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

def get_youtube_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'my'])
        full_transcript = " ".join([t['text'] for t in transcript_list])
        return full_transcript, True
    except Exception as e:
        return f"No Subtitles Found (Error: {str(e)})", False

async def generate_voice(text, voice_name, output_filename):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_filename)

# Main Dashboard Interface
video_link = st.text_input("🔗 Paste YouTube Video Link Here:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Process & Generate Recap Package"):
    if not api_key and not os.environ.get("GEMINI_API_KEY"):
        st.error("Please provide a valid Gemini API Key.")
    elif not video_link:
        st.error("Please paste a YouTube link first.")
    else:
        video_id = get_video_id(video_link)
        
        if not video_id:
            st.error("Invalid YouTube Link Layout. Please check the URL.")
        else:
            with st.spinner("📥 Extracting transcript/subtitles from YouTube video..."):
                source_data, has_subtitles = get_youtube_transcript(video_id)
                
            if not api_key:
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            
            with st.spinner("🤖 AI is analyzing the data and preparing your Recap Package..."):
                # UNIVERSAL BACKUP PROTECTION FOR GEMINI MODELS
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    # Just a test call to see if it causes 404
                    test_response = model.generate_content("test")
                except Exception as model_err:
                    # If 1.5-pro fails with 404, switch instantly to 1.5-flash which is widely compatible
                    model = genai.GenerativeModel('gemini-1.5-flash')
                
                try:
                    base_prompt = f"""
                    You are an expert AI YouTube Movie Recap Scriptwriter for the digital brand "GLC Entertainment".
                    Your task is to write a highly engaging, dramatic, and thrilling movie recap script in Burmese.
                    
                    Strict Rules for Production Alignment:
                    1. Create an original narrative flow based on the story timeline to safely bypass copyright flags.
                    2. The tone must be conversational, captivating, and fast-paced (Burmese vlog/storytelling style).
                    3. Format the final output into clear sections:
                       - [BURMESE SCRIPT FOR TTS]: Write the pure text that will be fed into a Text-to-Speech reader. Do not include scene numbers inside this section.
                       - [AI VIDEO/PHOTO PROMPTS]: Provide visual generation prompts in English based on key scenes. Match the aspect ratio requirement: {video_size}.
                    """
                    
                    if has_subtitles:
                        st.success("✅ Subtitles extracted successfully! Processing via Transcript Mode.")
                        with st.expander("📄 View Raw English Transcript"):
                            st.write(source_data)
                        full_prompt = f"{base_prompt}\n\nHere is the source transcript to completely rewrite and transform:\n{source_data}"
                    else:
                        st.info("ℹ️ Note: This video has no English subtitles. Activating 'Auto-Story Search Backup Mode' using the Video ID.")
                        full_prompt = f"""
                        {base_prompt}
                        
                        CRITICAL INSTRUCTION FOR BACKUP MODE:
                        The user provided a YouTube video link with ID '{video_id}' which does not have built-in subtitles. 
                        Please utilize your vast internal knowledge base, web-search capabilities, and data patterns to identify which movie, show, or story this video ID or topic likely corresponds to. 
                        If you cannot pinpoint the exact video, generate a highly thrilling and generic action/thriller/horror movie recap script that fits a YouTube recap format perfectly.
                        """
                    
                    response = model.generate_content(full_prompt)
                    ai_output = response.text
                    
                    st.subheader("✨ Generated Output Package")
                    
                    script_section = ai_output
                    prompt_section = "AI Prompts generated inside the text."
                    
                    if "[BURMESE SCRIPT FOR TTS]" in ai_output:
                        parts = ai_output.split("[AI VIDEO/PHOTO PROMPTS]")
                        script_section = parts[0].replace("[BURMESE SCRIPT FOR TTS]", "").strip()
                        if len(parts) > 1:
                            prompt_section = parts[1].strip()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📝 Copyright-Free Burmese Script")
                        st.text_area("Final Script Text:", value=script_section, height=400)
                        
                    with col2:
                        st.markdown(f"### 🖼️ AI Photo/Video Prompts ({video_size})")
                        st.text_area("Use these prompts in Midjourney/Imagen/Runway:", value=prompt_section, height=400)
                    
                    st.markdown("---")
                    st.subheader("🔊 AI Audio Voice Generation")
                    
                    clean_burmese_text = re.sub(r'\[.*?\]', '', script_section).strip()
                    
                    with st.spinner("🎙️ Generating high-quality Burmese audio file..."):
                        selected_voice = voice_mapping[voice_option]
                        output_audio_path = "glc_recap_voice.mp3"
                        
                        asyncio.run(generate_voice(clean_burmese_text[:2000], selected_voice, output_audio_path))
                        
                        if os.path.exists(output_audio_path):
                            st.success(f"✅ Audio generated successfully using {voice_option}!")
                            st.audio(output_audio_path, format="audio/mp3")
                            
                            with open(output_audio_path, "rb") as file:
                                st.download_button(
                                    label="📥 Download Audio (MP3)",
                                    data=file,
                                    file_name=f"glc_recap_{voice_option}.mp3",
                                    mime="audio/mp3"
                                )
                        else:
                            st.error("Failed to generate the audio file.")
                            
                except Exception as e:
                    st.error(f"Error during AI Processing: {str(e)}")
