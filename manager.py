import os
import time
import sqlite3
import re
from datetime import datetime
from dotenv import load_dotenv

from src.collector.reddit_collector import RedditCollector
from src.collector.google_searcher import GoogleSearcher
from src.processor.gemini_analyzer import GeminiAnalyzer
from src.processor.claude_processor import ClaudeProcessor
from src.painter.local_painter import LocalPainter
from src.affiliate.coupang_helper import CoupangHelper

load_dotenv()

class GTBManager:
    def __init__(self):
        self.db_path = "data/gtb_storage.db"
        self._init_db()
        print("[*] GTB 매거진 '본질 강화' 엔진 가동 중...")
        self.collector = RedditCollector()
        self.searcher = GoogleSearcher()
        self.analyzer = GeminiAnalyzer()
        self.processor = ClaudeProcessor()
        self.painter = LocalPainter()
        self.affiliate = CoupangHelper()
        
        self.category_map = {
            "Supplements": "건강",
            "Gadgets": "IT테크",
            "HomeImprovement": "라이프",
            "Technology": "IT테크",
            "BuyItForLife": "라이프",
            "LifeProTips": "꿀팁",
            "ExplainLikeImFive": "지식",
            "Biohacking": "건강"
        }
        self.target_subreddits = list(self.category_map.keys())

    def _extract_search_query(self, title):
        """제목에서 검색에 유리한 핵심 키워드를 추출합니다."""
        # 불용어 제거 (간이 버전)
        stop_words = ['how', 'to', 'the', 'a', 'is', 'are', 'what', 'why', 'in', 'of', 'for', 'on', 'with', 'and', 'my', 'do', 'any', 'best', 'new']
        words = re.sub(r'[^a-zA-Z\s]', '', title).lower().split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # 핵심 키워드 3-4개 조합
        return " ".join(filtered_words[:4])

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
        cursor.execute("INSERT OR IGNORE INTO posts (reddit_id, title, processed_date, file_path) VALUES (?, ?, ?, ?)",
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
            'vs_title': r'VS_TITLE:\s*(.*?)(?:\n---|\nTITLE:|$)',
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
        print(f"🚀 GTB 수익화/유입 최적화 모드 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        today_str = datetime.now().strftime("%Y%m%d")

        for sub in self.target_subreddits:
            # 후보군 10개를 가져옴 (Gemini가 분석할 재료)
            posts = self.collector.fetch_top_posts(sub, limit=10)
            category_name = self.category_map.get(sub, "인사이트")
            
            # 아직 처리하지 않은 후보들만 선별
            candidates = [p for p in posts if not self.is_already_processed(p['id'])]
            
            if not candidates:
                print(f"[-] {sub} 카테고리에 새로운 후보가 없습니다.")
                continue

            # [핵심] Gemini가 수익성과 유입 확률이 가장 높은 주제 1개만 선정
            print(f"[*] Gemini가 {len(candidates)}개의 후보 중 '황금 주제' 분석 중...")
            selected_posts = self.analyzer.analyze_and_rank_topics(candidates)
            
            published_in_sub = False
            for post in selected_posts:
                print(f"[!] 최종 당첨! ({sub}): {post['title']}")
                
                # 구체적인 롱테일 키워드로 한국 트렌드 검색
                search_query = post.get('target_keywords', post['title']).split(',')[0]
                korean_trends = self.searcher.search_korean_trends(search_query)
                
                # 고도화된 Claude 프로세서로 글 생성
                processed_text = self.processor.process_post(post, korean_trends=korean_trends)
                if not processed_text: continue
                parsed_data = self.parse_claude_result(processed_text)
                
                img_prompt = parsed_data.get('image_prompt', "Professional photography")
                image_filename = f"thumb_{post['id']}.png"
                self.painter.generate_image(img_prompt, image_filename)
                
                os.makedirs("public/images", exist_ok=True)
                if os.path.exists(f"data/images/{image_filename}"):
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

                # [DB 저장 로직] Cloudflare D1에 직접 INSERT
                safe_title = parsed_data.get('title', 'no_title').replace("'", "''")
                safe_summary = parsed_data.get('summary', '').replace("'", "''")
                # 본문 마크다운 결합 (수익화 CTA 및 버튼 강화)
                full_content = f"## 💡 핵심 요약\n{parsed_data.get('summary')}\n\n{parsed_data.get('content')}"
                if coupang_items:
                    full_content += "\n\n---\n### 🛒 추천 상품 (최저가 및 재고 확인)\n"
                    for item in coupang_items:
                        full_content += f"- **[{item['name']}]({item['link']})** ({item['price']}원) - *실시간 할인 확인하기*\n"
                    full_content += "\n*쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.*\n"
                
                safe_content = full_content.replace("'", "''")
                slug = f"{today_str}-{post['id']}"
                image_url = f"/images/{image_filename}"
                
                print(f"[*] DB에 포스팅 저장 중: {safe_title}")
                
                # D1 실행
                db_name = "auto-blog-db"
                sql = f"INSERT OR IGNORE INTO posts (slug, title, summary, content, category, image_url) VALUES ('{slug}', '{safe_title}', '{safe_summary}', '{safe_content}', '{category_name}', '{image_url}');"
                
                with open("temp.sql", "w", encoding="utf-8") as f:
                    f.write(sql)
                
                os.system(f"npx wrangler d1 execute {db_name} --remote --file=temp.sql --yes")
                os.remove("temp.sql")

                self.mark_as_processed(post['id'], parsed_data.get('title'), f"db://{slug}")
                print(f"[+++] DB 발행 완료: {slug}")
                
                os.system("git add public/images/*")
                os.system(f"git commit -m \"Image: {image_filename}\"")
                os.system("git push origin main")
                
                published_in_sub = True
                time.sleep(5)
                break 

            if not published_in_sub:
                print(f"[-] {sub} 카테고리에 새로 발행할 수 있는 글이 없습니다.")

        print("\n" + "="*60)
        print("✅ 모든 작업 완료.")
        print("="*60)

if __name__ == "__main__":
    manager = GTBManager()
    manager.run_pipeline()