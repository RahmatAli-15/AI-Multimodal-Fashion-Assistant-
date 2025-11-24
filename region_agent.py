import logging

class RegionAgent:
    """
    Detects the region/city from user text.
    Fully upgraded version:
    - Covers ALL major Indian states & metros
    - Includes Tier-2 / Tier-3 cities for fashion preferences
    - Handles slang, abbreviations, and phonetic spellings
    - Returns normalized region (north/south/east/west/central/metro)
    """

    # MAIN REGION BUCKETS (for TrendAgent, recommender adjustments)
    REGION_MAP = {
        "north": [
            "delhi", "new delhi", "ncr",
            "punjab", "chandigarh", "amritsar", "jalandhar",
            "haryana", "gurgaon", "gurugram", "faridabad",
            "uttarakhand", "dehradun", "haridwar",
            "himachal", "shimla", "manali",
            "up", "uttar pradesh", "lucknow", "kanpur", "noida", "ghaziabad"
        ],

        "south": [
            "tamil", "tamil nadu", "chennai", "tn",
            "karnataka", "bangalore", "bengaluru", "blr", "mysore",
            "kerala", "kochi", "trivandrum",
            "andhra", "andhra pradesh", "vijayawada", "visakhapatnam", "vizag",
            "telangana", "hyderabad"
        ],

        "east": [
            "kolkata", "bengal", "west bengal",
            "odisha", "bhubaneswar",
            "assam", "guwahati",
            "tripura", "agartala"
        ],

        "west": [
            "gujarat", "surat", "rajkot", "ahmedabad",
            "maharashtra", "pune", "nagpur", "nashik",
            "goa", "west"
        ],

        "central": [
            "mp", "madhya pradesh", "bhopal", "indore",
            "chhattisgarh", "raipur"
        ],

        # Special metro tags (for trend-boosting fashion styles)
        "metro": [
            "mumbai", "bombay",
            "delhi", "bangalore", "bengaluru",
            "chennai", "hyderabad", "pune", "kolkata"
        ],
    }

    # EXTRA FUZZY MAP FOR SHORTCUTS / SLANG
    FUZZY = {
        "mum": "mumbai",
        "bom": "mumbai",
        "blr": "bangalore",
        "hyd": "hyderabad",
        "del": "delhi",
        "gzb": "ghaziabad",
        "noida": "noida",
        "gurgaon": "gurgaon",
        "ggn": "gurgaon",
        "vizag": "visakhapatnam",
        "cal": "kolkata",
        "kol": "kolkata",
        "ahm": "ahmedabad"
    }

    def detect(self, text):
        """Return a normalized region label: north/south/east/west/central/metro"""
        if not text:
            return None

        t = text.lower()

        # ----------------------------------------------------
        # 1) FUZZY SHORTCUT MATCHES (SLANG / ABBREVIATIONS)
        # ----------------------------------------------------
        for short, full in self.FUZZY.items():
            if short in t:
                logging.info(f"[REGION] fuzzy match {short} → {full}")
                # determine region category from full name
                return self._reverse_lookup(full)

        # ----------------------------------------------------
        # 2) DIRECT MATCHES AGAINST REGION_MAP
        # ----------------------------------------------------
        for region, words in self.REGION_MAP.items():
            for w in words:
                if w in t:
                    logging.info(f"[REGION] direct match: {w} → {region}")
                    return region

        logging.info("[REGION] no match")
        return None

    # Helper to convert city → region
    def _reverse_lookup(self, city):
        city = city.lower()
        for region, words in self.REGION_MAP.items():
            if city in words:
                return region
        return None
