import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GoogleSearcher:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = os.getenv("GOOGLE_SEARCH_CX")

    def search_korean_trends(self, keyword):
        """구글에서 한국 상위 블로그 정보를 검색하여 요약합니다."""
        if not self.api_key or not self.cx:
            print("[!] 구글 검색 API 키 또는 CX가 설정되지 않았습니다. 트렌드 분석을 건너뜁니다.")
            return None

        print(f"[*] 구글에서 '{keyword}' 관련 한국 트렌드 검색 중...")
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": keyword,
            "lr": "lang_ko", 
            "num": 5
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                items = response.json().get("items", [])
                trend_summary = []
                for item in items:
                    title = item.get("title")
                    snippet = item.get("snippet")
                    trend_summary.append(f"- 제목: {title}\n  내용요약: {snippet}")
                
                return "\n".join(trend_summary)
            else:
                print(f"[!] 구글 검색 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"[!] 구글 검색 중 오류 발생: {e}")
            return None

if __name__ == "__main__":
    searcher = GoogleSearcher()
    print(searcher.search_korean_trends("비타민D K2 효능"))