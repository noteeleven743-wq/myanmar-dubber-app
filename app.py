import streamlit as st
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx # 🔊 အသံကျယ်အောင် လုပ်ရန် ဤနေရာတွင် ထပ်ထည့်ထားပါသည်
import os
import sys
import tempfile
import subprocess
import re

st.set_page_config(layout="wide")
st.title("🎬 AI Video Dubbing (Manual Translation Mode)")
st.write("အရည်အသွေး အကောင်းဆုံး Movie Recap ဗီဒီယိုများ ဖန်တီးရန် ကိုယ်တိုင် ဘာသာပြန်စာသား ထည့်သွင်းနိုင်သော စနစ်")

# Session State များ သတ်မှတ်ခြင်း
if 'segments' not in st.session_state:
    st.session_state.segments = None
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'original_text' not in st.session_state:
    st.session_state.original_text = ""

def clean_and_format_for_tts(text):
    chars_to_remove = ['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '-', '_', '...']
    for c in chars_to_remove:
        text = text.replace(c, ' ')
    replacements = {
        "ယောက်ျား": "ယောက်ကျား", "သူဌေး": "သဌေး", "ကုတင်": "ကတင်", "မြွေ": "မွေ",
        "ခင်ပွန်းသည်": "ခင်ပွန်းသယ်", "ဇနီးသည်": "ဇနီးသယ်", "ဧည့်သည်": "ဧည့်သယ်",
        "ဂိုဏ်း": "ဂိုင်း", "ကောင်မလေး": "ကောင်မ လေး", "အံ့ဩ": "အံ့အော",
        "ပါးစပ်": "ပစပ်", "ဓားပြ": "ဒမြ", "ဧကရာဇ်": "အေကရစ်", "ယဇ်ပလ္လင်": "ရစ်ပလင်",
        "ယဇ်ကောင်": "ရစ်ကောင်", "သူတောင်းစား": "သတောင်းစား", "CEO": "စီးအီးအို",
        "လောလီပေါ့": "သကြားလုံး", "၁": "တစ်", "၂": "နှစ်", "၃": "သုံး", "၄": "လေး", 
        "၅": "ငါး", "၆": "ခြောက်", "၇": "ခုနစ်", "၈": "ရှစ်", "၉": "ကိုး", "၀": "သုည"
    }
    for old_word, new_word in replacements.items():
        text = text.replace(old_word, new_word)
    return text.strip()

uploaded_file = st.file_uploader("သင့်၏ ဗီဒီယိုဖိုင် (.mp4) ကို ဤနေရာတွင် ရွေးချယ်တင်ပါ", type=["mp4"])

if uploaded_file is not None:
    if st.button("၁။ ဗီဒီယိုမှ မူရင်းစာသားများကို ထုတ်ယူမည်"):
        st.info("ဗီဒီယိုထဲမှ အသံများကို စာသားအဖြစ် ပြောင်းလဲနေပါသည်... ခေတ္တစောင့်ပါ။")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(uploaded_file.read())
            st.session_state.video_path = temp_video.name

        video = VideoFileClip(st.session_state.video_path)
        temp_audio_path = "temp_audio.wav"
        video.audio.write_audiofile(temp_audio_path, logger=None)

        model = whisper.load_model("base")
        result = model.transcribe(temp_audio_path)
        st.session_state.segments = result["segments"]

        out_text = ""
        for i, segment in enumerate(st.session_state.segments):
            text = segment["text"].strip()
            if text:
                out_text += f"[{i}] {text}\n"
        
        st.session_state.original_text = out_text
        st.rerun()

    if st.session_state.segments is not None:
        st.success("မူရင်းစာသားများ ထုတ်ယူပြီးပါပြီ။ အောက်ပါ မူရင်းစာသားများကို Copy ကူး၍ ChatGPT တွင် ဘာသာပြန်ပါ။")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("မူရင်း တရုတ်စာသားများ (Copy ကူးယူပါ)", value=st.session_state.original_text, height=350)
        
        with col2:
            translated_input = st.text_area("မြန်မာလို ဘာသာပြန်ထားသော စာသားများကို ဤနေရာတွင် Paste ချပါ", height=350)

        if st.button("၂။ အသံထည့်၍ ဗီဒီယို ဖန်တီးမည် (Microsoft Thiha Voice)"):
            if not translated_input.strip():
                st.error("ကျေးဇူးပြု၍ ဘာသာပြန်စာသားများ အရင် ထည့်ပေးပါ။")
            else:
                st.info("မြန်မာအသံဖန်တီး၍ ဗီဒီယိုကို အချိန်ကိုက် ချိန်ညှိနေပါသည်...")
                
                translated_dict = {}
                pattern = r"\[(\d+)\]\s*(.*)"
                matches = re.findall(pattern, translated_input)
                for match in matches:
                    translated_dict[int(match[0])] = match[1].strip()

                video = VideoFileClip(st.session_state.video_path)
                final_clips = []
                last_end = 0
                progress_bar = st.progress(0)
                total_segments = len(st.session_state.segments)

                for i, segment in enumerate(st.session_state.segments):
                    start_time = segment["start"]
                    end_time = segment["end"]
                    
                    if start_time > last_end:
                        gap_duration = start_time - last_end
                        if gap_duration > 0 and last_end < video.duration:
                            safe_start = min(start_time, video.duration)
                            gap_clip = video.subclip(last_end, safe_start)
                            final_clips.append(gap_clip)

                    if start_time >= video.duration:
                        break
                    safe_end = min(end_time, video.duration)
                    speech_clip = video.subclip(start_time, safe_end)

                    myanmar_text = translated_dict.get(i, "")

                    if myanmar_text:
                        cleaned_myanmar_text = clean_and_format_for_tts(myanmar_text)
                        temp_seg_audio = f"temp_audio_{i}.mp3"
                        
                        try:
                            # 🚨 Streamlit တွင် သေချာပေါက် အလုပ်လုပ်စေမည့် Command အသစ် 🚨
                            subprocess.run(
                                [sys.executable, '-m', 'edge_tts', '--text', cleaned_myanmar_text, '--voice', 'my-MM-ThihaNeural', '--write-media', temp_seg_audio], 
                                check=True, capture_output=True
                            )
                            
                            raw_audio_clip = AudioFileClip(temp_seg_audio)
                            
                            # 🔊 ဤနေရာတွင် အသံကို ၃၀% ပိုမြန်အောင် (1.3) နှင့် ၅၀% ပိုကျယ်အောင် (1.5) ပြင်ထားပါသည်
                            fast_audio_clip = raw_audio_clip.fx(vfx.speedx, factor=1.3).fx(afx.volumex, 1.5)
                            
                            target_duration = fast_audio_clip.duration
                            current_duration = speech_clip.duration
                            
                            if current_duration > 0 and target_duration > 0:
                                speed_factor = current_duration / target_duration
                                adjusted_clip = speech_clip.fx(vfx.speedx, factor=speed_factor)
                                # မူရင်းတရုတ်အသံကိုဖျောက်ပြီး မြန်မာအသံအစားထိုးခြင်း
                                adjusted_clip = adjusted_clip.set_audio(fast_audio_clip)
                                final_clips.append(adjusted_clip)
                            else:
                                final_clips.append(speech_clip)
                                
                        except subprocess.CalledProcessError as e:
                            # Error တက်ပါက မျက်နှာပြင်တွင် အသိပေးမည်
                            st.warning(f"အပိုင်း [{i}] အသံဖန်တီးမှု မအောင်မြင်ပါ: {e.stderr.decode()}")
                            final_clips.append(speech_clip)
                        except Exception as e:
                            st.warning(f"အပိုင်း [{i}] အသံဖန်တီးမှု မအောင်မြင်ပါ: {e}")
                            final_clips.append(speech_clip)
                    else:
                        final_clips.append(speech_clip)
                    
                    last_end = safe_end
                    progress_bar.progress((i + 1) / total_segments)

                if last_end < video.duration:
                    final_clips.append(video.subclip(last_end, video.duration))

                output_video_path = "Myanmar_Dubbed_Manual_Pro.mp4"
                
                if final_clips:
                    final_video = concatenate_videoclips(final_clips)
                    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-final-audio.m4a", remove_temp=True, logger=None)

                    st.balloons()
                    st.success("🎉 အကောင်းဆုံး အရည်အသွေးဖြင့် ပြောင်းလဲပြီးပါပြီ!")

                    with open(output_video_path, "rb") as file:
                        st.download_button(
                            label="📥 Pro ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
                            data=file,
                            file_name="Myanmar_Dubbed_Manual_Pro.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("ဗီဒီယို ဖန်တီးမှု မအောင်မြင်ပါ။")

