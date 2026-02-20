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
        Reddit 원문과 한국 트렌드를 결합하여 'A vs B 비교 분석글'을 생성합니다.
        """
        trend_context = ""
        if korean_trends:
            trend_context = f"\n[참고: 현재 한국 시장의 관심 키워드 및 트렌드]\n{korean_trends}\n"

        compare_a = raw_post.get('compare_a', '')
        compare_b = raw_post.get('compare_b', '')
        compare_context = ""
        if compare_a and compare_b:
            compare_context = f"\n[비교 대상]\nA: {compare_a}\nB: {compare_b}\n"

        prompt = f"""
        당신은 해당 분야에서 10년 이상 경력을 가진 전문 비교 분석가입니다.
        독자가 "A vs B" 검색 시 가장 먼저 찾게 되는, 압도적으로 유용한 비교 분석글을 작성합니다.

        [분석 대상 데이터]
        제목: {raw_post['title']}
        핵심 내용: {raw_post['content']}
        트렌드 키워드: {raw_post.get('target_keywords', '')}
        선정이유: {raw_post.get('analysis_reason', '')}
        {compare_context}
        {trend_context}

        [작성 원칙]
        1. **제목 형식:** 반드시 "A vs B: 핵심 차이점과 선택 가이드" 형태로 작성. 비교 대상이 명확해야 함.
        2. **객관적 비교:** 감정이 아닌 데이터와 스펙 기반으로 비교. 각 항목별 마크다운 표 필수 포함.
        3. **구조화된 본문:**
           - 서론: 왜 이 비교가 중요한지 (검색 의도 충족)
           - 핵심 비교표: 가격, 성능, 특징 등 항목별 비교
           - 상세 분석: 각 항목을 깊이 있게 설명
           - 결론: "이런 사람은 A, 저런 사람은 B" 명확한 추천
        4. **SEO 키워드 자연 삽입:** "A vs B", "A B 비교", "A B 차이" 등의 검색 키워드를 본문에 자연스럽게 포함.
        5. **말투:** "~합니다"와 "~이죠"를 섞어 권위 있되 읽기 편한 어조. 이모지는 섹션당 최대 1개.
        6. **한국 맥락 적용:** 한국 소비자 관점에서 가격, 구매처, 사용 환경 등을 고려하여 분석.

        [본문 구조 - 반드시 준수]
        ## 서론 (왜 비교해야 하는가)
        ## 한눈에 보는 비교표
        ## 상세 비교 분석
        ### 항목 1
        ### 항목 2
        ### 항목 3
        ## 결론: 당신에게 맞는 선택은?

        [출력 형식 - 반드시 이 형식을 따르세요]
        VS_TITLE: [A vs B 형식의 비교 대상 명시, 예: "에어팟 프로 vs 갤럭시 버즈"]
        ---
        TITLE: [A vs B: 부제목 형식의 제목]
        ---
        SUMMARY: [비교 핵심 요약 2-3문장]
        ---
        CONTENT: [본문 - 비교표 포함 마크다운]
        ---
        IMAGE_PROMPT: [두 제품/개념이 나란히 비교되는 전문적이고 깔끔한 사진 프롬프트]
        ---
        KEYWORDS: [A vs B, A B 비교, A B 차이 등 검색 의도 키워드]
        """

        print(f"[*] Claude가 비교 분석 콘텐츠를 생성 중...")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
