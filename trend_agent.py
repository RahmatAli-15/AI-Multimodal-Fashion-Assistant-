import logging

class TrendAgent:
    """
    Ultra-optimized Trend Agent
    - Uses global + seasonal + event + region trends
    - Auto-extracts trends from product dataset (viral, trending, popularity)
    - Multi-keyword fuzzy matching
    - Dataset-aware (tags, style, category, occasion)
    """

    GLOBAL = {
        # Fashion-wide viral items
        "viral": [
            "oversized hoodie", "co-ord set", "chunky sneakers",
            "plaid skirt", "baggy jeans", "oversized tee"
        ],

        # Seasonal trends
        "winter": ["puffer jacket", "turtleneck", "long coat", "sweatshirt"],
        "summer": ["cotton dress", "shorts", "linen shirt", "tank top"],
        "monsoon": ["windcheater", "quick dry", "waterproof jacket"],

        # Event-based trends (works with your EventAgent)
        "farewell": ["bodycon dress", "satin gown", "blazer"],
        "wedding": ["lehenga", "sherwani", "ethnic wear", "gown"],
        "haldi": ["yellow kurta", "yellow lehenga", "ethnic"],
        "mehendi": ["green kurta", "green lehenga", "ethnic"],
        "party": ["shimmer", "jumpsuit", "co-ord", "clubwear"],
        "casual": ["tshirt", "hoodie", "shirt", "jeans"],

        # Region-specific preferences
        "north": ["hoodie", "puffer jacket", "kurtas", "ethnic wear"],
        "south": ["linen shirt", "cotton kurta", "lightweight tee"],
        "mumbai": ["oversized tee", "cargo pants", "sneakers"],
        "blr": ["co-ord set", "techwear jacket", "minimal sneakers"],
        "metro": ["oversized", "streetwear", "baggy"],
        "east": ["windcheater", "printed kurti", "sneakers"],
        "west": ["denim jacket", "kurti", "pastel tees"],
    }

    def __init__(self, products=None):
        self.products = products or []

    # --------------------------------------------------
    # INTERNAL: Extract searchable blob from product
    # --------------------------------------------------
    def _blob(self, p):
        parts = [
            p.get("title", ""),
            p.get("category", ""),
            p.get("style", ""),
            p.get("material", ""),
            p.get("gender", "")
        ]
        parts.extend(p.get("tags", []))
        parts.extend(p.get("colors", []))

        occ = p.get("occasion")
        if isinstance(occ, str):
            parts.append(occ)
        elif isinstance(occ, list):
            parts.extend(occ)

        return " ".join(parts).lower()

    # --------------------------------------------------
    # INTERNAL: multi-keyword fuzzy match
    # --------------------------------------------------
    def _multi_match(self, product, keywords):
        blob = self._blob(product)

        score = 0
        for kw in keywords:
            kw = kw.lower()
            if kw in blob:
                score += 1
            else:
                # fuzzy: partial match
                words = kw.split()
                if any(w in blob for w in words):
                    score += 0.5
        return score

    # --------------------------------------------------
    # TREND DETECTION
    # --------------------------------------------------
    def get_trending(self, region=None, event=None, top_k=10):
        logging.info("[TREND] Fetching trending items")

        region = (region or "").lower()
        event = (event or "").lower()

        trend_keywords = []

        # --------------------------------------------------
        # 1) Region-based trends
        # --------------------------------------------------
        if region in self.GLOBAL:
            trend_keywords += self.GLOBAL[region]

        # metros share similar streetwear/modern trends
        if region == "metro":
            trend_keywords += self.GLOBAL.get("metro", [])

        # --------------------------------------------------
        # 2) Event-based trends
        # --------------------------------------------------
        if event in self.GLOBAL:
            trend_keywords += self.GLOBAL[event]

        # --------------------------------------------------
        # 3) Always include global viral trends
        # --------------------------------------------------
        trend_keywords += self.GLOBAL.get("viral", [])

        # --------------------------------------------------
        # 4) Score matching products
        # --------------------------------------------------
        scored = []
        for p in self.products:
            s = self._multi_match(p, trend_keywords)

            # Viral tag boost
            tags = " ".join(p.get("tags", [])).lower()
            if "trending" in tags or "viral" in tags:
                s += 2

            # Popularity boost
            popularity = p.get("popularity", 0)
            if popularity > 85:
                s += 2

            # Rating boost
            if p.get("rating", 0) >= 4.5:
                s += 1.5

            scored.append((s, p))

        # --------------------------------------------------
        # 5) Sort best-first
        # --------------------------------------------------
        scored.sort(key=lambda x: x[0], reverse=True)

        # --------------------------------------------------
        # 6) Return top-k unique items
        # --------------------------------------------------
        uniq = []
        seen = set()

        for _, p in scored:
            pid = p.get("id") or id(p)
            if pid not in seen:
                uniq.append(p)
                seen.add(pid)
            if len(uniq) >= top_k:
                break

        return uniq
