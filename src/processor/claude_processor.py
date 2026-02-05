import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeProcessor:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5" 

    def process_post(self, raw_post, korean_trends=None):
        """
        Reddit 원문과 한국 상위 블로그 트렌드를 결합하여 포스팅을 생성합니다.
        """
        trend_context = ""
        if korean_trends:
            trend_context = f"\n[현재 한국 상위 블로그 트렌드 정보]\n{korean_trends}\n"

        prompt = f"""
        당신은 한국의 네이버 블로그와 티스토리에서 검색 상위 1%를 차지하는 최고급 콘텐츠 에디터입니다.
        해외 Reddit의 최신 정보와 한국의 상위 노출 트렌드를 결합하여 최고의 포스팅을 작성하세요.

        [Reddit 원문 정보]
        제목: {raw_post['title']}
        본문: {raw_post['content']}
        {trend_context}

        [요청 사항]
        1. 제목: 한국의 상위 노출 블로그들처럼 '클릭을 부르는 제목 패턴'을 사용하되, Reddit의 신선한 주제를 강조하세요. 
           (예: 총정리, ~하는 이유, 약사/의사 추천 등 한국형 키워드 포함)
        2. 본문: 한국 독자들이 선호하는 '가독성 좋은 구조' (이모지 활용, 명확한 소제목, 불렛 포인트)를 적용하세요.
        3. 톤앤매너: 전문적이면서도 이웃집 블로거처럼 친근한 구어체를 사용하세요.
        4. 상품 매칭: 본문 중간중간 자연스럽게 쿠팡에서 추천할만한 상품(영양제, it기기 등)의 필요성을 언급하세요.

        [출력 형식]
        TITLE: [제목]
        ---
        SUMMARY: [3줄 요약]
        ---
        CONTENT: [본문 내용]
        ---
        IMAGE_PROMPT: [영문 이미지 프롬프트]
        ---
        KEYWORDS: [쿠팡 검색 키워드]
        """

        print(f"[*] Claude 4.5가 한국형 트렌드를 반영하여 가공 중...")
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error: {str(e)}")
            return None