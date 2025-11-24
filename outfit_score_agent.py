import logging

class OutfitScoreAgent:
    """
    Scores outfits (1–100) using improved dataset-aware smart logic:
      - Color harmony (preferred + dominant image colors)
      - Skin tone match
      - Style match (new)
      - Occasion match (new)
      - Gender match (new)
      - Trendiness (tags + popularity)
      - Rating boost
      - Budget fit
      - Versatility score
    """

    def __init__(self):
        pass

    def score(self, product, analysis, preferred_colors=None, budget=None, event=None):
        score = 50  # base score

        title = product.get("title", "").lower()
        tags  = [t.lower() for t in product.get("tags", [])]
        prod_colors = [c.lower() for c in product.get("colors", [])]

        style = (product.get("style") or "").lower()
        occasion = (product.get("occasion") or "")
        if isinstance(occasion, str):
            occasion = [occasion]
        occasion = [o.lower() for o in occasion]

        gender = (product.get("gender") or "").lower()

        dom_colors = [d.lower() for d in analysis.get("dominant_colors", [])]
        skin = (analysis.get("skin_tone") or "").lower()

        # ------------------------------------------------
        # 1) Preferred color match boost
        # ------------------------------------------------
        if preferred_colors:
            for c in preferred_colors:
                c = c.lower()
                if c in prod_colors or c in title or c in tags:
                    score += 15
                    break

        # ------------------------------------------------
        # 2) Image dominant color match
        # ------------------------------------------------
        for dc in dom_colors:
            if dc in prod_colors:
                score += 12
                break

        # ------------------------------------------------
        # 3) Skin tone harmony scoring
        # ------------------------------------------------
        warm_palette = ["beige", "brown", "olive", "maroon", "rust", "mustard"]
        cool_palette = ["blue", "grey", "black", "white", "navy", "silver"]

        if skin:
            if skin in ["warm", "tan", "medium warm"]:
                if any(c in prod_colors for c in warm_palette):
                    score += 10
            elif skin in ["cool", "fair", "light cool"]:
                if any(c in prod_colors for c in cool_palette):
                    score += 10

        # ------------------------------------------------
        # 4) EVENT-based scoring (BIG IMPROVEMENT)
        # ------------------------------------------------
        if event:
            e = event.lower()
            if e in occasion:        # perfect match
                score += 15
            else:
                # partial match based on tags / category / style
                if e in tags or e in title or e in style:
                    score += 10

        # ------------------------------------------------
        # 5) Gender alignment (helps accuracy)
        # ------------------------------------------------
        if analysis.get("gender"):
            user_gender = analysis["gender"].lower()
            if gender == user_gender:
                score += 10
            else:
                score -= 10

        # ------------------------------------------------
        # 6) Trendiness (tags + popularity)
        # ------------------------------------------------
        popularity = product.get("popularity", 0)
        if "viral" in tags or "trending" in tags or popularity > 80:
            score += 10

        # ------------------------------------------------
        # 7) Rating boost
        # ------------------------------------------------
        rating = product.get("rating", 0)
        if rating >= 4.5:
            score += 8
        elif rating >= 4.0:
            score += 5

        # ------------------------------------------------
        # 8) Budget fit
        # ------------------------------------------------
        price = product.get("price")
        if budget and price:
            if price <= budget:
                score += 10
            else:
                score -= 12

        # ------------------------------------------------
        # 9) Versatility — more tags = better match
        # ------------------------------------------------
        if len(tags) >= 4:
            score += 6
        elif len(tags) >= 2:
            score += 3

        # ------------------------------------------------
        # 10) Style match (simple boost)
        # ------------------------------------------------
        if style in ["classic", "modern", "minimal"]:
            score += 4

        # ------------------------------------------------
        # FINAL: clamp 1–100
        # ------------------------------------------------
        score = max(1, min(100, score))

        logging.debug(f"[OUTFIT SCORE] {product.get('title')} → {score}")
        return score


    def rank_products(self, products, analysis, preferred_colors=None, budget=None, event=None):
        scored = []
        for p in products:
            s = self.score(p, analysis, preferred_colors, budget, event)
            scored.append((s, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for s, p in scored]
