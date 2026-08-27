import streamlit as st
import os, sys, subprocess
from moviepy.editor import VideoFileClip, AudioFileClip
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx
import whisper

st.set_page_config(page_title="AI Dubbing (Auto Text + Manual Translate)", page_icon="🎬")
st.title("🎬 AI Dubbing (မူရင်းစာသား + ကိုယ်တိုင်ဘာသာပြန်)")
st.write("ဗီဒီယိုတင်လိုက်ပါ၊ မူရင်းစာသားကို အလိုအလျောက် ထုတ်ပေးပါမည်။ ထို့နောက် မြန်မာလို ဘာသာပြန်ထည့်ပါ။")

video_file = st.file_uploader("🎬 ဗီဒီယို (MP4) တင်ပါ", type=['mp4'])

if video_file:
    # ဗီဒီယိုကို သိမ်းဆည်းခြင်း
    with open("video.mp4", "wb") as f:
        f.write(video_file.read())

    # Whisper ဖြင့် စာသားထုတ်ခြင်း (တစ်ခါသာ လုပ်ဆောင်ရန် session_state ကို သုံးထားပါသည်)
    if 'original_text' not in st.session_state or st.session_state.video_name != video_file.name:
        with st.spinner('အသံကို စာသားအဖြစ် ပြောင်းလဲနေပါသည် (Whisper AI)... ခဏစောင့်ပေးပါ...'):
            try:
                subprocess.run(['ffmpeg', '-y', '-i', 'video.mp4', '-q:a', '0', '-map', 'a', 'temp_audio.wav'], capture_output=True)
                model = whisper.load_model('base')
                result = model.transcribe('temp_audio.wav')
                st.session_state.original_text = result['text'].strip()
                st.session_state.video_name = video_file.name
            except Exception as e:
                st.error("⚠️ မူရင်းအသံကို စာသားပြောင်းရာတွင် အခက်အခဲရှိနေပါသည်။ (ဗီဒီယိုတွင် အသံပါ/မပါ စစ်ဆေးပါ)")
                st.session_state.original_text = ""
                st.session_state.video_name = video_file.name

    # မူရင်းစာသားကို ပြသခြင်း (ပြင်လို့မရအောင် disabled လုပ်ထားသည်)
    st.text_area("📝 မူရင်းစာသား (Original Text)", value=st.session_state.original_text, height=150, disabled=True)

    # မြန်မာလို ရိုက်ထည့်ရန် နေရာ
    myanmar_text = st.text_area("✍️ မြန်မာလို ဘာသာပြန်ကို ဒီမှာ ရိုက်ထည့်ပါ", height=150)

    if st.button("🚀 ဗီဒီယို စတင်ဖန်တီးမည်"):
        if myanmar_text.strip():
            with st.spinner('အသံ ဖန်တီးနေပါသည် (Thiha Neural)...'):
                try:
                    txt = myanmar_text.strip()
                    # မလိုအပ်သော သင်္ကေတများ ဖယ်ရှားခြင်း
                    for c in ['.',',','?','!','\"','\'','-','...']: 
                        txt = txt.replace(c, ' ')
                    
                    # Edge-tts ဖြင့် မြန်မာအသံ ထုတ်ခြင်း
                    subprocess.run([sys.executable, '-m', 'edge_tts', '--text', txt, '--voice', 'my-MM-ThihaNeural', '--write-media', 'temp_audio.mp3'], check=True)
                    
                    video = VideoFileClip("video.mp4")
                    
                    # 🔊 အသံကို ၃၀% ပိုမြန်အောင် (1.3x) နှင့် ၅၀% ပိုကျယ်အောင် (1.5x) လုပ်ခြင်း
                    r_aud = AudioFileClip('temp_audio.mp3').fx(vfx.speedx, factor=1.3).fx(afx.volumex, 1.5)
                    
                    final_video = video.set_audio(r_aud)
                    
                    with st.spinner('ဗီဒီယိုနှင့် အသံ ပေါင်းစပ်နေပါသည်...'):
                        final_video.write_videofile('Final_Manual_Video.mp4', codec='libx264', audio_codec='aac', logger=None)
                        
                    st.success("🎉 အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
                    
                    with open("Final_Manual_Video.mp4", "rb") as file:
                        st.download_button(
                            label="📥 ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
                            data=file,
                            file_name="Myanmar_Dubbed_Manual.mp4",
                            mime="video/mp4"
                        )
                except Exception as e:
                    st.error(f"⚠️ Error ဖြစ်နေပါသည်: {e}")
        else:
            st.warning("⚠️ ကျေးဇူးပြု၍ မြန်မာစာသား ထည့်ပေးပါ။")
