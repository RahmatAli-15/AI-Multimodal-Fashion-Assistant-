import logging

# Canonical event search templates mapped to your dataset fields
EVENT_MAP = {
    "farewell": ["dress", "satin", "blazer", "partywear", "western"],
    "wedding": ["wedding", "lehenga", "sherwani", "ethnic", "traditional"],
    "engagement": ["engagement", "gown", "sherwani", "ethnic"],
    "haldi": ["yellow", "ethnic", "kurta", "lehenga"],
    "mehendi": ["green", "lehenga", "ethnic"],
    "reception": ["gown", "ethnic", "partywear"],
    "party": ["party", "shimmer", "jumpsuit", "co-ord", "club"],
    "birthday": ["party", "casual", "dress"],
    "interview": ["formal", "shirt", "trousers", "blazer"],
    "office": ["formal", "office", "shirt", "blazer"],
    "date": ["casual", "dress", "shirt", "chinos"],
    "gym": ["sports", "activewear", "tshirt", "trackpants"],
    "festival": ["ethnic", "traditional", "kurta"],
    "casual": ["casual", "tshirt", "jeans"],
}

# Fuzzy keyword mapping (extended)
FUZZY_KEYWORD_MAP = {
    "farewell": "farewell",
    "goodbye": "farewell",
    "college farewell": "farewell",
    "office farewell": "farewell",

    "marriage": "wedding",
    "shaadi": "wedding",
    "shadi": "wedding",
    "wedding ceremony": "wedding",
    "sagai": "engagement",
    "engagement": "engagement",
    "ring ceremony": "engagement",
    "haldi": "haldi",
    "mehendi": "mehendi",
    "mehndi": "mehendi",
    "reception": "reception",

    "party": "party",
    "club": "party",
    "nightout": "party",
    "birthday": "birthday",
    "bday": "birthday",

    "interview": "interview",
    "job": "interview",
    "formal": "interview",
    "office": "office",
    "work": "office",

    "date": "date",
    "dating": "date",

    "gym": "gym",
    "workout": "gym",
    "fitness": "gym",

    "festival": "festival",
    "ethnic day": "festival",

    "casual": "casual",
    "regular": "casual",
}


class EventAgent:
    def detect(self, text):
        """
        Detects user's event intent and returns:
        - event name (str)
        - recommended search templates (list)
        """
        if not text:
            return None, []

        t = text.lower().strip()

        # ---------------------------------------------
        # 1) DIRECT EVENT MATCH
        # ---------------------------------------------
        for ev in EVENT_MAP:
            if ev in t:
                logging.info(f"[EVENT] direct match: {ev}")
                return ev, EVENT_MAP[ev]

        # ---------------------------------------------
        # 2) FUZZY KEYWORD MATCH
        # ---------------------------------------------
        for key, ev in FUZZY_KEYWORD_MAP.items():
            if key in t:
                logging.info(f"[EVENT] fuzzy match: {key} → {ev}")
                return ev, EVENT_MAP.get(ev, [])

        # ---------------------------------------------
        # 3) PATTERN-BASED LOGICAL GUESS (fallback)
        # ---------------------------------------------
        if "dress" in t:
            logging.info("[EVENT] fallback guess → party")
            return "party", EVENT_MAP["party"]

        if "ethnic" in t or "kurta" in t or "lehenga" in t:
            logging.info("[EVENT] fallback guess → festival")
            return "festival", EVENT_MAP["festival"]

        if "blazer" in t or "formal" in t:
            logging.info("[EVENT] fallback guess → interview")
            return "interview", EVENT_MAP["interview"]

        logging.info("[EVENT] no match")
        return None, []
