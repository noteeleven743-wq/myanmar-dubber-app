import streamlit as st
import os, sys, subprocess, time
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
from moviepy.audio.AudioClip import AudioClip
import whisper
import google.generativeai as genai

st.set_page_config(page_title="Auto AI Dubbing", page_icon="🤖")
st.title("🤖 AI Auto Dubbing (Gemini + Fast)")
st.write("Gemini AI ဖြင့် အလိုအလျောက် ဘာသာပြန်ပေးပါမည်။ ရုပ်ထွက်ပိုင်းများကို ဖြုတ်ထား၍ ပိုမိုမြန်ဆန်ပါသည်။")

# API Key ထည့်ရန် နေရာ
api_key = st.text_input("🔑 Google Gemini API Key ထည့်ပါ", type="password")
video_file = st.file_uploader("🎬 ဗီဒီယို (MP4) တင်ပါ", type=['mp4'])

if st.button("🚀 အလိုအလျောက် ဗီဒီယို စတင်ဖန်တီးမည်"):
    if video_file and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error("API Key မှားယွင်းနေပါသည်။ ပြန်စစ်ဆေးပေးပါ။")
            st.stop()

        with st.spinner('ဗီဒီယိုကို သိမ်းဆည်းနေပါသည်...'):
            with open("video.mp4", "wb") as f:
                f.write(video_file.read())
                
        with st.spinner('အသံပိုင်းဆိုင်ရာ စစ်ဆေးနေပါသည်... (Whisper AI)'):
            subprocess.run(['ffmpeg', '-y', '-i', 'video.mp4', '-q:a', '0', '-map', 'a', 'temp_audio.wav'], capture_output=True)
            video = VideoFileClip("video.mp4")
            segments = whisper.load_model('base').transcribe('temp_audio.wav')['segments']
            
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        f_clips, last_e = [], 0
        for i, seg in enumerate(segments):
            s_t, e_t = seg['start'], seg['end']
            if s_t > last_e and last_e < video.duration:
                f_clips.append(video.subclip(last_e, min(s_t, video.duration)).set_audio(AudioClip(lambda t: [0,0], duration=min(s_t, video.duration)-last_e)))
            if s_t >= video.duration: break
            
            sp_clip = video.subclip(s_t, min(e_t, video.duration))
            
            # မူရင်းစာသား
            original_text = seg['text'].strip()
            txt = ''
            
            if original_text:
                try:
                    # Gemini သို့ ဘာသာပြန်ခိုင်းခြင်း
                    prompt = f"အောက်ပါ တရုတ်စာသားကို Movie Recap အတွက် မြန်မာလို သဘာဝကျကျ ဘာသာပြန်ပေးပါ။ စည်းကမ်းချက် - ဇာတ်ကောင်နာမည်တွေ လုံးဝ မထည့်ပါနဲ့။ နိုင်ငံခြားနာမည်တွေအစား 'ကောင်လေး'၊ 'ကောင်မလေး'၊ 'အမျိုးသား'၊ 'အမျိုးသမီး' စသည်ဖြင့်သာ သုံးပါ။ ဘာသာပြန်ထားသော မြန်မာစာသားသီးသန့်ကိုသာ ပြန်ထုတ်ပေးပါ။ စာသား: {original_text}"
                    response = model.generate_content(prompt)
                    txt = response.text.strip()
                    time.sleep(2) # API Limit မဖြစ်စေရန် ခဏနားခြင်း
                except Exception as e:
                    txt = original_text # ဘာသာပြန်မရပါက မူရင်းအတိုင်းထားမည်
            
            if txt:
                for c in ['.',',','?','!','\"','\'','-','...']: txt = txt.replace(c, ' ')
                
                # အသံ ၅၀% ချဲ့ထားပါသည်
                subprocess.run([sys.executable, '-m', 'edge_tts', '--text', txt.strip(), '--voice', 'my-MM-ThihaNeural', '--volume=+50%', '--write-media', f'temp_{i}.mp3'], check=True)
                
                # အသံကို ၃၀% ပိုမြန်အောင် လုပ်ထားပါသည် (factor=1.3)
                r_aud = AudioFileClip(f'temp_{i}.mp3').fx(vfx.speedx, factor=1.3)
                
                if sp_clip.duration > 0 and r_aud.duration > 0:
                    # ရုပ်ကို အသံအသစ်နှင့် ကိုက်ညီအောင် ချိန်ညှိခြင်း (Blur ဖြုတ်ထားသည်)
                    adj_clip = sp_clip.fx(vfx.speedx, factor=sp_clip.duration / r_aud.duration).set_audio(r_aud)
                    f_clips.append(adj_clip)
                else:
                    f_clips.append(sp_clip.set_audio(AudioClip(lambda t: [0,0], duration=sp_clip.duration)))
            else:
                f_clips.append(sp_clip.set_audio(AudioClip(lambda t: [0,0], duration=sp_clip.duration)))
            
            last_e = min(e_t, video.duration)
            progress_bar.progress((i + 1) / len(segments))
            progress_text.text(f"Gemini ဖြင့် ဘာသာပြန်နေပါသည်... အပိုင်း {i+1}/{len(segments)} ပြီးစီးပါပြီ")
        
        if last_e < video.duration:
            f_clips.append(video.subclip(last_e, video.duration).set_audio(AudioClip(lambda t: [0,0], duration=video.duration-last_e)))
            
        with st.spinner('ဗီဒီယို ပေါင်းစပ်နေပါသည် (အလွန်မြန်ဆန်ပါမည်)...'):
            final_video = concatenate_videoclips(f_clips, method='compose')
            final_video.write_videofile('Final_Auto_Video.mp4', codec='libx264', audio_codec='aac', logger=None)
            
        st.success("🎉 အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
        
        with open("Final_Auto_Video.mp4", "rb") as file:
            btn = st.download_button(
                label="📥 ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
                data=file,
                file_name="Myanmar_Dubbed_Gemini_Fast.mp4",
                mime="video/mp4"
            )
    else:
        st.warning("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုနှင့် API Key ကို ပြည့်စုံစွာ ထည့်ပါ။")
