import logging

# Canonical gift suggestion templates (aligned with your product fields)
GIFT_MAP = {
    "girl": ["women", "women's", "female", "earrings", "handbag", "bracelet", "beauty", "cute"],
    "boy": ["men", "male", "watch", "wallet", "perfume", "shoes", "sneakers"],
    "mom": ["women", "ethnic", "saree", "kurti", "jewellery", "handbag"],
    "dad": ["men", "formal", "shirt", "belt", "smartwatch", "formal shoes"],
    "friend_female": ["women", "casual", "handbag", "bracelet", "dress"],
    "friend_male": ["men", "casual", "hoodie", "watch", "wallet"],
    "friend": ["gift", "unisex", "hoodie", "perfume", "accessory"],
    "sister": ["women", "earrings", "kurti", "bracelet", "cute gifts"],
    "brother": ["men", "tshirt", "hoodie", "wallet", "shoes"],
    "wife": ["women", "dress", "jewellery", "gown", "handbag"],
    "husband": ["men", "watch", "shirt", "wallet"],
}

# Fuzzy keyword mapping (big vocabulary)
FUZZY_MAP = {
    "girlfriend": "girl",
    "gf": "girl",
    "gurl": "girl",

    "boyfriend": "boy",
    "bf": "boy",

    "mom": "mom",
    "mother": "mom",
    "mumma": "mom",
    "amma": "mom",

    "dad": "dad",
    "father": "dad",
    "papa": "dad",

    "sis": "sister",
    "sister": "sister",
    "didi": "sister",

    "bro": "brother",
    "bhai": "brother",
    "brother": "brother",

    "wife": "wife",
    "wifey": "wife",

    "husband": "husband",
    "hubby": "husband",

    "female friend": "friend_female",
    "male friend": "friend_male",
    "bestie": "friend",
    "friend": "friend",

    "parents": "mom",      # fallback to female gifts
    "family": "friend",    # neutral fallback
}


class GiftAgent:
    def detect(self, text):
        """
        Detect intended gift recipient and return:
        - mapped recipient category (str)
        - search-friendly keyword templates (list)
        """
        if not text:
            return None, []

        t = text.lower().strip()

        # ------------------------------------------------------
        # 1) Direct keyword matches ("girl", "boy", "mom", etc.)
        # ------------------------------------------------------
        for key in GIFT_MAP:
            if key in t:
                logging.info(f"[GIFT] direct match: {key}")
                return key, GIFT_MAP[key]

        # ------------------------------------------------------
        # 2) Fuzzy keyword mapping ("gf", "sis", "bestie", etc.)
        # ------------------------------------------------------
        for word, mapped in FUZZY_MAP.items():
            if word in t:
                logging.info(f"[GIFT] fuzzy match: {word} → {mapped}")
                return mapped, GIFT_MAP.get(mapped, [])

        # ------------------------------------------------------
        # 3) Heuristic fallback
        # ------------------------------------------------------
        if "her" in t:
            logging.info("[GIFT] fallback → girl")
            return "girl", GIFT_MAP["girl"]

        if "him" in t:
            logging.info("[GIFT] fallback → boy")
            return "boy", GIFT_MAP["boy"]

        logging.info("[GIFT] no match")
        return None, []
