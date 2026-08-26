import streamlit as st
import os, sys, subprocess, re
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
from moviepy.audio.AudioClip import AudioClip
import whisper

st.set_page_config(page_title="Fast AI Dubbing", page_icon="⚡")
st.title("⚡ AI Video Dubbing (Fast & Optimized)")
st.write("စာတန်းထိုးခြင်းနှင့် Effect များကို ဖြုတ်ထားသောကြောင့် ဗီဒီယိုထွက်နှုန်း အလွန်မြန်ဆန်ပါသည်။")

video_file = st.file_uploader("🎬 ဗီဒီယို (MP4) တင်ပါ", type=['mp4'])
my_text = st.text_area("📝 ဘာသာပြန်ထားသော စာသားများ ထည့်ပါ", height=200, placeholder="[0] စာသား...\n[1] စာသား...")

if st.button("🚀 ဗီဒီယို စတင်ဖန်တီးမည်"):
    if video_file and my_text:
        with st.spinner('ဗီဒီယိုကို သိမ်းဆည်းနေပါသည်...'):
            with open("video.mp4", "wb") as f:
                f.write(video_file.read())
                
        with st.spinner('အသံပိုင်းဆိုင်ရာ စစ်ဆေးနေပါသည်... (Whisper AI)'):
            t_dict = {int(m[0]):m[1].strip() for m in re.findall(r'\[(\d+)\]\s*(.*)', my_text.strip())}
            
            subprocess.run(['ffmpeg', '-y', '-i', 'video.mp4', '-q:a', '0', '-map', 'a', 'temp_audio.wav'], capture_output=True)
            video = VideoFileClip("video.mp4") # ဘယ်ညာလှန်ခြင်း ဖြုတ်ထားပါသည်
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
            txt = t_dict.get(i, '')
            
            if txt:
                # အသံ ၅၀% ချဲ့ထားပါသည်
                subprocess.run([sys.executable, '-m', 'edge_tts', '--text', txt.strip(), '--voice', 'my-MM-ThihaNeural', '--volume=+50%', '--write-media', f'temp_{i}.mp3'], check=True)
                
                # အသံကို ၃၀% ပိုမြန်အောင် လုပ်ထားပါသည် (factor=1.3)
                r_aud = AudioFileClip(f'temp_{i}.mp3').fx(vfx.speedx, factor=1.3)
                
                if sp_clip.duration > 0 and r_aud.duration > 0:
                    # ရုပ်ကို အသံအသစ်နှင့် ကိုက်ညီအောင် ချိန်ညှိခြင်း (စာတန်းထိုးနှင့် Blur များ ဖြုတ်ထားပါသည်)
                    adj_clip = sp_clip.fx(vfx.speedx, factor=sp_clip.duration / r_aud.duration).set_audio(r_aud)
                    f_clips.append(adj_clip)
                else:
                    f_clips.append(sp_clip.set_audio(AudioClip(lambda t: [0,0], duration=sp_clip.duration)))
            else:
                f_clips.append(sp_clip.set_audio(AudioClip(lambda t: [0,0], duration=sp_clip.duration)))
            
            last_e = min(e_t, video.duration)
            progress_bar.progress((i + 1) / len(segments))
            progress_text.text(f"လုပ်ဆောင်နေပါသည်... အပိုင်း {i+1}/{len(segments)} ပြီးစီးပါပြီ")
        
        if last_e < video.duration:
            f_clips.append(video.subclip(last_e, video.duration).set_audio(AudioClip(lambda t: [0,0], duration=video.duration-last_e)))
            
        with st.spinner('ဗီဒီယို ပေါင်းစပ်နေပါသည် (မြန်ဆန်ပါမည်)...'):
            final_video = concatenate_videoclips(f_clips, method='compose')
            final_video.write_videofile('Final_Video.mp4', codec='libx264', audio_codec='aac', logger=None)
            
        st.success("🎉 အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
        
        with open("Final_Video.mp4", "rb") as file:
            btn = st.download_button(
                label="📥 ဗီဒီယိုကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
                data=file,
                file_name="Myanmar_Dubbed_Fast.mp4",
                mime="video/mp4"
            )
    else:
        st.warning("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုနှင့် စာသားများကို ပြည့်စုံစွာ ထည့်ပါ။")

