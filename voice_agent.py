# agents/voice_agent.py
import logging
import os

class VoiceAgent:
    """
    Multi-mode Voice Agent
    - main_assistant.py → normal voice output (SAPI / pyttsx3)
    - live.py (Streamlit) → returns audio file for playback
    """

    def __init__(self, debug=False, voice_name=None, streamlit_mode=False):
        self.debug = debug
        self.streamlit_mode = streamlit_mode   # <--- IMPORTANT
        self.engine = None
        self.mode = "none"

        # --------------------------
        # STREAMLIT MODE (file-only)
        # --------------------------
        if self.streamlit_mode:
            self.mode = "file"
            logging.info("[TTS] Streamlit file-output mode enabled")
            return

        # --------------------------
        # WINDOWS SAPI MODE
        # --------------------------
        try:
            import win32com.client as wincl
            self.engine = wincl.Dispatch("SAPI.SpVoice")
            self.mode = "sapi"

            if voice_name:
                for v in self.engine.GetVoices():
                    if voice_name.lower() in v.GetDescription().lower():
                        self.engine.Voice = v
                        break

            logging.info("[TTS] Using Windows SAPI Voice")
            return
        except Exception:
            logging.info("[TTS] SAPI not available → trying pyttsx3")

        # --------------------------
        # PYTTSX3 fallback
        # --------------------------
        try:
            import pyttsx3
            e = pyttsx3.init()

            if voice_name:
                for v in e.getProperty("voices"):
                    if voice_name.lower() in v.name.lower():
                        e.setProperty("voice", v.id)
                        break

            self.engine = e
            self.mode = "pyttsx3"
            logging.info("[TTS] Using pyttsx3 engine")
            return
        except Exception:
            logging.info("[TTS] pyttsx3 not available → final fallback")

        # --------------------------
        # PRINT-only fallback
        # --------------------------
        self.engine = None
        self.mode = "print"


    def speak(self, text):
        if not text:
            return None

        logging.info(f"[TTS] Speak mode: {self.mode}")

        # ------------------------------------------------
        # STREAMLIT: Produce an audio file (for st.audio)
        # ------------------------------------------------
        if self.mode == "file":
            try:
                import pyttsx3
                engine = pyttsx3.init()
                outfile = "tts_output.wav"
                engine.save_to_file(text, outfile)
                engine.runAndWait()
                return outfile      # <--- RETURN PATH FOR STREAMLIT
            except Exception:
                logging.exception("[TTS] File TTS failed → printing")
                print("[AI]:", text)
                return None

        # ------------------------------------------------
        # WINDOWS SAPI
        # ------------------------------------------------
        if self.mode == "sapi" and self.engine:
            try:
                self.engine.Speak(text)
                return None
            except Exception:
                logging.exception("[TTS] SAPI failed → fallback to pyttsx3")

        # ------------------------------------------------
        # PYTTSX3
        # ------------------------------------------------
        if self.mode == "pyttsx3" and self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
                return None
            except Exception:
                logging.exception("[TTS] pyttsx3 failed → print fallback")

        # ------------------------------------------------
        # PRINT fallback
        # ------------------------------------------------
        print("[AI]:", text)
        return None
