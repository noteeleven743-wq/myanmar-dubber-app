import streamlit as st
import whisper
import google.generativeai as genai
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip
import os
import tempfile

st.title("🎬 AI Video Dubbing (Chinese to Myanmar)")
st.write("တရုတ်ဗီဒီယိုများကို မြန်မာလို အလိုအလျောက် အသံထည့်ပေးမည့် App (Gemini AI အသုံးပြုထားပါသည်)")

# Gemini API Key ချိတ်ဆက်ခြင်း
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Gemini API Key ကို Streamlit Secrets တွင် မထည့်ရသေးပါ။")

uploaded_file = st.file_uploader("သင့်၏ ဗီဒီယိုဖိုင် (.mp4) ကို ဤနေရာတွင် ရွေးချယ်တင်ပါ", type=["mp4"])

if uploaded_file is not None:
    if st.button("🚀 စတင် ဘာသာပြန်မည်"):
        st.info("လုပ်ဆောင်နေပါသည်... (ဗီဒီယိုရှည်ပါက အချိန်အနည်းငယ် ကြာနိုင်ပါသည်)")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(uploaded_file.read())
            temp_video_path = temp_video.name

        try:
            # ၁။ အသံခွဲထုတ်ခြင်း
            st.text("၁။ ဗီဒီယိုထဲမှ အသံကို ခွဲထုတ်နေပါသည်...")
            video = VideoFileClip(temp_video_path)
            temp_audio_path = "temp_audio.wav"
            video.audio.write_audiofile(temp_audio_path, logger=None)

            # ၂။ စာသားပြောင်းခြင်း (Whisper)
            st.text("၂။ တရုတ်အသံကို စာသားအဖြစ် ပြောင်းနေပါသည်...")
            model = whisper.load_model("base")
            result = model.transcribe(temp_audio_path)
            original_text = result["text"]
            st.success(f"မူရင်းစာသား တွေ့ရှိပါသည် - {original_text}")

            if original_text.strip() == "":
                st.warning("ဗီဒီယိုထဲမှ စကားပြောသံကို မဖမ်းမိပါ။ ဗီဒီယိုအသံ တိုးနေခြင်း ဖြစ်နိုင်ပါသည်။")
            else:
                # ၃။ မြန်မာလို ဘာသာပြန်ခြင်း (Gemini AI)
                st.text("၃။ မြန်မာဘာသာသို့ ပြန်ဆိုနေပါသည် (Gemini AI ဖြင့်)...")
                
                # Gemini ကို ဘာသာပြန်ခိုင်းခြင်း (gemini-pro သို့ ပြောင်းထားသည်)
                gemini_model = genai.GenerativeModel('gemini-pro')
                prompt = f"Translate the following Chinese text to Myanmar (Burmese) language naturally. Do not output any other text, just the direct translation:\n\n{original_text}"
                response = gemini_model.generate_content(prompt)
                myanmar_text = response.text.strip()
                
                st.success(f"Gemini ၏ ဘာသာပြန်ဆိုမှု - {myanmar_text}")
                
                # ၄။ မြန်မာအသံ ဖန်တီးခြင်း
                st.text("၄။ မြန်မာအသံအဖြစ်သို့ ပြောင်းလဲနေပါသည်...")
                myanmar_audio_path = "myanmar_audio.mp3"
                tts = gTTS(text=myanmar_text, lang='my', slow=False)
                tts.save(myanmar_audio_path)

                # အသံဖိုင် သီးသန့်ထုတ်ပြခြင်း
                st.audio(myanmar_audio_path, format="audio/mp3")

                # ၅။ ဗီဒီယိုနှင့် အသံပေါင်းခြင်း
                st.text("၅။ ဗီဒီယိုနှင့် အသံကို ပြန်လည် ပေါင်းစပ်နေပါသည်...")
                output_video_path = "Myanmar_Dubbed_Video.mp4"
                new_audio = AudioFileClip(myanmar_audio_path)
                final_video = video.set_audio(new_audio)
                final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True, logger=None)

                st.success("🎉 အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ! အောက်ပါခလုတ်ကို နှိပ်၍ ရယူပါ။")

                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="📥 ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
                        data=file,
                        file_name="Myanmar_Dubbed_Video.mp4",
                        mime="video/mp4"
                    )

        except Exception as e:
            st.error(f"အဆင်မပြေမှု တစ်ခုခုဖြစ်သွားပါသည် - {e}")
