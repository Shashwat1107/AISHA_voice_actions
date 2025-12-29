# import openwakeword
# from openwakeword.model import Model
# import pyaudio
# import numpy as np

# # 1. Initialize with ONNX (No tflite needed!)
# # openWakeWord will automatically find the 'alexa' onnx model
# model = Model(wakeword_models=['alexa'], inference_framework='onnx')

# # 2. Setup Microphone Stream
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 16000
# CHUNK = 1280 # openWakeWord works best with this chunk size

# audio = pyaudio.PyAudio()
# stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
# #---------------------------------------------------------
# import logging
# # 1. Setup the logger to save to 'errors.log'
# logging.basicConfig(
#     filename='errors.log', 
#     level=logging.ERROR,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
# #----------------------------------------------------------
# print("Listening for 'Alexa'...")
# try:
#     while True:
#         # Read audio data
#         data = stream.read(CHUNK)
#         audio_frame = np.frombuffer(data, dtype=np.int16)
        
#         # Predict
#         prediction = model.predict(audio_frame)
        
#         # If confidence is above 0.5, trigger the Brain
#         if prediction['alexa'] > 0.5:
#             print("\n[!] Alexa detected! Waking up...")
            
#             # Here is where you call your Stage 2 (Speech-to-Text)
#             # command = listen_and_process_with_qwen() 
#             # print(f"Executing: {command}")
# except Exception as e:
#     logging.error("An error occurred", exc_info=True)


#---------------------------------------------------------
import webbrowser
# Add at top if needed: import webbrowser
def search_and_play_on_youtube(query):
    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        return "✗ Install yt-dlp (pip install yt-dlp) to enable YouTube playback"

    try:
        opts = {'quiet': True, 'skip_download': True}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entry = info['entries'][0]
            video_id = entry.get('id') or ''
            title = entry.get('title', 'track')
            # Prefer Music url (opens in browser)
            url = f"https://music.youtube.com/watch?v={video_id}"
            webbrowser.open(url)
            return f"▶ Playing on YouTube Music: {title}"
    except Exception as e:
        return f"✗ Playback failed: {e}"
    
if __name__ == "__main__":
    print(search_and_play_on_youtube("dangal dangal"))