import re
import logging

class BudgetAgent:
    """
    Budget extraction agent.
    Supports:
    - ₹, Rs, INR, $, “k”, “thousand”
    - Ranges: 500-1500, 700 to 1200
    - Spoken formats: '2k', '5 thousand'
    - Keywords: cheap, affordable, low budget
    """

    def extract(self, text):
        if not text:
            return None

        t = text.lower().strip()

        # -----------------------------------------
        # 1) RANGE extraction
        # -----------------------------------------
        # e.g.: "500-1500", "600 to 1200", "700 upto 900"
        range_match = re.search(r"(\d+)\s*(?:-|to|upto|–|—)\s*(\d+)", t)
        if range_match:
            low, high = map(int, range_match.groups())
            est = (low + high) // 2
            logging.info(f"[BUDGET] Range {low}-{high} → Estimated {est}")
            return est

        # -----------------------------------------
        # 2) K / Thousand formats
        # -----------------------------------------
        # e.g.: "2k", "3.5k", "5 thousand"
        k_match = re.search(r"(\d+(\.\d+)?)\s*(k|thousand)", t)
        if k_match:
            num = float(k_match.group(1))
            val = int(num * 1000)
            logging.info(f"[BUDGET] Converted K/thousand: {num}k → {val}")
            return val

        # -----------------------------------------
        # 3) Currency formats
        # -----------------------------------------
        # ₹1500, Rs 900, $50, INR 2000
        currency_match = re.search(r"(₹|rs\.?|inr|\$)\s*(\d+)", t)
        if currency_match:
            val = int(currency_match.group(2))
            logging.info(f"[BUDGET] Currency detected → {val}")
            return val

        # -----------------------------------------
        # 4) Standalone digits
        # -----------------------------------------
        # but avoid false positives like "size 7", "item 42"
        nums = re.findall(r"\d+", t)

        if nums:
            # Take the largest meaningful number (budget is usually largest)
            num = max(map(int, nums))

            # Ignore small numbers (size, age)
            if num < 100:
                logging.info(f"[BUDGET] Ignored small number {num}")
            else:
                logging.info(f"[BUDGET] Extracted standalone number → {num}")
                return num

        # -----------------------------------------
        # 5) Keyword-based fallback
        # -----------------------------------------
        cheap_words = ["cheap", "affordable", "low budget", "budget", "underbudget"]
        if any(w in t for w in cheap_words):
            logging.info("[BUDGET] Keyword fallback → 1000")
            return 1000

        return None
