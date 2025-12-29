import json
import re
import subprocess
import webbrowser
import requests
import os
import time
from datetime import datetime
from volume_control import VolumeController
import pyautogui
import ollama
import speech_recognition as sr

vc = VolumeController()

# ============================================================================
# COMMAND MAPPER - Maps text patterns to actual device functions
# ============================================================================
class CommandMapper:
    """Maps recognized commands to actual device control functions"""
    
    def __init__(self):
        self.command_keywords = {
            'VOLUME': ['volume', 'sound', 'louder', 'quieter', 'mute', 'unmute'],
            'MEDIA': ['play', 'pause', 'stop', 'next', 'previous', 'rewind', 'forward'],
            'APP': ['open', 'launch', 'start', 'run'],
            'SEARCH': ['tell me', 'search', 'google', 'find', 'look up', 'tell me about', 'who', 'what', 'when', 'where', 'why', 'how', 'explain'],
            'YOU': ['who are you', 'what can you do', 'your name', 'you'],
            'BRIGHTNESS': ['brightness', 'dim', 'bright', 'light'],
            'LOCK': ['lock', 'logout', 'sleep', 'shutdown'],
            'SCREENSHOT': ['screenshot', 'screen shot', 'capture'],
            'REMINDER': ['remind', 'reminder', 'remember', 'alert'],
            'TIME': ['time', 'what time', 'current time', 'date'],
        }
    
    def extract_intent(self, text):
        """Extract the primary intent from user input"""
        text_lower = text.lower()
        for intent, keywords in self.command_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        return 'UNKNOWN'
    
    def extract_params(self, text, intent):
        """Extract parameters relevant to the intent"""
        text_lower = text.lower()
        params = {}
        
        if intent == 'VOLUME':
            if any(word in text_lower for word in ['increase', 'louder', 'up']):
                params['action'] = 'increase'
            elif any(word in text_lower for word in ['decrease', 'quieter', 'down']):
                params['action'] = 'decrease'
            elif 'mute' in text_lower:
                params['action'] = 'mute'
            elif 'unmute' in text_lower:
                params['action'] = 'unmute'
            else:
                params['action'] = 'set'
            # Extract percentage if mentioned
            numbers = re.findall(r'\d+', text)
            if numbers:
                params['level'] = int(numbers[0])
        
        elif intent == 'APP':
            # Extract app name
            for app_word in ['open', 'launch', 'start', 'run']:
                if app_word in text_lower:
                    parts = text_lower.split(app_word, 1)
                    if len(parts) > 1:
                        params['app_name'] = parts[1].strip()
        
        elif intent == 'SEARCH':
            # # Extract search query
            # for search_word in ('search', 'google', 'find', 'look up', 'tell me about', 'who', 'what', 'when', 'where', 'why', 'how', 'explain'):
            #     if search_word in text_lower:
            #         parts = text_lower.split(search_word, 1)
            #         if len(parts) > 1 and parts[1].strip():
            #             params['query'] = parts[1].strip()
            #             break
            # Fallback: use full text as query (for direct questions like "What is python?")
            # if 'query' not in params:
                params['query'] = text.strip()
        elif intent == 'YOU':
            params['action'] = 'info'


        elif intent == 'MEDIA':
            # Detect "play <song>" vs plain "play"
            # Matches: "play bohemian rhapsody", "play thunder by imagine dragons", "play despacito on youtube music"
            play_song_match = re.match(r'play(?:\s+the)?\s+(?P<song>.+)', text_lower)
            is_generic_play = re.match(r'play(?:\s+song|music|some music|songs)?\s*$', text_lower)

            if play_song_match and not is_generic_play:
                song = play_song_match.group('song').strip()
                # Remove trailing qualifiers like "on youtube", "on youtube music", "on spotify"
                song = re.sub(r'\s+on\s+(youtube|youtube music|spotify|soundcloud)\s*$', '', song).strip()
                params['action'] = 'play'
                params['song'] = song
            elif 'play' in text_lower or 'resume' in text_lower or 'continue' in text_lower:
                params['action'] = 'play'
            elif 'pause' in text_lower or 'stop' in text_lower:
                params['action'] = 'pause'
            elif 'next' in text_lower:
                params['action'] = 'next'
            elif 'previous' in text_lower or 'play the previous' in text_lower:
                params['action'] = 'previous'
        
        elif intent == 'TIME':
            params['action'] = 'get_time'
        
        return params
    
    def map_to_function(self, intent, params):
        """Map intent and parameters to executable functions"""
        command_map = {
            'VOLUME': self.execute_volume_control,
            'MEDIA': self.execute_media_control,
            'APP': self.execute_app_control,
            'SEARCH': self.execute_web_search,
            'BRIGHTNESS': self.execute_brightness_control,
            'LOCK': self.execute_lock_control,
            'SCREENSHOT': self.execute_screenshot,
            'REMINDER': self.execute_reminder,
            'TIME': self.execute_time_command,
            'YOU': self.execute_about,
            'UNKNOWN': self.handle_unknown,
        }
        
        handler = command_map.get(intent, self.handle_unknown)
        return handler(params)
    
    # ===== DEVICE CONTROL FUNCTIONS =====
    
    def execute_volume_control(self, params):
        """Control system volume"""
        action = params.get('action', 'get')
        level = params.get('level', 50)
        
        try:
            if action == 'increase':
                vc.volume_up()
                return "✓ Volume increased"
            elif action == 'decrease':
                vc.volume_down()
                return "✓ Volume decreased"
            elif action == 'mute':
                vc.mute()
                return "✓ Muted"
            elif action == 'unmute':
                vc.unmute()
                return "✓ Unmuted"
            
            elif action == 'set':
                vc.volume_to(level/100)
                return f"✓ Volume set to {level}%"
            else:
                current = vc.get_volume()
                return f"Current volume: {current}%"
        except Exception as e:
            return f"✗ Volume control failed: {e}"
    
    def execute_media_control(self, params):
        """Control media playback"""
        action = params.get('action', 'play')
        
        try:
            # Windows media control using keyboard shortcuts
            if action == 'play' or action == 'resume' or action == 'continue':
                song = params.get('song', False)
                if song:
                    return self.search_and_play_on_youtube(song)
                
                pyautogui.press('playpause')
                return "▶ Play"
            elif action == 'pause' or action == 'stop':
                pyautogui.press('playpause')
                return "⏸ Paused"
            elif action == 'next':
                pyautogui.press('nexttrack')
                return "⏭ Next track"
            elif action == 'previous':
                pyautogui.press('prevtrack')
                return "⏮ Previous track"
        except Exception as e:
            return f"✗ Media control failed: {e}"
    
    def play_music(self, query):
        try:
            url = f"https://music.youtube.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"🎵 Playing music for: {query}"
        except Exception as e:
            return f"✗ Could not open YT music: {e}"
    
    def execute_app_control(self, params):
        """Open applications"""
        app_name = params.get('app_name', '').lower().strip()
        
        app_paths = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'chrome': 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'edge': 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
            'firefox': 'C:\\Program Files\\Mozilla Firefox\\firefox.exe',
            'word': 'WINWORD.EXE',
            'excel': 'EXCEL.EXE',
            'powershell': 'powershell.exe',
            'cmd': 'cmd.exe',
            'settings': 'ms-settings:',
            'control panel': 'control.exe',
        }
        
        try:
            app_executable = app_paths.get(app_name, app_name)
            subprocess.Popen(app_executable)
            return f"✓ Opening {app_name}"
        except Exception as e:
            return f"✗ Could not open {app_name}: {e}"
    
    def execute_local_search(self, query):
        """Attempt to get an instant answer from DuckDuckGo Instant Answer API"""
        try:
            url = "https://api.duckduckgo.com/"
            resp = requests.get(url, params={'q': query, 'format': 'json', 'no_html': 1, 'skip_disambig': 1}, timeout=5)
            data = resp.json()
            # Prefer concise AbstractText or Answer
            answer = data.get('AbstractText') or data.get('Answer') or data.get('Definition')
            if answer:
                return answer.strip()
            # Try RelatedTopics
            related = data.get('RelatedTopics', [])
            if related:
                # many entries are dicts with 'Text'
                for item in related:
                    if isinstance(item, dict) and item.get('Text'):
                        return item.get('Text')
            return None
        except Exception:
            return None

    # Add at top if needed: import webbrowser
    def search_and_play_on_youtube(self, query):
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
        
    def execute_web_search(self, params):
        """Perform web search with local instant-answer fallback"""
        query = params.get('query', 'hello world')
        
        try:
            # Try local instant answer first
            answer = self.execute_local_search(query)
            if answer:
                # return a concise answer without opening the browser
                return f"🔎 {query}\n\n{answer}"
            # Fallback to opening web browser search
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return f"🔍 Searching for: {query}"
        except Exception as e:
            return f"✗ Search failed: {e}"
    
    def execute_brightness_control(self, params):
        """Control screen brightness"""
        try:
            # Windows brightness control
            subprocess.run(['powershell', '-Command', 'powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e'], check=False)
            return "💡 Brightness adjusted"
        except Exception as e:
            return f"✗ Brightness control failed: {e}"
    
    def execute_lock_control(self, params):
        """Lock, sleep, or shutdown"""
        action = params.get('action', 'lock').lower()
        
        try:
            if 'lock' in action:
                pyautogui.hotkey('win', 'l')
                return "🔒 Device locked"
            elif 'sleep' in action:
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
                return "😴 Device sleeping"
            elif 'shutdown' in action:
                os.system('shutdown /s /t 30')
                return "⏻ Shutdown initiated (30s)"
        except Exception as e:
            return f"✗ Lock control failed: {e}"
    
    def execute_screenshot(self, params):
        """Take screenshot"""
        try:
            screenshot = pyautogui.screenshot()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            screenshot.save(filename)
            return f"📸 Screenshot saved as {filename}"
        except ImportError:
            return "✗ Pyautogui not installed. Install with: pip install pyautogui"
        except Exception as e:
            return f"✗ Screenshot failed: {e}"
    
    def execute_reminder(self, params):
        """Set reminder (placeholder)"""
        reminder_text = params.get('text', 'Remember this')
        return f"⏰ Reminder set: {reminder_text}"
    
    def execute_time_command(self, params):
        """Get current time and date"""
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"🕐 {current_time}\n📅 {current_date}"
    
    def execute_about(self, params):
        """Return a short description about Aisha (the assistant)"""
        return ("Hi, I'm Aisha — This Desktop's assistant. I can control system volume, \
                open apps, perform quick web searches, set reminders,take screenshots, \
                and what not. Say 'Aisha' followed by your command to get started.")
    
    def handle_unknown(self, params):
        """Handle unknown commands"""
        return "❓ Command not recognized. Try: volume up, open notepad, search python, play music"


# ============================================================================
# AI-POWERED COMMAND PROCESSOR (Ollama)
# ============================================================================
 
def get_brain_output(user_text):
    """Use Ollama to convert natural language to structured command"""
    prompt = f"""You are a command parser for a voice assistant. Convert the user's natural speech to a JSON command.

                AVAILABLE COMMANDS:
                - VOLUME: increase/decrease/mute/set (with level 0-100)
                - MEDIA: play/pause/next/previous
                - APP: open any application
                - SEARCH: web search
                - BRIGHTNESS: adjust brightness
                - LOCK: lock/sleep/shutdown
                - SCREENSHOT: take screenshot
                - REMINDER: set reminder
                - TIME: get current time

                USER SAYS: "{user_text}"

                Return ONLY valid JSON with "intent" and "params" keys. Example:
                {{"intent": "VOLUME", "params": {{"action": "increase"}}}}
            """

    try:
        response = ollama.chat(
            model='qwen3:1.7b',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        return response['message']['content']
    except Exception as e:
        return json.dumps({"intent": "UNKNOWN", "params": {"error": str(e)}})


# ============================================================================
# VOICE RECOGNITION
# ============================================================================
 
def listen():
    """Listen for voice command"""
    r = sr.Recognizer()
    r.energy_threshold = 1000
    r.phrase_time_limit = 7
    r.pause_threshold = 0.7
    
    with sr.Microphone() as source:
        print("\n[STEP 1] 🎤 Listening... (Speak now)")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
     
    try:
        text = r.recognize_google(audio)
        if any(wake_word in text.lower() for wake_word in ["ayesha", "aisha", "aayesha"]):
            print(f"[STEP 2] ✓ Recognized: {text}")
            return text
        else:
            print("[STEP 2] ℹ Wake word not detected")
            return None
    except sr.UnknownValueError:
        print("[STEP 2] ✗ Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"[STEP 2] ✗ API Error: {e}")
        return None
 

# ============================================================================
# MAIN EXECUTION ENGINE
# ============================================================================

def execute_command(user_text):
    """Main command execution pipeline"""
    print("\n" + "="*60)
    print(f"[STEP 3] Processing: {user_text}")
    
    # Step 1: Parse with AI (optional, for complex commands)
    # Uncomment to use Ollama AI parsing
    # ai_response = get_brain_output(user_text)
    # print(f"[STEP 4] AI Response: {ai_response}")
    
    # Step 2: Use rule-based mapper (faster, no AI needed)
    mapper = CommandMapper()
    intent = mapper.extract_intent(user_text)
    params = mapper.extract_params(user_text, intent)
    
    print(f"[STEP 4] Intent: {intent}")
    print(f"[STEP 5] Parameters: {params}")
    
    # Step 3: Execute command
    result = mapper.map_to_function(intent, params)
    print(f"[STEP 6] Result: {result}")
    print("="*60 + "\n")
    
    return result


# ============================================================================
# MAIN LOOP
# ============================================================================
 
def main_loop():
    print("🤖 Voice Assistant Started")
    print("Say 'Ayesha' or 'Aisha' followed by your command\n")
    
    while True:
        try:
            voice_input = listen()
            if voice_input:
                result = execute_command(voice_input)

                # Print result safely (avoid encoding errors on some consoles)
                try:
                    print(f"[RESULT] {result}")
                except Exception:
                    import sys
                    try:
                        safe = result.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
                        print(f"[RESULT] {safe}")
                    except Exception:
                        print("[RESULT] (could not display result due to encoding)")

            # time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Assistant stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main_loop()