# agents/speech_agent.py
import logging, os

class SpeechAgent:
    def __init__(self, debug=False):
        self.debug = debug

        # Load Groq STT if available
        try:
            from groq import Groq
            self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        except Exception:
            self.groq = None
            logging.info("[STT] Groq API not available, using fallback STT.")

    # ------------------------------------------------------
    # RECORD AUDIO
    # ------------------------------------------------------
    def record_audio(self, timeout=6, phrase_time_limit=6):
        """
        Attempts to capture microphone audio.
        Falls back to typed input if mic/STT libs aren't installed.
        """
        try:
            import speech_recognition as sr
            r = sr.Recognizer()

            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.6)
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                return audio

        except Exception:
            logging.info("[STT] Microphone not available — typing mode.")
            return None

    # ------------------------------------------------------
    # AUDIO → TEXT
    # ------------------------------------------------------
    def audio_to_text(self, audio):
        """
        Converts captured audio into text using:
            1) Groq Whisper (if available)
            2) Google STT via SpeechRecognition as fallback
        """
        if not audio:
            return None

        # --- GROQ WHISPER STT ---
        if self.groq:
            try:
                import tempfile

                # Save temporary wav
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio.get_wav_data())
                    temp_path = tmp.name

                # Read back file and send to API
                with open(temp_path, "rb") as f:
                    resp = self.groq.audio.transcriptions.create(
                        file=(temp_path, f.read()),
                        model="whisper-large-v3"
                    )

                text = getattr(resp, "text", None)
                if text:
                    return text.strip()

            except Exception:
                logging.exception("[STT] Groq Whisper failed — fallback.")

        # --- SPEECHRECOGNITION FALLBACK ---
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            return r.recognize_google(audio)
        except Exception:
            logging.exception("[STT] Google STT failed.")
            return None