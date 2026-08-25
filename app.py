import streamlit as st
import whisper
import google.generativeai as genai
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
import os
import tempfile
import time

st.title("🎬 AI Video Dubbing (Pro Version - Custom Voice)")
st.write("AI အသံကို ၃၀% ပိုမြန်စေပြီး ရုပ်နှင့်အသံ အလိုအလျောက် ချိန်ညှိပေးသည့်စနစ်")

# ကိုရဲလင်းနိုင်၏ စည်းကမ်းချက်များအတိုင်း စာသားကို သန့်စင်ပေးမည့်စနစ်
def clean_and_format_for_tts(text):
    # သင်္ကေတများ ဖယ်ရှားခြင်း
    chars_to_remove = ['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '-', '_', '...']
    for c in chars_to_remove:
        text = text.replace(c, ' ')
        
    # သတ်မှတ်ထားသော စာလုံးပေါင်းများ အလိုအလျောက် ပြင်ဆင်ခြင်း
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
        "၁": "တစ်", "၂": "နှစ်", "၃": "သုံး", "၄": "လေး", "၅": "ငါး", "၆": "ခြောက်", "၇": "ခုနစ်", "၈": "ရှစ်", "၉": "ကိုး", "၀": "သုည"
    }
    for old_word, new_word in replacements.items():
        text = text.replace(old_word, new_word)
        
    return text.strip()

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Gemini API Key ကို Streamlit Secrets တွင် မထည့်ရသေးပါ။")

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
                st.text("၃။ မြန်မာအသံဖန်တီး၍ ဗီဒီယိုကို အချိန်ကိုက် ချိန်ညှိနေပါသည်...")
                gemini_model = genai.GenerativeModel('gemini-3.6-flash')
                
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

                    try:
                        if original_text:
                            # ကိုရဲလင်းနိုင်၏ အမိုက်စား Prompt အသစ်
                            prompt = f"""အောက်ပါ တရုတ်စာသားကို မြန်မာလို ဘာသာပြန်ပေးပါ။ အောက်ပါ စည်းကမ်းချက်များကို တိတိကျကျ လိုက်နာပါ -
၁။ ဇာတ်ကောင်နာမည်တွေ လုံးဝ မထည့်ရ (နိုင်ငံခြားနာမည်တွေအစား ကောင်လေး၊ ကောင်မလေး၊ သူဌေး၊ အမေ စသဖြင့် နာမ်စားများသာ သုံးပါ)။
၂။ ပုံအညွှန်း (Image descriptions) များ လုံးဝ မထည့်ရ။
၃။ ဇာတ်လမ်းပြောပြသည့်ပုံစံ ဖြင့် ရိုးရှင်း၊ ချောမွေ့ပြီး နားထောင်လို့ကောင်းအောင် ပုံပြင်ပြောပြတဲ့ ပုံမျိုး ရေးပေးပါ။
၄။ မူရင်းဇာတ်လမ်းပါ အကြောင်းအရာ အချက်အလက်များကို တစ်ခုမှ မကျန်စေဘဲ အသေးစိတ် အပြည့်အစုံ ပြန်ဆိုပေးပါ။
၅။ အင်္ဂလိပ်စာလုံး လုံးဝ မရောဘဲ မြန်မာဘာသာ သီးသန့်ဖြင့်သာ ရေးပေးပါ။

ဘာသာပြန်ရမည့် တရုတ်စာသား - {original_text}"""
                            
                            response = gemini_model.generate_content(prompt)
                            myanmar_text = response.text.strip()
                            
                            # စာသားသန့်စင်ခြင်း
                            cleaned_myanmar_text = clean_and_format_for_tts(myanmar_text)
                            
                            # မြန်မာအသံ ဖန်တီးခြင်း
                            temp_seg_audio = f"temp_audio_{i}.mp3"
                            tts = gTTS(text=cleaned_myanmar_text, lang='my', slow=False)
                            tts.save(temp_seg_audio)
                            
                            # အသံကို ၃၀% မြန်စေရန် Speed Up (1.3x) လုပ်ခြင်း
                            raw_audio_clip = AudioFileClip(temp_seg_audio)
                            fast_audio_clip = raw_audio_clip.fx(vfx.speedx, factor=1.3)
                            
                            target_duration = fast_audio_clip.duration
                            current_duration = speech_clip.duration
                            
                            if current_duration > 0 and target_duration > 0:
                                speed_factor = current_duration / target_duration
                                adjusted_clip = speech_clip.fx(vfx.speedx, factor=speed_factor)
                                adjusted_clip = adjusted_clip.set_audio(fast_audio_clip)
                                final_clips.append(adjusted_clip)
                            else:
                                final_clips.append(speech_clip)
                                
                            # API limit မကျော်စေရန် ၂ စက္ကန့် အနားပေးခြင်း
                            time.sleep(2) 
                            
                        else:
                            final_clips.append(speech_clip)
                            
                    except Exception as e:
                        st.warning(f"အပိုင်းအမှတ် {i+1} တွင် အခက်အခဲရှိနေပါသည်: {e}") 
                        final_clips.append(speech_clip)
                        time.sleep(2)
                    
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

