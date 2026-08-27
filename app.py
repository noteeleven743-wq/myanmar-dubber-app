import streamlit as st
import os, sys, subprocess
from moviepy.editor import VideoFileClip, AudioFileClip
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx

st.set_page_config(page_title="Manual AI Dubbing", page_icon="🎬")
st.title("🎬 AI Dubbing (Manual Text)")
st.write("ကိုယ်တိုင် ဘာသာပြန်ထားသော မြန်မာစာသားများကို ထည့်သွင်း၍ ဗီဒီယိုဖြင့် ပေါင်းစပ်ပါမည်။")

# ဗီဒီယိုနှင့် စာသား တောင်းခံမည့် အပိုင်း
video_file = st.file_uploader("🎬 ဗီဒီယို (MP4) တင်ပါ", type=['mp4'])
myanmar_text = st.text_area("📝 မြန်မာစာသားကို ဒီမှာ ထည့်ပါ (Script)", height=200)

if st.button("🚀 ဗီဒီယို စတင်ဖန်တီးမည်"):
    if video_file and myanmar_text.strip():
        with st.spinner('ဗီဒီယိုကို သိမ်းဆည်းနေပါသည်...'):
            with open("video.mp4", "wb") as f:
                f.write(video_file.read())
        
        with st.spinner('အသံ ဖန်တီးနေပါသည် (Thiha Neural)...'):
            try:
                # စာသားများကို ပြင်ဆင်ခြင်း
                txt = myanmar_text.strip()
                for c in ['.',',','?','!','\"','\'','-','...']: 
                    txt = txt.replace(c, ' ')
                
                # Edge-tts ဖြင့် အသံထွက်ခြင်း
                subprocess.run([sys.executable, '-m', 'edge_tts', '--text', txt, '--voice', 'my-MM-ThihaNeural', '--write-media', 'temp_audio.mp3'], check=True)
                
                # ဗီဒီယိုကို ခေါ်ယူခြင်း
                video = VideoFileClip("video.mp4")
                
                # 🔊 အသံကို ၃၀% ပိုမြန်အောင် (1.3x) နှင့် ၅၀% ပိုကျယ်အောင် (1.5x) လုပ်ခြင်း
                r_aud = AudioFileClip('temp_audio.mp3').fx(vfx.speedx, factor=1.3).fx(afx.volumex, 1.5)
                
                # ဗီဒီယိုနှင့် အသံ ပေါင်းစပ်ခြင်း
                final_video = video.set_audio(r_aud)
                
                with st.spinner('ဗီဒီယိုနှင့် အသံ ပေါင်းစပ်နေပါသည်...'):
                    final_video.write_videofile('Final_Manual_Video.mp4', codec='libx264', audio_codec='aac', logger=None)
                    
                st.success("🎉 အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
                
                # ဒေါင်းလုဒ်ခလုတ်
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
        st.warning("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုနှင့် စာသားကို ပြည့်စုံစွာ ထည့်ပါ။")

