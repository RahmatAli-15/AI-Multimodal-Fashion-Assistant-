import logging

class ProductRecommenderAgent:
    """
    Final AI-grade recommender:
    Combines:
      - OutfitScoreAgent concepts (color harmony, trend, rating)
      - EventAgent (occasion match)
      - RegionAgent (soft boost)
      - BudgetAgent (budget fit)
      - Keyword relevance
      - User preferred colors
      - Popularity + rating core score

    Outputs the *best ranked* products for the UI.
    """

    def __init__(self, products):
        self.products = products or []

    def rank(self, candidates, context=None):
        if not candidates:
            return []

        ctx = context or {}

        budget = ctx.get("budget")
        region = (ctx.get("region") or "").lower()
        user_text = (ctx.get("user_text") or "").lower()
        event = (ctx.get("event") or "").lower()
        outfit_templates = [t.lower() for t in ctx.get("outfit_recommendations", [])]

        preferred_colors = [
            c.lower() for c in ctx.get("preferred_colors", [])
        ]

        analysis = ctx.get("analysis", {}) or {}
        dominant_colors = [
            c.lower() for c in analysis.get("dominant_colors", [])
        ]
        skin = (analysis.get("skin_tone") or "").lower()

        key_words = user_text.split()

        warm_palette = ["beige", "brown", "olive", "maroon", "rust", "mustard"]
        cool_palette = ["blue", "grey", "black", "white", "navy", "silver"]

        # --------------------------------------------------
        # INTERNAL SCORING FUNCTION
        # --------------------------------------------------
        def score(p):
            s = 0

            title = p.get("title", "").lower()
            category = (p.get("category") or "").lower()
            style = (p.get("style") or "").lower()
            tags_list = [t.lower() for t in p.get("tags", [])]
            tags = " ".join(tags_list)
            colors = [c.lower() for c in p.get("colors", [])]
            price = p.get("price")
            gender = (p.get("gender") or "").lower()

            # -------------------------------------
            # 1) Popularity + Rating (Core Weight)
            # -------------------------------------
            s += int(p.get("popularity", 0))
            s += int(p.get("rating", 0) * 10)

            # -------------------------------------
            # 2) Budget Fit
            # -------------------------------------
            if budget and price:
                if price <= budget:
                    s += 25
                else:
                    s -= 20

            # -------------------------------------
            # 3) REGION Soft Match
            # -------------------------------------
            if region and region in tags:
                s += 10

            # -------------------------------------
            # 4) Keyword Relevance (user_text)
            # -------------------------------------
            for w in key_words:
                if w in title or w in tags or w in category:
                    s += 6
                if w in style:
                    s += 4

            # -------------------------------------
            # 5) EVENT / Outfit Template Match
            # -------------------------------------
            if event:
                # occasion match
                occ = p.get("occasion") or []
                if isinstance(occ, str):
                    occ = [occ]
                occ = [o.lower() for o in occ]

                if event in occ:
                    s += 15
                elif event in title or event in tags or event in category:
                    s += 10

            # Outfit templates (from EventAgent or FaceBodyAgent)
            for ot in outfit_templates:
                if ot in title or ot in tags or ot in category:
                    s += 12
                    break

            # -------------------------------------
            # 6) Color Match
            # -------------------------------------
            # Preferred by user
            for pc in preferred_colors:
                if pc in colors or pc in title:
                    s += 10
                    break

            # Dominant image colors
            for dc in dominant_colors:
                if dc in colors:
                    s += 7
                    break

            # -------------------------------------
            # 7) SKIN TONE Matching
            # -------------------------------------
            if skin:
                if skin in ["warm", "tan", "medium warm"]:
                    if any(c in colors for c in warm_palette):
                        s += 8
                elif skin in ["cool", "fair", "light cool"]:
                    if any(c in colors for c in cool_palette):
                        s += 8

            # -------------------------------------
            # 8) Gender Alignment (from analysis)
            # -------------------------------------
            if analysis.get("gender"):
                user_gender = analysis["gender"].lower()
                if gender == user_gender:
                    s += 8
                else:
                    s -= 6

            # -------------------------------------
            # 9) Trendiness Boost
            # -------------------------------------
            if "viral" in tags_list or "trending" in tags_list:
                s += 10

            # -------------------------------------
            # 10) More Tags → More Versatile
            # -------------------------------------
            if len(tags_list) >= 4:
                s += 5

            # -------------------------------------
            # FINAL SCORE
            # -------------------------------------
            return s

        # --------------------------------------------------
        # RANKING: highest score first
        # --------------------------------------------------
        ranked = sorted(candidates, key=lambda p: score(p), reverse=True)

        return ranked
