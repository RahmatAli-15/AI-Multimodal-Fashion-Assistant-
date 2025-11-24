import logging
import os
from PIL import Image
import numpy as np
from transformers import BlipProcessor, BlipForConditionalGeneration


class FaceBodyAgent:
    def __init__(self):
        """
        Loads BLIP for offline vision captioning.
        Includes optional GROK Vision API.
        """
        try:
            self.processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            logging.info("[BLIP] Loaded successfully")
        except Exception:
            logging.exception("[BLIP] failed to load. Using fallback only.")
            self.model = None

        self.use_grok = False

    # ----------------------------------------------------
    # Better color detection
    # ----------------------------------------------------
    def _extract_dominant_colors(self, img):
        img = img.resize((30, 30))
        arr = np.array(img).reshape(-1, 3)
        avg = arr.mean(axis=0)
        r, g, b = avg

        # Neutral / dark logic
        brightness = (r + g + b) / 3

        if brightness < 60:
            return ["black", "dark"]
        if brightness < 120:
            return ["grey", "neutral"]

        # Hue-based logic
        if r > g and r > b:
            return ["red", "warm"]
        if g > r and g > b:
            return ["green", "cool"]
        if b > r and b > g:
            return ["blue", "cool"]

        return ["light", "neutral"]

    # ----------------------------------------------------
    # Heuristic skin tone estimate
    # ----------------------------------------------------
    def _estimate_skin_tone(self, img):
        arr = np.array(img.resize((20, 20))).reshape(-1, 3)
        avg = arr.mean(axis=0)
        r, g, b = avg

        if r > g and r > b:
            if r < 120:
                return "dark"
            elif r < 160:
                return "medium"
            else:
                return "wheatish"
        else:
            return "fair"

    # ----------------------------------------------------
    # Caption-based gender detection
    # ----------------------------------------------------
    def _detect_gender(self, caption):
        text = caption.lower()

        female_keywords = ["woman", "lady", "girl", "female", "lehenga", "dress", "kurti", "saree"]
        male_keywords = ["man", "boy", "male", "shirt", "blazer", "suit", "kurta"]

        if any(w in text for w in female_keywords):
            return "female"
        if any(w in text for w in male_keywords):
            return "male"
        return "unknown"

    # ----------------------------------------------------
    # Clothing keyword extraction
    # ----------------------------------------------------
    def _extract_clothing(self, caption):
        clothing_keywords = []
        possible = [
            "shirt", "dress", "kurti", "saree", "hoodie", "jacket", "top", "skirt",
            "pants", "jeans", "suit", "blazer", "tshirt", "lehenga", "formals"
        ]

        for w in possible:
            if w in caption.lower():
                clothing_keywords.append(w)

        return clothing_keywords

    # ----------------------------------------------------
    # Build strong outfit recommendations
    # ----------------------------------------------------
    def _build_recommendations(self, dom_colors, gender, clothing):
        rec = []

        if "blue" in dom_colors:
            rec += ["blue", "navy", "grey", "black"]
        if "red" in dom_colors:
            rec += ["maroon", "beige", "brown"]
        if "green" in dom_colors:
            rec += ["olive", "white", "black"]

        if gender == "male":
            rec += ["shirt", "tshirt", "jeans", "blazer", "casual"]
        if gender == "female":
            rec += ["dress", "kurti", "top", "jeans", "casual"]

        for c in clothing:
            rec.append(c)

        # De-duplicate
        final = list(dict.fromkeys(rec))

        # Very strong minimal fallback
        if not final:
            final = ["casual", "shirt", "jeans", "dress"]

        return final

    # ----------------------------------------------------
    # Main analysis
    # ----------------------------------------------------
    def analyze(self, image_path: str):
        if not image_path or not os.path.exists(image_path):
            logging.error(f"[FACEBODY] Image not found: {image_path}")
            return self._empty_response(image_path)

        img = Image.open(image_path).convert("RGB")

        # 1) BLIP caption
        if not self.model:
            return self._fallback(img, image_path)

        try:
            inputs = self.processor(img, return_tensors="pt")
            caption_ids = self.model.generate(**inputs)
            caption = self.processor.decode(caption_ids[0], skip_special_tokens=True)
        except Exception:
            logging.exception("[BLIP] Failed generating caption")
            return self._fallback(img, image_path)

        # 2) Parse attributes
        dom_colors = self._extract_dominant_colors(img)
        skin_tone = self._estimate_skin_tone(img)
        gender = self._detect_gender(caption)
        clothing = self._extract_clothing(caption)
        recommendations = self._build_recommendations(dom_colors, gender, clothing)

        return {
            "image_path": image_path,
            "dominant_colors": dom_colors,
            "skin_tone": skin_tone,
            "gender": gender,
            "clothing_keywords": clothing,
            "outfit_recommendations": recommendations,
            "raw": {
                "caption": caption,
                "colors": dom_colors,
                "clothing": clothing
            }
        }

    # ----------------------------------------------------
    # Fallback (BLIP missing)
    # ----------------------------------------------------
    def _fallback(self, img, image_path):
        dom_colors = self._extract_dominant_colors(img)
        skin = self._estimate_skin_tone(img)
        return {
            "image_path": image_path,
            "dominant_colors": dom_colors,
            "skin_tone": skin,
            "gender": "unknown",
            "clothing_keywords": [],
            "outfit_recommendations": [],
            "raw": {"info": "BLIP not available"}
        }

    # ----------------------------------------------------
    # Empty error
    # ----------------------------------------------------
    def _empty_response(self, path):
        return {
            "image_path": path,
            "dominant_colors": [],
            "skin_tone": None,
            "gender": "unknown",
            "clothing_keywords": [],
            "outfit_recommendations": [],
            "raw": {}
        }
