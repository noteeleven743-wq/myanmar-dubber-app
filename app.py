import streamlit as st
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ColorClip, CompositeVideoClip, ImageClip
import moviepy.video.fx.all as vfx
from moviepy.audio.AudioClip import AudioClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import sys
import tempfile
import subprocess
import re

st.set_page_config(layout="wide")
st.title("🎬 AI Video Dubbing (All-In-One Ultimate Mode)")
st.write("မူပိုင်ခွင့်ကင်းရှင်းစေမည့် Effects များနှင့် မြန်မာစာတန်းထိုး (Burn-in Subtitles) အားလုံး တစ်နေရာတည်းတွင် ပါဝင်သောစနစ်")

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

def make_frame_mute(t):
    return [0, 0]

def create_subtitle_clip(text, video_w, video_h, duration, font_path):
    sub_h = int(video_h * 0.2)
    img = Image.new('RGBA', (video_w, sub_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_size = int(video_h * 0.045) 
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = draw.textsize(text, font=font)

    x = (video_w - text_w) / 2
    y = (sub_h - text_h) / 2

    stroke_width = max(1, int(font_size * 0.05))
    draw.text((x, y), text, font=font, fill="white", stroke_width=stroke_width, stroke_fill="black")

    clip = ImageClip(np.array(img)).set_duration(duration)
    return clip

col_v, col_f = st.columns(2)
with col_v:
    uploaded_file = st.file_uploader("၁။ သင့်၏ ဗီဒီယိုဖိုင် (.mp4) ကို တင်ပါ", type=["mp4"])
with col_f:
    font_file = st.file_uploader("၂။ မြန်မာဖောင့်ဖိုင် (.ttf) ကို တင်ပါ (စာတန်းထိုးရန်)", type=["ttf"])

if uploaded_file is not None:
    if st.button("၃။ ဗီဒီယိုမှ မူရင်းစာသားများကို ထုတ်ယူမည်"):
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
        st.success("မူရင်းစာသားများ ထုတ်ယူပြီးပါပြီ။")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("မူရင်း တရုတ်စာသားများ", value=st.session_state.original_text, height=250)
        
        with col2:
            translated_input = st.text_area("မြန်မာလို ဘာသာပြန်ထားသော စာသားများကို ဤနေရာတွင် Paste ချပါ", height=250)

        st.write("---")
        st.write("### 🛠️ ဗီဒီယို ပြုပြင်ရန် ရွေးချယ်မှုများ (All-In-One)")
        col3, col4 = st.columns(2)
        with col3:
            apply_flip = st.checkbox("🪞 ဗီဒီယိုကို ဘယ်ညာ ပြောင်းပြန်လှန်မည် (Mirror Effect)", value=True)
            apply_color = st.checkbox("🎨 ကာလာကို အနည်းငယ် ပြောင်းမည် (Color Tweak)", value=True)
        with col4:
            apply_blur_bar = st.checkbox("⬛ အောက်ခြေတွင် တရုတ်စာဖုံးရန် အလွှာပါးခံမည် (Dark Overlay)", value=True)
            apply_burn_subtitles = st.checkbox("📝 ဗီဒီယိုပေါ်တွင် မြန်မာစာတန်း အသေထိုးမည် (Burn-in Subtitles)", value=True)

        if st.button("၄။ အသံထည့်၍ ဗီဒီယို ဖန်တီးမည်"):
            if not translated_input.strip():
                st.error("ကျေးဇူးပြု၍ ဘာသာပြန်စာသားများ အရင် ထည့်ပေးပါ။")
            elif apply_burn_subtitles and font_file is None:
                st.error("စာတန်းထိုးရန်အတွက် မြန်မာဖောင့်ဖိုင် (.ttf) ကို အပေါ်တွင် အရင်တင်ပေးပါ။")
            else:
                st.info("မြန်မာအသံ နှင့် စာတန်းထိုးများကို ဗီဒီယိုပေါ်သို့ ပေါင်းစပ်နေပါသည်...")
                
                # ဖောင့်ဖိုင်ကို ယာယီသိမ်းဆည်းခြင်း
                current_font_path = "default"
                if font_file is not None:
                    with open("temp_font.ttf", "wb") as f:
                        f.write(font_file.read())
                    current_font_path = "temp_font.ttf"

                translated_dict = {}
                pattern = r"\[(\d+)\]\s*(.*)"
                matches = re.findall(pattern, translated_input)
                for match in matches:
                    translated_dict[int(match[0])] = match[1].strip()

                video = VideoFileClip(st.session_state.video_path)
                
                if apply_flip:
                    video = video.fx(vfx.mirror_x)
                if apply_color:
                    video = video.fx(vfx.colorx, factor=1.05)
                if apply_blur_bar:
                    bar_height = int(video.h * 0.18)
                    dark_clip = ColorClip(size=(video.w, bar_height), color=(0,0,0)).set_opacity(0.6).set_position(('center', 'bottom')).set_duration(video.duration)
                    video = CompositeVideoClip([video, dark_clip])

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
                            mute_audio = AudioClip(make_frame_mute, duration=gap_clip.duration)
                            gap_clip = gap_clip.set_audio(mute_audio)
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
                            subprocess.run(
                                [sys.executable, '-m', 'edge_tts', '--text', cleaned_myanmar_text, '--voice', 'my-MM-ThihaNeural', '--write-media', temp_seg_audio], 
                                check=True, capture_output=True
                            )
                            
                            raw_audio_clip = AudioFileClip(temp_seg_audio)
                            fast_audio_clip = raw_audio_clip.fx(vfx.speedx, factor=1.15)
                            
                            target_duration = fast_audio_clip.duration
                            current_duration = speech_clip.duration
                            
                            if current_duration > 0 and target_duration > 0:
                                speed_factor = current_duration / target_duration
                                adjusted_clip = speech_clip.fx(vfx.speedx, factor=speed_factor)
                                adjusted_clip = adjusted_clip.set_audio(fast_audio_clip)
                                
                                if apply_burn_subtitles and current_font_path != "default":
                                    sub_clip = create_subtitle_clip(myanmar_text, adjusted_clip.w, adjusted_clip.h, adjusted_clip.duration, current_font_path)
                                    adjusted_clip = CompositeVideoClip([adjusted_clip, sub_clip.set_position(('center', 'bottom'))])
                                
                                final_clips.append(adjusted_clip)
                            else:
                                mute_audio = AudioClip(make_frame_mute, duration=speech_clip.duration)
                                speech_clip = speech_clip.set_audio(mute_audio)
                                final_clips.append(speech_clip)
                                
                        except Exception:
                            mute_audio = AudioClip(make_frame_mute, duration=speech_clip.duration)
                            speech_clip = speech_clip.set_audio(mute_audio)
                            final_clips.append(speech_clip)
                    else:
                        mute_audio = AudioClip(make_frame_mute, duration=speech_clip.duration)
                        speech_clip = speech_clip.set_audio(mute_audio)
                        final_clips.append(speech_clip)
                    
                    last_end = safe_end
                    progress_bar.progress((i + 1) / total_segments)

                if last_end < video.duration:
                    end_clip = video.subclip(last_end, video.duration)
                    mute_audio = AudioClip(make_frame_mute, duration=end_clip.duration)
                    end_clip = end_clip.set_audio(mute_audio)
                    final_clips.append(end_clip)

                output_video_path = "Myanmar_Dubbed_All_In_One.mp4"
                
                if final_clips:
                    final_video = concatenate_videoclips(final_clips)
                    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-final-audio.m4a", remove_temp=True, logger=None)

                    st.balloons()
                    st.success("🎉 All-In-One ဗီဒီယိုကို အောင်မြင်စွာ ပြုပြင်ဖန်တီးပြီးပါပြီ!")

                    with open(output_video_path, "rb") as file:
                        st.download_button(
                            label="📥 All-In-One ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန်",
                            data=file,
                            file_name="Myanmar_Dubbed_All_In_One.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("ဗီဒီယို ဖန်တီးမှု မအောင်မြင်ပါ။")

