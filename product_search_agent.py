import logging
import re

class ProductSearchAgent:
    """
    AI-like product search engine.
    Supports:
      - natural text keywords
      - EventAgent templates
      - GiftAgent templates
      - category / tags / style / colors / material / gender / occasion
      - budget filtering
      - color filtering
      - fit filtering
      - preferred style matching
      - region soft boosting
    """

    def __init__(self, products):
        self.products = products or []

    # ----------------------------------------------------------
    # Build a search blob for each product
    # ----------------------------------------------------------
    def _product_blob(self, p):
        parts = [
            p.get("title", ""),
            p.get("category", ""),
            p.get("material", ""),
            p.get("style", ""),
            p.get("gender", ""),
        ]

        # tags
        parts.extend(p.get("tags", []) or [])

        # colors
        parts.extend(p.get("colors", []) or [])

        # occasion
        occ = p.get("occasion")
        if isinstance(occ, str):
            parts.append(occ)
        elif isinstance(occ, list):
            parts.extend(occ)

        blob = " ".join(parts).lower()
        return blob

    # ----------------------------------------------------------
    # Keyword match (multi-keyword, fuzzy)
    # ----------------------------------------------------------
    def _keyword_match(self, product, keywords):
        if not keywords:
            return True

        blob = self._product_blob(product)
        k = keywords.lower().strip()

        # Exact
        if k in blob:
            return True

        # Word-by-word fuzzy
        for w in k.split():
            if w in blob:
                return True

        return False

    # ----------------------------------------------------------
    # MAIN SEARCH FUNCTION
    # ----------------------------------------------------------
    def search(self, keywords="", budget=None, region=None, color=None, fit=None, preferred=None):
        logging.info("[SEARCH_AGENT] Running enhanced search")

        k = (keywords or "").lower().strip()
        key_words = k.split() if k else []

        region = (region or "").lower().strip() or None
        color = (color or "").lower().strip()
        preferred = (preferred or "").lower().strip()
        fit = (fit or "").lower().strip()

        matched = []

        for p in self.products:
            blob = self._product_blob(p)
            price = p.get("price")

            # ------------------------------------------
            # Budget Filter
            # ------------------------------------------
            if budget and price and price > budget:
                continue

            # ------------------------------------------
            # Keyword match
            # ------------------------------------------
            if k and not self._keyword_match(p, k):
                continue

            # ------------------------------------------
            # Color filter
            # ------------------------------------------
            if color:
                prod_colors = [c.lower() for c in p.get("colors", [])]
                if color not in prod_colors and color not in blob:
                    continue

            # ------------------------------------------
            # Fit filter (slim / casual / regular etc.)
            # ------------------------------------------
            if fit and fit not in blob:
                continue

            # ------------------------------------------
            # Preferred style (minimal, classic, modern…)
            # ------------------------------------------
            if preferred and preferred not in blob:
                continue

            matched.append(p)

        # -----------------------------------------------------
        # Scoring & Ranking Logic
        # -----------------------------------------------------
        def relevance_score(p, reg=region):
            blob = self._product_blob(p)
            score = 0

            # Keyword relevance
            for w in key_words:
                if w in blob:
                    score += 1

            # Region soft boost
            if reg:
                if reg in blob:
                    score += 1

            return score

        # FINAL SORT ORDER:
        #   1) relevance score
        #   2) popularity desc
        #   3) rating desc
        #   4) price asc
        matched.sort(
            key=lambda x: (
                -relevance_score(x),
                -x.get("popularity", 0),
                -x.get("rating", 0),
                x.get("price", 999999)
            )
        )

        return matched
