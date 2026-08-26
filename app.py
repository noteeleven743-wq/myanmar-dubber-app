import streamlit as st
import whisper
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
import os
import tempfile
import subprocess
import re

st.title("🎬 AI Video Dubbing (Ultimate Pro - Gemini 1.5 Flash)")
st.write("အကောင်းဆုံးသော AI ဘာသာပြန်စနစ်နှင့် Microsoft (Thiha) အသံဖြင့် Movie Recap ဗီဒီယိုများ ဖန်တီးပေးသည့်စနစ်")

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

# Secrets ထဲမှ API Key ကို လှမ်းယူခြင်း
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Gemini API Key ကို Streamlit Secrets တွင် ထည့်သွင်းရန် လိုအပ်ပါသည်။")

uploaded_file = st.file_uploader("သင့်၏ ဗီဒီယိုဖိုင် (.mp4) ကို ဤနေရာတွင် ရွေးချယ်တင်ပါ", type=["mp4"])

if uploaded_file is not None:
    if st.button("🚀 စတင် ဘာသာပြန်မည်"):
        st.info("လုပ်ဆောင်နေပါသည်... အကောင်းဆုံး အရည်အသွေးရရှိရန် အချိန်အနည်းငယ် စောင့်ဆိုင်းပေးပါ။")

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
                st.text("၃။ Gemini 1.5 Flash ဖြင့် Movie Recap စတိုင် ဘာသာပြန်နေပါသည် (Batch Mode)...")
                
                # စာကြောင်းများကို [0] စာသား, [1] စာသား ပုံစံဖြင့် စုစည်းခြင်း
                batch_texts = []
                for i, segment in enumerate(segments):
                    text = segment["text"].strip()
                    if text:
                        batch_texts.append(f"[{i}] {text}")
                
                full_prompt_text = "\n".join(batch_texts)
                
                prompt = (
                    "အောက်ပါ တရုတ်စာသားများကို မြန်မာလို ဘာသာပြန်ပေးပါ။ စာကြောင်းတစ်ခုစီ၏ ရှေ့တွင် ကွင်းပိတ်နှင့် နံပါတ် (ဥပမာ - [0], [1]) ပါရှိပါသည်။\n"
                    "ဘာသာပြန်ပြီးပါက ထိုနံပါတ်ကွင်းပိတ်ကို မူလအတိုင်း မပျက်မကွက် ပြန်ထည့်ပေးပါ။ ဥပမာ: '[0] မင်္ဂလာပါ။'\n\n"
                    "**အရေးကြီးသော စည်းကမ်းချက်များ:**\n"
                    "၁။ **Movie Recap စတိုင်:** ရုပ်ရှင်ကို ပရိသတ်အား ပြန်ပြောပြနေသည့် သွက်လက်သော စကားပြောဟန်ဖြင့်သာ ပြန်ဆိုပါ။ 'ထိုသူသည်', '၎င်းက' ကဲ့သို့ စာအုပ်ကြီးဆန်သော စကားလုံးများ လုံးဝမသုံးပါနှင့်။\n"
                    "၂။ **ဇာတ်ကောင်နာမည် မသုံးရ:** နာမည်များအစား (ဥပမာ - ကောင်လေး၊ ကောင်မလေး၊ လူဆိုးကြီး၊ သဌေး) စသဖြင့် နာမ်စားများကိုသာ သုံးပါ။\n"
                    "၃။ အခြားပိုနေသော စကားချီးများ လုံးဝမထည့်ပါနှင့်။ ဘာသာပြန်စာသားသက်သက်သာ ပေးပါ။\n\n"
                    "ဘာသာပြန်ရမည့်စာသားများ:\n"
                    f"{full_prompt_text}"
                )

                translated_dict = {}
                
                # Movie Recap များအတွက် Safety Filter အားလုံးကို ဖြုတ်ချထားခြင်း
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]

                # တကယ့် အလုပ်လုပ်သော Gemini 1.5 Flash ကို သုံးခြင်း
                try:
                    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                    response = gemini_model.generate_content(prompt, safety_settings=safety_settings)
                    response_text = response.text.strip()
                    
                    # Regex ဖြင့် နံပါတ်နှင့် စာသားကို ပြန်ခွဲထုတ်ခြင်း
                    pattern = r"\[(\d+)\]\s*(.*)"
                    matches = re.findall(pattern, response_text)
                    for match in matches:
                        idx = int(match[0])
                        translated_text = match[1].strip()
                        translated_dict[idx] = translated_text
                        
                    st.success("💡 ဘာသာပြန်ဆိုမှု အောင်မြင်စွာ ပြီးစီးပါပြီ!")
                except Exception as e:
                    st.error(f"Gemini API ချိတ်ဆက်မှု အခက်အခဲဖြစ်သွားပါသည်: {e}")

                st.text("၄။ မြန်မာအသံဖန်တီး၍ ဗီဒီယိုကို အချိန်ကိုက် ချိန်ညှိနေပါသည်...")
                
                final_clips = []
                last_end = 0
                progress_bar = st.progress(0)
                total_segments = len(segments)

                for i, segment in enumerate(segments):
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

                    # Error စာသားများပါလာပါက အသံထွက်မဖတ်စေရန် တားဆီးထားခြင်း
                    if myanmar_text and "error" not in myanmar_text.lower() and "server" not in myanmar_text.lower():
                        cleaned_myanmar_text = clean_and_format_for_tts(myanmar_text)
                        temp_seg_audio = f"temp_audio_{i}.mp3"
                        
                        try:
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
                        except Exception as e:
                            final_clips.append(speech_clip)
                    else:
                        final_clips.append(speech_clip)
                    
                    last_end = safe_end
                    progress_bar.progress((i + 1) / total_segments)

                if last_end < video.duration:
                    final_clips.append(video.subclip(last_end, video.duration))

                st.text("၅။ အပိုင်းများအားလုံးကို ဗီဒီယိုတစ်ခုတည်းအဖြစ် ပြန်လည် ပေါင်းစပ်နေပါသည်...")
                output_video_path = "Myanmar_Dubbed_Pro.mp4"
                
                if final_clips:
                    final_video = concatenate_videoclips(final_clips)
                    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-final-audio.m4a", remove_temp=True, logger=None)

                    st.success("🎉 အကောင်းဆုံး အရည်အသွေးဖြင့် ပြောင်းလဲပြီးပါပြီ!")

                    with open(output_video_path, "rb") as file:
                        st.download_button(
                            label="📥 Ultimate Pro ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
                            data=file,
                            file_name="Myanmar_Dubbed_Ultimate.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("ဗီဒီယို ဖန်တီးမှု မအောင်မြင်ပါ။")

        except Exception as e:
            st.error(f"အဆင်မပြေမှု တစ်ခုခုဖြစ်သွားပါသည် - {e}")

