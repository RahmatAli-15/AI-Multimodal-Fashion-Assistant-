import os
import logging
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
import base64
import json

load_dotenv()


# -----------------------------------------------------------
# Helper: Convert HEX → Basic Color Names
# -----------------------------------------------------------

def hex_to_color_name(hex_value):
    """Convert hex color values into basic human-friendly names."""
    if not hex_value:
        return None

    # remove "#"
    hex_value = hex_value.replace("#", "")
    if len(hex_value) != 6:
        return None

    try:
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
    except:
        return None

    # Simple rule-based mapping
    if r > 200 and g < 80 and b < 80:
        return "red"
    if r < 80 and g < 80 and b > 150:
        return "blue"
    if r < 80 and g > 150 and b < 80:
        return "green"
    if r > 200 and g > 200 and b < 80:
        return "yellow"
    if r > 200 and g > 200 and b > 200:
        return "white"
    if r < 60 and g < 60 and b < 60:
        return "black"
    if r > 180 and g > 120 and b > 180:
        return "pink"
    if r > 200 and g > 150 and b > 80:
        return "beige"
    if r < 160 and g < 160 and b < 160:
        return "grey"

    return "mixed"


class VisionAgent:
    """
    AI Vision Agent (Gemini 1.5 Flash) — UPGRADED
    - robust JSON extraction
    - skin tone normalization
    - hex → color names
    - guaranteed outfit keywords
    """

    def __init__(self):
        api = os.getenv("GEMINI_API_KEY")
        if not api:
            logging.error("❌ Missing GEMINI_API_KEY in .env")
        genai.configure(api_key=api)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _encode_image(self, image_path: str):
        try:
            with open(image_path, "rb") as f:
                return f.read()
        except Exception as e:
            logging.error(f"[VISION] Cannot read image: {e}")
            return None

    # -----------------------------------------------------------
    # Main Vision Analysis
    # -----------------------------------------------------------
    def analyze(self, image_path: str):
        if not image_path or not os.path.exists(image_path):
            logging.error(f"[VISION] Image not found: {image_path}")
            return {"error": "image_not_found", "image_path": image_path}

        img_bytes = self._encode_image(image_path)
        if img_bytes is None:
            return {"error": "read_failed", "image_path": image_path}

        prompt = """
        You are a professional fashion stylist.
        Analyze the person and return STRICT JSON.

        JSON structure:
        {
            "gender": "male/female/unknown",
            "skin_tone": "cool/warm/neutral",
            "dominant_colors": ["#hex", "#hex", "#hex"],
            "detected_clothes": ["tshirt","shirt","dress","hoodie"],
            "outfit_recommendations": [
                "keyword1",
                "keyword2"
            ]
        }
        Make sure:
        - skin_tone is one of: cool, warm, neutral
        - dominant_colors must be hex values
        - outfit_recommendations must contain 2–5 keywords
        """

        try:
            response = self.model.generate_content(
                [prompt, {"mime_type": "image/jpeg", "data": img_bytes}]
            )
            text = response.text.strip()

            if text.startswith("```"):
                text = text.strip("`").strip()

            data = json.loads(text)

        except Exception:
            logging.exception("[VISION] Gemini failed")
            return {"error": "gemini_failed"}

        # ---------------------------------------------------
        # Clean & Normalize Output
        # ---------------------------------------------------
        gender = (data.get("gender") or "unknown").lower()

        # Normalize skin tone
        raw_tone = (data.get("skin_tone") or "").lower().strip()
        if "cool" in raw_tone:
            skin = "cool"
        elif "warm" in raw_tone:
            skin = "warm"
        elif raw_tone in ["fair", "light"]:
            skin = "cool"
        elif raw_tone in ["medium", "wheatish"]:
            skin = "neutral"
        elif raw_tone in ["dark", "deep"]:
            skin = "warm"
        else:
            skin = "neutral"

        # Convert hex → basic color names
        hex_colors = data.get("dominant_colors", [])
        readable_colors = []
        for hx in hex_colors:
            name = hex_to_color_name(hx)
            if name:
                readable_colors.append(name)

        # fallback if Gemini gives nothing
        if not readable_colors:
            readable_colors = ["blue", "black", "white"]

        # Normalize detected clothes
        clothes = [c.lower() for c in data.get("detected_clothes", [])]

        # Outfit recommendations — always guarantee output
        rec = data.get("outfit_recommendations", [])
        if not rec:
            # Generate guaranteed fallback keywords
            rec = []
            rec.extend(readable_colors[:2])

            if gender == "male":
                rec.extend(["shirt", "tshirt", "jeans"])
            elif gender == "female":
                rec.extend(["dress", "kurti", "top"])

            rec = list(set(rec))

        # Final JSON
        return {
            "image_path": image_path,
            "gender": gender,
            "skin_tone": skin,
            "dominant_colors": readable_colors,
            "detected_clothes": clothes,
            "outfit_recommendations": rec,
        }
