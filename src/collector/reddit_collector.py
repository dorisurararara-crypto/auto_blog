import requests
import time
import re
from bs4 import BeautifulSoup

class RedditCollector:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

    def fetch_top_posts(self, subreddit_name, limit=1):
        """레딧(old 버전)과 구글 뉴스를 교대로 시도하여 무조건 데이터를 가져옵니다."""
        
        # 시도 1: old.reddit.com (더 안정적임)
        print(f"\n[*] r/{subreddit_name} 트렌드 수집 중 (Reddit Mirror)...")
        reddit_url = f"https://old.reddit.com/r/{subreddit_name}/top/.rss?t=day"
        
        try:
            response = requests.get(reddit_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return self._parse_reddit_rss(response.text, limit)
            else:
                print(f"[!] 레딧 응답 지연 (Status: {response.status_code}). 구글 뉴스로 전환합니다.")
        except Exception:
            print("[!] 레딧 접속 불가. 구글 뉴스로 전환합니다.")

        # 시도 2: 구글 뉴스 (백업 - 매우 안정적)
        # 해당 서브레딧 키워드로 글로벌 최신 뉴스를 가져옵니다.
        print(f"[*] '{subreddit_name}' 관련 글로벌 최신 트렌드 검색 중 (Google News)...")
        google_news_url = f"https://news.google.com/rss/search?q={subreddit_name}+latest&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(google_news_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return self._parse_google_news_rss(response.text, limit)
        except Exception as e:
            print(f"[!] 모든 수집 수단 실패: {e}")
        
        return []

    def _parse_reddit_rss(self, xml_text, limit):
        soup = BeautifulSoup(xml_text, "xml")
        entries = soup.find_all("entry")[:limit]
        posts = []
        for entry in entries:
            title = entry.find("title").text
            content_html = entry.find("content").text if entry.find("content") else ""
            content_text = BeautifulSoup(content_html, "html.parser").get_text()
            posts.append({
                "id": entry.find("id").text.split("/")[-1],
                "title": title,
                "content": content_text if len(content_text) > 20 else title,
                "url": entry.find("link")["href"] if entry.find("link") else ""
            })
            print(f"[+] 레딧 수집 성공: {title[:30]}...")
        return posts

    def _parse_google_news_rss(self, xml_text, limit):
        soup = BeautifulSoup(xml_text, "xml")
        items = soup.find_all("item")[:limit]
        posts = []
        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            posts.append({
                "id": re.sub(r'[^a-zA-Z0-0]', '', title)[:15],
                "title": title,
                "content": f"Global Trend News: {title}. Source: {link}",
                "url": link
            })
            print(f"[+] 구글 뉴스 수집 성공: {title[:30]}...")
        return posts

if __name__ == "__main__":
    collector = RedditCollector()
    results = collector.fetch_top_posts("Supplements", limit=1)
    print(f"수집 결과: {len(results)}건")
