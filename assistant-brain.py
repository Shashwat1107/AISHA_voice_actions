import speech_recognition as sr
import ollama
import json
from volume_control import VolumeController

vc = VolumeController()

def get_brain_output(user_text):
    # Simplified prompt for Qwen 1.7B
    prompt = f"""
    TASK: Convert user text to JSON. 
    COMMANDS: [SET_REMINDER, VOLUME_CONTROL, MEDIA_CONTROL, OPEN_APP, WEB_SEARCH]
    USER SAYS: "{user_text}"
    JSON:"""

    try:
        # Use 'chat' instead of 'generate' for better instruction following
        response = ollama.chat(model='qwen3:1.7b', messages=[
            {'role': 'user', 'content': prompt}
        ], format='json')
        
        return response['message']['content']
    except Exception as e:
        return f"Error: {e}"

def listen():
    r = sr.Recognizer()
    r.energy_threshold=1000; r.phrase_time_limit=7; r.pause_threshold=0.7
    with sr.Microphone() as source:
        print("\n[STEP 1] Listening... (Speak now)")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)
    
    try:
        text = r.recognize_google(audio)
        if("Ayesha" in text or "Aisha" in text or "aayesha" in text):
            print(f"[STEP 2] Recognized Text: {text}")
            return text
    except:
        print("[STEP 2] Failed: Could not hear anything.")
        return None

# --- TEST ---
voice_input = listen()
# if voice_input:
#     result = get_brain_output(voice_input)
#     print(f"[STEP 3] Executable Command: {result}")

if __name__ == "__main__":
    print(voice_input)