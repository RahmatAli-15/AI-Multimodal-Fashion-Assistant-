# main_assistant.py (single-shot fashion assistant) — FINAL UPDATED VERSION

import os
import json
import logging
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# CLEAN LOGGING SETUP
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("groq").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.ERROR)

# Agents
from agents.speech_agent import SpeechAgent
from agents.voice_agent import VoiceAgent
from agents.router_agent import route
from agents.vision_agent import VisionAgent
from agents.facebody_agent import FaceBodyAgent
from agents.product_search_agent import ProductSearchAgent
from agents.product_recommender_agent import ProductRecommenderAgent
from agents.trend_agent import TrendAgent
from agents.budget_agent import BudgetAgent
from agents.event_agent import EventAgent
from agents.region_agent import RegionAgent
from agents.gift_agent import GiftAgent

ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT, "data")
PRODUCTS_PATH = os.path.join(DATA_DIR, "products.json")
USER_PROFILE_PATH = os.path.join(DATA_DIR, "user_profile.json")
UI_OUTPUT_PATH = os.path.join(DATA_DIR, "ui_output.json")
UI_LOG_PATH = os.path.join(DATA_DIR, "ui_logs.txt")
os.makedirs(DATA_DIR, exist_ok=True)


def load_products(path=PRODUCTS_PATH):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logging.exception("Failed to load products.json")
    logging.warning("Products DB not found or invalid. Create data/products.json")
    return []


def top1_text(item):
    if not item:
        return ""
    title = item.get("title") or item.get("name") or str(item)
    price = item.get("price")
    return f"{title} — ₹{price}" if price else title


def write_ui_output(payload: dict):
    try:
        tmp = UI_OUTPUT_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, UI_OUTPUT_PATH)
    except Exception:
        logging.exception("Failed to write UI output")


def append_ui_log(line: str):
    try:
        ts = datetime.utcnow().isoformat() + "Z"
        with open(UI_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{ts} {line}\n")
    except Exception:
        logging.exception("Failed to append UI log")


class FashionAssistantSingleShot:
    def __init__(self, hybrid=True):
        self.hybrid = hybrid
        self.products = load_products()

        # Core agents
        self.speech = SpeechAgent(debug=False)
        self.voice = VoiceAgent(debug=False)
        self.router = route
        self.vision = VisionAgent()
        self.facebody = FaceBodyAgent()
        self.search = ProductSearchAgent(self.products)
        self.reco = ProductRecommenderAgent(self.products)
        self.trend = TrendAgent(self.products)
        self.budget = BudgetAgent()
        self.event = EventAgent()
        self.region = RegionAgent()
        self.gift = GiftAgent()

        self.stop_words = {"exit", "quit", "stop", "goodbye"}

    def ask_input(self):
        if self.hybrid:
            audio = self.speech.record_audio()
            if audio:
                text = self.speech.audio_to_text(audio)
                if text:
                    logging.info("[USER SAID] %s", text)
                    if text.lower().strip() in self.stop_words:
                        self.voice.speak("Goodbye!")
                        return None
                    return text.strip()

        txt = input("You (text): ").strip()
        if not txt:
            return None
        if txt.lower().strip() in self.stop_words:
            self.voice.speak("Goodbye!")
            return None
        return txt

    def run(self):
        self.voice.speak("Hello! Ask me for outfits, or say 'upload image' to try-on. ")
        user_text = self.ask_input()
        if not user_text:
            return

        logging.info("INPUT: %s", user_text)
        append_ui_log(f"[INPUT] {user_text}")

        route_name = self.router(user_text)
        logging.info("ROUTE: %s", route_name)

        final = []
        note = None
        analysis = {}

        try:
            # ----------------------------------------------------------
            # VISION ROUTE (image → keywords → search)
            # ----------------------------------------------------------
            if route_name == "vision":
                # ask for image
                self.voice.speak("Please enter your image path.")
                img = input("Image path: ").strip()

                # analyze
                analysis = self.facebody.analyze(img)
                append_ui_log(f"[VISION] analyzed {img}")
                logging.debug("[VISION] analysis: %s", analysis)

                # store analysis for second question
                self.last_analysis = analysis

                # Ask user what they want next
                self.voice.speak(
                    "Image uploaded successfully! What would you like to know? "
                )
                print("\n🟦 Image uploaded successfully!")
                print("Now ask anything — e.g., 'farewell outfit', 'casual look', 'jeans under 500', 'wedding suggestions'.\n")

                # Get next user query
                follow_up = self.ask_input()
                if not follow_up:
                    return

                append_ui_log(f"[VISION-FOLLOWUP] {follow_up}")

                # Detect event or just general query
                ev, templates = self.event.detect(follow_up)
                budget_val = self.budget.extract(follow_up)
                region = self.region.detect(follow_up)

                # Build keyword seed from analysis
                base_keywords = analysis.get("outfit_recommendations") or []
                dom = analysis.get("dominant_colors", [])
                for c in dom:
                    base_keywords.append(c)

                # build final query keywords
                query_parts = base_keywords

                # add event templates
                if templates:
                    query_parts += templates

                # add user given words directly
                query_parts += follow_up.lower().split()

                query = " ".join(list(dict.fromkeys(query_parts)))  # unique

                # run final search
                final = self.search.search(
                    keywords=query,
                    budget=budget_val,
                    region=region
                )

                note = f"Vision + query: {follow_up} → {query}"

            # ----------------------------------------------------------
            elif route_name == "event":
                ev, templates = self.event.detect(user_text)
                region = self.region.detect(user_text)
                final = self.search.search(keywords=" ".join(templates), region=region)
                note = f"Event: {ev}"

            elif route_name == "trend":
                region = self.region.detect(user_text)
                final = self.trend.get_trending(region=region, top_k=10)
                note = "Trending items"

            elif route_name == "budget":
                b = self.budget.extract(user_text)
                final = self.search.search(keywords=user_text, budget=b)
                note = f"Budget: ₹{b}"

            elif route_name == "gift":
                who, opts = self.gift.detect(user_text)
                final = self.search.search(keywords=" ".join(opts))
                note = f"Gift ideas for {who}"

            # ----------------------------------------------------------
            # GENERIC SEARCH ROUTE
            # ----------------------------------------------------------
            else:
                region = self.region.detect(user_text)
                b_val = self.budget.extract(user_text)
                s = self.search.search(keywords=user_text, budget=b_val, region=region)

                final = self.reco.rank(
                    s,
                    context={"user_text": user_text, "region": region, "budget": b_val}
                )
                note = "Search results"

        except Exception:
            logging.exception("Processing failed")
            append_ui_log("[ERROR] Processing failed")
            final = []

        # Speak top result
        top_item = final[0] if final else None
        spoken = top1_text(top_item) if top_item else "Sorry, I couldn't find a recommendation."
        self.voice.speak(spoken)

        # UI results
        results_for_ui = []
        for p in final:
            img = p.get("image_path") or ""
            results_for_ui.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "price": p.get("price"),
                "tags": p.get("tags", []),
                "colors": p.get("colors", []),
                "image_path": img,
                "popularity": p.get("popularity"),
                "rating": p.get("rating")
            })

        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_text": user_text,
            "route": route_name,
            "note": note,
            "analysis": analysis,
            "results": results_for_ui
        }

        write_ui_output(payload)
        append_ui_log(f"[OUTPUT] {note or 'results'} ({len(results_for_ui)} items)")

        # Terminal Output
        def short_link(path):
            if not path:
                return "No image"
            return path[:20] + ".../" + path[-12:] if len(path) > 45 else path

        print("\n" + "-"*45)
        print("            FASHION ASSISTANT REPORT")
        print("-"*45)
        print(f"User Request      : {user_text}")
        print(f"Image Analyzed    : {analysis.get('image_path', 'N/A')}")
        print(f"Skin Tone         : {analysis.get('skin_tone', 'N/A')}")
        dom = ", ".join(analysis.get("dominant_colors", [])[:3])
        print(f"Dominant Colors   : {dom}")

        print("\nRecommended Colors Based on Analysis:")
        for rec in (analysis.get("outfit_recommendations") or []):
            print("→", rec)

        print("\nTop Outfit Suggestions:")
        top10 = final[:10]
        if not top10:
            print("No items found.")
        else:
            for i, item in enumerate(top10, start=1):
                title = item.get("title", "item")
                price = item.get("price", "NA")
                tags = ", ".join(item.get("tags", []))
                img = short_link(item.get("image_path", ""))
                print(f"\n{i}) {title} — ₹{price}")
                print(f"    Tags : {tags}")
                print(f"    Image: [CLICK TO VIEW] → {img}")

        print("\n" + "-"*45)
        print("          THANK YOU FOR USING F.A.I.")
        print("-"*45 + "\n")

        return payload


if __name__ == "__main__":
    FashionAssistantSingleShot(hybrid=True).run()



#C:/Users/Lenovo/Desktop/Ecommerce/images/ab.jpg 
#C:/Users/Lenovo/Desktop/Ecommerce/images/ab.jpeg