import streamlit as st
import whisper
import google.generativeai as genai
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
import os
import tempfile

st.title("🎬 AI Video Dubbing (Pro Version)")
st.write("ရုပ်နှင့်အသံ တစ်ထပ်တည်းကျစေရန် ဗီဒီယိုအား အလိုအလျောက် အနှေး/အမြန် ချိန်ညှိပေးသည့်စနစ် (Gemini 3.6 Flash)")

# မြန်မာအသံချောမွေ့စေရန် သင်္ကေတများ ရှင်းလင်းသည့်လုပ်ဆောင်ချက်
def clean_text(text):
    chars_to_remove = ['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '-', '_', '။', '၊', '...']
    for c in chars_to_remove:
        text = text.replace(c, ' ')
    return text.strip()

# Gemini API Key ချိတ်ဆက်ခြင်း
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Gemini API Key ကို Streamlit Secrets တွင် မထည့်ရသေးပါ။")

uploaded_file = st.file_uploader("သင့်၏ ဗီဒီယိုဖိုင် (.mp4) ကို ဤနေရာတွင် ရွေးချယ်တင်ပါ", type=["mp4"])

if uploaded_file is not None:
    if st.button("🚀 စတင် ဘာသာပြန်မည်"):
        st.info("လုပ်ဆောင်နေပါသည်... ရုပ်နှင့်အသံ အတိအကျ ချိန်ညှိနေသဖြင့် အချိန်ပိုကြာနိုင်ပါသည်။ ခေတ္တစောင့်ဆိုင်းပေးပါ။")

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
                st.text("၃။ မြန်မာအသံဖန်တီး၍ ဗီဒီယိုကို အချိန်ကိုက် ချိန်ညှိနေပါသည် (ဤအဆင့် အချိန်အနည်းငယ် ကြာပါမည်)...")
                gemini_model = genai.GenerativeModel('gemini-3.6-flash')
                
                final_clips = []
                last_end = 0
                progress_bar = st.progress(0)
                total_segments = len(segments)

                for i, segment in enumerate(segments):
                    start_time = segment["start"]
                    end_time = segment["end"]
                    original_text = segment["text"].strip()
                    
                    # (က) စကားမပြောဘဲ တိတ်ဆိတ်နေသည့် ကြားကာလ (Gap) များကို မူလအတိုင်း ထည့်သွင်းခြင်း
                    if start_time > last_end:
                        gap_duration = start_time - last_end
                        if gap_duration > 0 and last_end < video.duration:
                            safe_start = min(start_time, video.duration)
                            gap_clip = video.subclip(last_end, safe_start)
                            final_clips.append(gap_clip)

                    # (ခ) စကားပြောသည့် အပိုင်းကို ဖြတ်ထုတ်ခြင်း
                    if start_time >= video.duration:
                        break
                    safe_end = min(end_time, video.duration)
                    speech_clip = video.subclip(start_time, safe_end)

                    try:
                        if original_text:
                            # ၁။ ဘာသာပြန်ခြင်း
                            prompt = f"Translate the following Chinese text to Myanmar (Burmese) language naturally. Only output the direct translation:\n\n{original_text}"
                            response = gemini_model.generate_content(prompt)
                            myanmar_text = response.text.strip()
                            
                            # ၂။ စာသားသန့်စင်ခြင်း (Text Cleaning)
                            cleaned_myanmar_text = clean_text(myanmar_text)
                            
                            # ၃။ မြန်မာအသံ ဖန်တီးခြင်း
                            temp_seg_audio = f"temp_audio_{i}.mp3"
                            tts = gTTS(text=cleaned_myanmar_text, lang='my', slow=False)
                            tts.save(temp_seg_audio)
                            audio_clip = AudioFileClip(temp_seg_audio)
                            
                            # ၄။ ရုပ်နှင့်အသံ အံဝင်ခွင်ကျဖြစ်စေရန် ဗီဒီယိုကို အမြန်/အနှေး ချိန်ညှိခြင်း (Time-Stretching)
                            target_duration = audio_clip.duration
                            current_duration = speech_clip.duration
                            
                            if current_duration > 0 and target_duration > 0:
                                speed_factor = current_duration / target_duration
                                adjusted_clip = speech_clip.fx(vfx.speedx, factor=speed_factor)
                                adjusted_clip = adjusted_clip.set_audio(audio_clip)
                                final_clips.append(adjusted_clip)
                            else:
                                final_clips.append(speech_clip)
                        else:
                            final_clips.append(speech_clip)
                            
                    except Exception as e:
                        # Error တက်လျှင် မူလဗီဒီယိုအပိုင်းကိုသာ ပြန်ထည့်မည်
                        final_clips.append(speech_clip)
                    
                    last_end = safe_end
                    progress_bar.progress((i + 1) / total_segments)

                # (ဂ) နောက်ဆုံးကျန်နေသည့် ဗီဒီယိုအစွန်းအစများကို ပြန်ပေါင်းထည့်ခြင်း
                if last_end < video.duration:
                    final_clips.append(video.subclip(last_end, video.duration))

                st.text("၄။ အပိုင်းများအားလုံးကို ဗီဒီယိုတစ်ခုတည်းအဖြစ် ပြန်လည် ပေါင်းစပ်နေပါသည်...")
                output_video_path = "Myanmar_Dubbed_Pro.mp4"
                
                if final_clips:
                    final_video = concatenate_videoclips(final_clips)
                    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-final-audio.m4a", remove_temp=True, logger=None)

                    st.success("🎉 အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ! အောက်ပါခလုတ်ကို နှိပ်၍ ရယူပါ။")

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
