import os
import time
import sqlite3
import re
from datetime import datetime
from dotenv import load_dotenv

from src.collector.reddit_collector import RedditCollector
from src.collector.google_searcher import GoogleSearcher
from src.processor.claude_processor import ClaudeProcessor
from src.painter.local_painter import LocalPainter
from src.affiliate.coupang_helper import CoupangHelper

load_dotenv()

class GTBManager:
    def __init__(self):
        self.db_path = "data/gtb_storage.db"
        self._init_db()
        print("[*] GTB 매거진 엔진 최적화 버전 가동 중...")
        self.collector = RedditCollector()
        self.searcher = GoogleSearcher()
        self.processor = ClaudeProcessor()
        self.painter = LocalPainter()
        self.affiliate = CoupangHelper()
        
        self.category_map = {
            "Supplements": "건강",
            "Gadgets": "IT테크",
            "HomeImprovement": "라이프",
            "Technology": "IT테크",
            "BuyItForLife": "라이프"
        }
        self.target_subreddits = list(self.category_map.keys())

    def _init_db(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS posts (reddit_id TEXT PRIMARY KEY, title TEXT, processed_date TEXT, file_path TEXT)")
        conn.commit()
        conn.close()

    def is_already_processed(self, reddit_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM posts WHERE reddit_id = ?", (reddit_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_as_processed(self, reddit_id, title, file_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (reddit_id, title, processed_date, file_path) VALUES (?, ?, ?, ?)",
            (reddit_id, title, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file_path))
        conn.commit()
        conn.close()

    def sanitize_filename(self, filename):
        filename = re.sub(r'[\/:*?"<>|]', '', filename)
        filename = filename.replace(' ', '_')
        return filename[:50]

    def parse_claude_result(self, raw_text):
        """강화된 파싱 로직: 키워드를 찾지 못할 경우를 대비하여 유연하게 대응"""
        data = {}
        
        # 정규표현식으로 각 섹션 추출
        patterns = {
            'title': r'TITLE:\s*(.*?)(?:\n---|\nSUMMARY:|$)',
            'summary': r'SUMMARY:\s*(.*?)(?:\n---|\nCONTENT:|$)',
            'content': r'CONTENT:\s*(.*?)(?:\n---|\nIMAGE_PROMPT:|$)',
            'image_prompt': r'IMAGE_PROMPT:\s*(.*?)(?:\n---|\nKEYWORDS:|$)',
            'keywords': r'KEYWORDS:\s*(.*)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
            else:
                data[key] = ""
        
        # 만약 keywords가 비어있다면 제목에서 추출 시도
        if not data.get('keywords') and data.get('title'):
            # 제목의 첫 두 단어를 키워드로 사용
            data['keywords'] = " ".join(data['title'].split()[:2])
            
        return data

    def run_pipeline(self):
        print("\n" + "="*60)
        print(f"🚀 GTB 자동 포스팅 시작 (쿠팡 링크 강화): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        today_str = datetime.now().strftime("%Y%m%d")

        for sub in self.target_subreddits:
            posts = self.collector.fetch_top_posts(sub, limit=1)
            category_name = self.category_map.get(sub, "인사이트")
            
            for post in posts:
                if self.is_already_processed(post['id']):
                    continue

                search_query = " ".join(post['title'].split()[:3])
                korean_trends = self.searcher.search_korean_trends(search_query)
                processed_text = self.processor.process_post(post, korean_trends=korean_trends)
                if not processed_text: continue
                parsed_data = self.parse_claude_result(processed_text)
                
                # 이미지 생성 및 이동
                img_prompt = parsed_data.get('image_prompt', "Professional photography")
                image_filename = f"thumb_{post['id']}.png"
                self.painter.generate_image(img_prompt, image_filename)
                os.makedirs("public/images", exist_ok=True)
                if os.path.exists(f"data/images/{image_filename}"):
                    os.rename(f"data/images/{image_filename}", f"public/images/{image_filename}")
                
                # 쿠팡 상품 검색 (키워드 정제 로직 추가)
                print(f"[*] 쿠팡 상품 검색 시도 (키워드: {parsed_data.get('keywords')})")
                keywords_raw = parsed_data.get('keywords', "").replace("[", "").replace("]", "").split(",")
                # 첫 번째 유효한 키워드 선택
                search_keyword = "인기상품"
                for kw in keywords_raw:
                    clean_kw = kw.strip()
                    if clean_kw and len(clean_kw) > 1:
                        search_keyword = clean_kw
                        break
                
                coupang_items = self.affiliate.search_products(search_keyword, limit=3)
                
                # 만약 검색 결과가 없으면 제목에서 한 번 더 시도
                if not coupang_items:
                    fallback_kw = " ".join(parsed_data.get('title', '').split()[:2])
                    print(f"[*] 결과 없음. 대체 키워드로 재검색: {fallback_kw}")
                    coupang_items = self.affiliate.search_products(fallback_kw, limit=3)

                # 파일 저장
                safe_title = self.sanitize_filename(parsed_data.get('title', 'no_title'))
                final_filename = f"{today_str}_{safe_title}.md"
                final_post_path = f"src/content/blog/{final_filename}"
                os.makedirs("src/content/blog", exist_ok=True)
                
                with open(final_post_path, "w", encoding="utf-8") as f:
                    f.write("---\n")
                    f.write(f"title: \"{parsed_data.get('title')}\"\n")
                    f.write(f"summary: \"{parsed_data.get('summary')}\"\n")
                    f.write(f"image: \"/images/{image_filename}\"\n")
                    f.write(f"category: \"{category_name}\"\n")
                    f.write("---\n\n")
                    
                    f.write(f"## 💡 핵심 요약\n{parsed_data.get('summary')}\n\n")
                    f.write(f"{parsed_data.get('content')}\n\n")
                    
                    if coupang_items:
                        f.write("\n---\n### 🛒 추천 아이템\n")
                        for item in coupang_items:
                            f.write(f"- **[{item['name']}]({item['link']})** ({item['price']}원)\n")
                        f.write("\n\n*이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.*\n")
                    else:
                        print("[!] 최종적으로 쿠팡 상품을 찾지 못했습니다.")
                
                self.mark_as_processed(post['id'], parsed_data.get('title'), final_post_path)
                print(f"[+++] 발행 완료: {final_post_path}")
                
                os.system("git add .")
                os.system(f"git commit -m \"Post: {parsed_data.get('title')}\"")
                os.system("git push origin main")
                time.sleep(5)

        print("\n" + "="*60)
        print("✅ 모든 작업 완료.")
        print("="*60)

if __name__ == "__main__":
    manager = GTBManager()
    manager.run_pipeline()