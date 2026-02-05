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
        data = {}
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
        if not data.get('keywords') and data.get('title'):
            data['keywords'] = " ".join(data['title'].split()[:2])
        return data

    def run_pipeline(self):
        print("\n" + "="*60)
        print(f"🚀 GTB 자동 포스팅 시작 (안전 모드): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        today_str = datetime.now().strftime("%Y%m%d")

        for sub in self.target_subreddits:
            # 상위 5개까지 가져와서 중복되지 않은 가장 최신 글 하나를 선택
            posts = self.collector.fetch_top_posts(sub, limit=5)
            category_name = self.category_map.get(sub, "인사이트")
            
            published_in_sub = False
            for post in posts:
                if self.is_already_processed(post['id']):
                    print(f"[-] 중복 건너뛰기 ({sub}): {post['title'][:30]}...")
                    continue

                print(f"[*] 새 콘텐츠 발견! ({sub}): {post['title'][:30]}...")
                search_query = " ".join(post['title'].split()[:3])
                korean_trends = self.searcher.search_korean_trends(search_query)
                processed_text = self.processor.process_post(post, korean_trends=korean_trends)
                if not processed_text: continue
                parsed_data = self.parse_claude_result(processed_text)
                
                img_prompt = parsed_data.get('image_prompt', "Professional photography")
                image_filename = f"thumb_{post['id']}.png"
                self.painter.generate_image(img_prompt, image_filename)
                
                os.makedirs("public/images", exist_ok=True)
                if os.path.exists(f"data/images/{image_filename}"):
                    # Windows에서 대상 파일이 이미 존재할 경우 에러가 나지 않도록 os.replace 사용
                    import shutil
                    shutil.move(f"data/images/{image_filename}", f"public/images/{image_filename}")
                
                keywords_raw = parsed_data.get('keywords', "").replace("[", "").replace("]", "").split(",")
                search_keyword = "인기상품"
                for kw in keywords_raw:
                    clean_kw = kw.strip()
                    if clean_kw and len(clean_kw) > 1:
                        search_keyword = clean_kw
                        break
                
                coupang_items = self.affiliate.search_products(search_keyword, limit=3)
                if not coupang_items:
                    fallback_kw = " ".join(parsed_data.get('title', '').split()[:2])
                    coupang_items = self.affiliate.search_products(fallback_kw, limit=3)

                # [DB 저장 로직] 파일을 만드는 대신 Cloudflare D1에 직접 INSERT
                safe_title = parsed_data.get('title', 'no_title').replace("'", "''")
                safe_summary = parsed_data.get('summary', '').replace("'", "''")
                # 본문 마크다운 결합
                full_content = f"## 💡 핵심 요약\n{parsed_data.get('summary')}\n\n{parsed_data.get('content')}"
                if coupang_items:
                    full_content += "\n\n---\n### 🛒 추천 상품\n"
                    for item in coupang_items:
                        full_content += f"- **[{item['name']}]({item['link']})** ({item['price']}원)\n"
                    full_content += "\n*쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.*\n"
                
                safe_content = full_content.replace("'", "''")
                slug = f"{today_str}-{post['id']}"
                image_url = f"/images/{image_filename}"
                
                print(f"[*] DB에 포스팅 저장 중: {safe_title}")
                
                # D1 실행 (원격 배포된 DB에 즉시 반영)
                db_name = "auto-blog-db" # 실제 D1 데이터베이스 이름
                sql = f"INSERT INTO posts (slug, title, summary, content, category, image_url) VALUES ('{slug}', '{safe_title}', '{safe_summary}', '{safe_content}', '{category_name}', '{image_url}');"
                
                # 임시 SQL 파일 생성
                with open("temp.sql", "w", encoding="utf-8") as f:
                    f.write(sql)
                
                # D1 실행
                os.system(f"npx wrangler d1 execute {db_name} --remote --file=temp.sql --yes")
                os.remove("temp.sql")

                self.mark_as_processed(post['id'], parsed_data.get('title'), f"db://{slug}")
                print(f"[+++] DB 발행 완료: {slug}")
                
                # 이미지 파일은 여전히 깃허브에 올려야 함 (public/images)
                os.system("git add public/images/*")
                os.system(f"git commit -m \"Image: {image_filename}\"")
                os.system("git push origin main")
                
                published_in_sub = True
                time.sleep(5)
                break # 한 개의 글을 발행했으면 다음 카테고리로 이동

            if not published_in_sub:
                print(f"[-] {sub} 카테고리에 새로 발행할 수 있는 글이 없습니다.")

        print("\n" + "="*60)
        print("✅ 모든 작업 완료.")
        print("="*60)

if __name__ == "__main__":
    manager = GTBManager()
    manager.run_pipeline()
