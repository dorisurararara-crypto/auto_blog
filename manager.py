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
        
        print("[*] GTB 블로그 자동화 엔진 가동 중...")
        self.collector = RedditCollector()
        self.searcher = GoogleSearcher()
        self.processor = ClaudeProcessor()
        self.painter = LocalPainter()
        self.affiliate = CoupangHelper()
        
        self.target_subreddits = ["Supplements", "Gadgets", "HomeImprovement"]

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
        sections = raw_text.split("---")
        data = {}
        for section in sections:
            if "TITLE:" in section: data['title'] = section.replace("TITLE:", "").strip()
            elif "SUMMARY:" in section: data['summary'] = section.replace("SUMMARY:", "").strip()
            elif "CONTENT:" in section: data['content'] = section.replace("CONTENT:", "").strip()
            elif "IMAGE_PROMPT:" in section: data['image_prompt'] = section.replace("IMAGE_PROMPT:", "").strip()
            elif "KEYWORDS:" in section: data['keywords'] = section.replace("KEYWORDS:", "").strip()
        return data

    def run_pipeline(self):
        print("\n" + "="*60)
        print(f"🚀 블로그 포스팅 자동화 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        today_str = datetime.now().strftime("%Y%m%d")

        for sub in self.target_subreddits:
            posts = self.collector.fetch_top_posts(sub, limit=1)
            
            for post in posts:
                if self.is_already_processed(post['id']):
                    continue

                # 1. 트렌드 검색 및 가공
                search_query = " ".join(post['title'].split()[:3])
                korean_trends = self.searcher.search_korean_trends(search_query)
                processed_text = self.processor.process_post(post, korean_trends=korean_trends)
                if not processed_text: continue
                parsed_data = self.parse_claude_result(processed_text)
                
                # 2. 이미지 생성 (Astro public 폴더로 바로 저장)
                img_prompt = parsed_data.get('image_prompt', "Professional high-quality photography")
                image_filename = f"thumb_{post['id']}.png"
                # 이미지 경로를 public/images로 수정
                self.painter.generate_image(img_prompt, image_filename)
                # local_painter.py가 data/images에 저장하므로 이동 로직 추가 (나중에 painter 자체를 고쳐도 됨)
                os.rename(f"data/images/{image_filename}", f"public/images/{image_filename}")
                
                # 3. 쿠팡 링크
                keywords = parsed_data.get('keywords', "").replace("[", "").replace("]", "").split(",")
                search_keyword = keywords[0].strip() if keywords else "베스트셀러"
                coupang_items = self.affiliate.search_products(search_keyword, limit=3)
                
                # 4. 파일 저장 (Astro content 폴더로 저장)
                safe_title = self.sanitize_filename(parsed_data.get('title', 'no_title'))
                final_filename = f"{today_str}_{safe_title}.md"
                # 경로 수정
                final_post_path = f"src/content/blog/{final_filename}"
                
                with open(final_post_path, "w", encoding="utf-8") as f:
                    # Astro Frontmatter 추가 (매우 중요!)
                    f.write("---\n")
                    f.write(f"title: \"{parsed_data.get('title')}\"\n")
                    f.write(f"summary: \"{parsed_data.get('summary')}\"\n")
                    f.write(f"image: \"/images/{image_filename}\"\n")
                    f.write("---\n\n")
                    
                    f.write(f"![Thumbnail](/images/{image_filename})\n\n")
                    f.write(f"## 💡 핵심 요약\n{parsed_data.get('summary')}\n\n")
                    f.write(f"{parsed_data.get('content')}\n\n")
                    
                    if coupang_items:
                        f.write("\n---\n### 🛒 추천 아이템\n")
                        for item in coupang_items:
                            f.write(f"- **[{item['name']}]({item['link']})** ({item['price']}원)\n")
                        f.write("\n\n*이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.*\n")
                
                self.mark_as_processed(post['id'], parsed_data.get('title'), final_post_path)
                print(f"[+++] 블로그 게시 완료: {final_post_path}")
                
                # 5. Git Push (배포)
                print("[*] Cloudflare Pages로 배포 중 (Git Push)...")
                os.system("git add .")
                os.system(f"git commit -m \"New post: {parsed_data.get('title')}\"")
                os.system("git push origin main")
                
                time.sleep(5)

        print("\n" + "="*60)
        print("✅ 모든 작업 및 배포가 완료되었습니다.")
        print("="*60)

if __name__ == "__main__":
    manager = GTBManager()
    manager.run_pipeline()