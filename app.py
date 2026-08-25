import streamlit as st
import whisper
from deep_translator import GoogleTranslator
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
import os
import tempfile
import subprocess

st.title("🎬 AI Video Dubbing (No API Key - Fast Version)")
st.write("API Key လုံးဝမလိုဘဲ အခမဲ့ ဘာသာပြန်ပေးပြီး Microsoft Azure AI အသံ (Thiha) ဖြင့် Dubbing ထိုးပေးသည့်စနစ်")

def clean_and_format_for_tts(text):
    chars_to_remove = ['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '-', '_', '...']
    for c in chars_to_remove:
        text = text.replace(c, ' ')
        
    replacements = {
        "ယောက်ျား": "ယောက်ကျား",
        "သူဌေး": "သဌေး",
        "ကုတင်": "ကတင်",
        "မြွေ": "မွေ",
        "ခင်ပွန်းသည်": "ခင်ပွန်းသယ်",
        "ဇနီးသည်": "ဇနီးသယ်",
        "ဧည့်သည်": "ဧည့်သယ်",
        "ဂိုဏ်း": "ဂိုင်း",
        "ကောင်မလေး": "ကောင်မ လေး",
        "အံ့ဩ": "အံ့အော",
        "ပါးစပ်": "ပစပ်",
        "ဓားပြ": "ဒမြ",
        "ဧကရာဇ်": "အေကရစ်",
        "ယဇ်ပလ္လင်": "ရစ်ပလင်",
        "ယဇ်ကောင်": "ရစ်ကောင်",
        "သူတောင်းစား": "သတောင်းစား",
        "CEO": "စီးအီးအို",
        "လောလီပေါ့": "သကြားလုံး",
        "တစ်ကောင်": "တစ် ကောင်", 
        "တံခါး": "တခါး",
        "ကြပါဘူး": "ကျပါဘူး",
        "သတ္တဝါ": "သက်တဝါ",
        "၁": "တစ်", "၂": "နှစ်", "၃": "သုံး", "၄": "လေး", "၅": "ငါး", "၆": "ခြောက်", "၇": "ခုနစ်", "၈": "ရှစ်", "၉": "ကိုး", "၀": "သုည"
    }
    for old_word, new_word in replacements.items():
        text = text.replace(old_word, new_word)
        
    return text.strip()

uploaded_file = st.file_uploader("သင့်၏ ဗီဒီယိုဖိုင် (.mp4) ကို ဤနေရာတွင် ရွေးချယ်တင်ပါ", type=["mp4"])

if uploaded_file is not None:
    if st.button("🚀 စတင် ဘာသာပြန်မည်"):
        st.info("လုပ်ဆောင်နေပါသည်... စနစ်အား အနားပေး၍ လုပ်ဆောင်နေသဖြင့် အချိန်ပိုကြာနိုင်ပါသည်။")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(uploaded_file.read())
            temp_video_path = temp_video.name

        try:
            st.text("၁။ ဗီဒီယိုထဲမှ အသံကို ခွဲထုတ်နေပါသည်...")
            video = VideoFileClip(temp_video_path)
            temp_audio_path = "temp_audio.wav"
            video.audio.write_audiofile(temp_audio_path, logger=None)

            st.text("၂။ တရုတ်အသံကို အချိန်နှင့်တကွ ခွဲခြား မှတ်သားနေပါသည်...")
            model = whisper.load_model("base")
            result = model.transcribe(temp_audio_path)
            segments = result["segments"]

            if not segments:
                st.warning("ဗီဒီယိုထဲမှ စကားပြောသံကို မဖမ်းမိပါ။")
            else:
                st.text("၃။ API Key မလိုသောစနစ်ဖြင့် ဘာသာပြန်၍ ဗီဒီယိုကို အချိန်ကိုက် ချိန်ညှိနေပါသည်...")
                
                translator = GoogleTranslator(source='auto', target='my')
                
                final_clips = []
                last_end = 0
                progress_bar = st.progress(0)
                total_segments = len(segments)

                for i, segment in enumerate(segments):
                    start_time = segment["start"]
                    end_time = segment["end"]
                    original_text = segment["text"].strip()
                    
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

                    if original_text:
                        try:
                            # API Key မလိုဘဲ တိုက်ရိုက် ဘာသာပြန်ခြင်း (Limit မရှိပါ)
                            myanmar_text = translator.translate(original_text)
                            
                            if myanmar_text:
                                cleaned_myanmar_text = clean_and_format_for_tts(myanmar_text)
                                temp_seg_audio = f"temp_audio_{i}.mp3"
                                
                                subprocess.run(['edge-tts', '--text', cleaned_myanmar_text, '--voice', 'my-MM-ThihaNeural', '--write-media', temp_seg_audio])
                                
                                raw_audio_clip = AudioFileClip(temp_seg_audio)
                                fast_audio_clip = raw_audio_clip.fx(vfx.speedx, factor=1.15)
                                
                                target_duration = fast_audio_clip.duration
                                current_duration = speech_clip.duration
                                
                                if current_duration > 0 and target_duration > 0:
                                    speed_factor = current_duration / target_duration
                                    adjusted_clip = speech_clip.fx(vfx.speedx, factor=speed_factor)
                                    adjusted_clip = adjusted_clip.set_audio(fast_audio_clip)
                                    final_clips.append(adjusted_clip)
                                else:
                                    final_clips.append(speech_clip)
                            else:
                                final_clips.append(speech_clip)
                                
                        except Exception as e:
                            st.warning(f"အပိုင်းအမှတ် {i+1} တွင် အခက်အခဲရှိနေပါသည်: {e}")
                            final_clips.append(speech_clip)
                    else:
                        final_clips.append(speech_clip)
                    
                    last_end = safe_end
                    progress_bar.progress((i + 1) / total_segments)

                if last_end < video.duration:
                    final_clips.append(video.subclip(last_end, video.duration))

                st.text("၄။ အပိုင်းများအားလုံးကို ဗီဒီယိုတစ်ခုတည်းအဖြစ် ပြန်လည် ပေါင်းစပ်နေပါသည်...")
                output_video_path = "Myanmar_Dubbed_Pro.mp4"
                
                if final_clips:
                    final_video = concatenate_videoclips(final_clips)
                    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-final-audio.m4a", remove_temp=True, logger=None)

                    st.success("🎉 အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!")

                    with open(output_video_path, "rb") as file:
                        st.download_button(
                            label="📥 Pro ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
                            data=file,
                            file_name="Myanmar_Dubbed_Pro.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("ဗီဒီယို ဖန်တီးမှု မအောင်မြင်ပါ။")

        except Exception as e:
            st.error(f"အဆင်မပြေမှု တစ်ခုခုဖြစ်သွားပါသည် - {e}")

