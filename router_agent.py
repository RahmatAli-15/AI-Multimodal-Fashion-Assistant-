# agents/router_agent.py
import logging


def route(text: str):
    """
    Improved routing logic:
      - Detects image intent
      - Event detection
      - Trend queries
      - Budget queries
      - Gift queries
      - Region queries (new)
      - Color/style queries (new)
    """
    if not text:
        return "search"

    t = text.lower()

    # ---------------------
    # Vision / Image intent
    # ---------------------
    if any(w in t for w in ["upload image", ".jpg", ".png", "image", "photo", "pic", "selfie"]):
        logging.info("[ROUTER] → vision")
        return "vision"

    # ---------------------
    # Event routing
    # ---------------------
    if any(w in t for w in ["farewell", "wedding", "party", "date", "interview", "birthday"]):
        logging.info("[ROUTER] → event")
        return "event"

    # ---------------------
    # Trend routing
    # ---------------------
    if any(w in t for w in ["trend", "trending", "viral", "fashion trend", "what's trending"]):
        logging.info("[ROUTER] → trend")
        return "trend"

    # ---------------------
    # Budget routing
    # ---------------------
    if any(w in t for w in ["under", "budget", "cheap", "less than", "₹", "rupees", "rs", "affordable"]):
        logging.info("[ROUTER] → budget")
        return "budget"

    # ---------------------
    # Gift routing
    # ---------------------
    if any(w in t for w in ["gift", "present", "surprise", "for him", "for her"]):
        logging.info("[ROUTER] → gift")
        return "gift"

    # ---------------------
    # Region routing (new)
    # ---------------------
    if any(w in t for w in ["delhi", "punjab", "kerala", "mumbai", "bangalore", "north", "south", "east", "west"]):
        logging.info("[ROUTER] → region")
        return "region"

    # ---------------------
    # Color/style preference
    # ---------------------
    if any(w in t for w in ["black", "white", "red", "blue", "oversize", "slim fit", "regular fit"]):
        logging.info("[ROUTER] → search")
        return "search"

    # Default to general search
    logging.info("[ROUTER] → search (default)")
    return "search"
