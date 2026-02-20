import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_and_rank_topics(self, raw_posts):
        """
        Analyze topics and pick the best one for a comparison-style article (A vs B).
        """
        if not raw_posts:
            return []

        topics_str = ""
        for i, post in enumerate(raw_posts):
            topics_str += f"[{i}] Title: {post['title']}\n"

        prompt = f"""
        You are a top-tier SEO strategist specializing in Korean search market.
        Your goal: find the topic BEST suited for an "A vs B" comparison article that will rank high on Google Korea.

        [Selection Criteria]
        1. Comparison Potential: Can we extract TWO comparable products, methods, or technologies from this topic?
        2. Search Intent: Koreans actively search "A vs B", "A B 비교", "A B 차이" for this topic.
        3. Content Gap: Lack of quality Korean comparison content on this topic.
        4. Profitability: Links well to Coupang products (both A and B sides).
        5. E-E-A-T: We can provide expert-level comparison with data.

        [Topics List]
        {topics_str}

        [Output Format - STRICT]
        WINNER_INDEX: [Index Number]
        REASON: [Short analysis in Korean on why this is the best comparison topic]
        COMPARE_A: [First item/product/method to compare - in Korean]
        COMPARE_B: [Second item/product/method to compare - in Korean]
        TARGET_KEYWORDS: [3 comparison-focused long-tail keywords in Korean, comma separated, must include "vs" or "비교"]
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text

            winner_match = re.search(r'WINNER_INDEX:\s*(\d+)', result_text)
            if winner_match:
                winner_idx = int(winner_match.group(1))
                if winner_idx >= len(raw_posts):
                    winner_idx = 0

                reason = re.search(r'REASON:\s*(.*)', result_text, re.MULTILINE)
                keywords = re.search(r'TARGET_KEYWORDS:\s*(.*)', result_text, re.MULTILINE)
                compare_a = re.search(r'COMPARE_A:\s*(.*)', result_text, re.MULTILINE)
                compare_b = re.search(r'COMPARE_B:\s*(.*)', result_text, re.MULTILINE)

                winner_post = raw_posts[winner_idx]
                winner_post['analysis_reason'] = reason.group(1).strip() if reason else "Selected for high comparison potential."
                winner_post['target_keywords'] = keywords.group(1).strip() if keywords else ""
                winner_post['compare_a'] = compare_a.group(1).strip() if compare_a else ""
                winner_post['compare_b'] = compare_b.group(1).strip() if compare_b else ""

                print(f"[*] Gemini selected comparison topic: '{winner_post['title'][:30]}...'")
                if winner_post.get('compare_a') and winner_post.get('compare_b'):
                    print(f"    → {winner_post['compare_a']} vs {winner_post['compare_b']}")
                return [winner_post]

            return [raw_posts[0]]
        except Exception as e:
            print(f"[!] Gemini analysis error: {e}")
            return [raw_posts[0]]

if __name__ == "__main__":
    analyzer = GeminiAnalyzer()
    test_posts = [{"title": "Best magnesium for sleep?"}, {"title": "OLED vs IPS for work"}]
    print(analyzer.analyze_and_rank_topics(test_posts))
