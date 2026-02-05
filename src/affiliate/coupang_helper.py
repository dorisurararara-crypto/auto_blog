import os
import hmac
import hashlib
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CoupangHelper:
    def __init__(self):
        self.access_key = os.getenv("COUPANG_ACCESS_KEY")
        self.secret_key = os.getenv("COUPANG_SECRET_KEY")
        self.domain = "https://api-gateway.coupang.com"

    def _generate_auth_header(self, method, path, query_string=""):
        """쿠팡 파트너스 공식 HMAC 서명 생성 (여기.txt 참고)"""
        # GMT 기준 시간 생성
        date_gmt = time.strftime('%y%m%d', time.gmtime())
        time_gmt = time.strftime('%H%M%S', time.gmtime())
        datetime_str = date_gmt + 'T' + time_gmt + 'Z'
        
        # 메시지 조합
        message = datetime_str + method + path + (query_string or "")
        
        # HMAC 서명 생성
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        return f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_str}, signature={signature}"

    def search_products(self, keyword, limit=3):
        """키워드로 상품 검색 (여기.txt의 안정적인 파싱 로직 적용)"""
        # 정확한 API 경로
        path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
        
        # 키워드 인코딩
        encoded_keyword = requests.utils.quote(keyword)
        query_string = f"keyword={encoded_keyword}&limit={limit}"
        
        url = f"{self.domain}{path}?{query_string}"
        
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": self._generate_auth_header("GET", path, query_string)
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 여기.txt의 유연한 데이터 파싱 로직 적용
                items = []
                if "data" in data:
                    d = data["data"]
                    if isinstance(d, list): 
                        items = d
                    elif isinstance(d, dict):
                        items = d.get("productData", []) or d.get("items", [])

                result_links = []
                for item in items:
                    p_url = item.get("productUrl") or item.get("link")
                    p_name = item.get("productName") or item.get("title")
                    p_price = item.get("productPrice") or item.get("price")
                    
                    if not p_url or not p_name: 
                        continue

                    result_links.append({
                        "name": p_name,
                        "price": p_price,
                        "link": p_url,
                        "image": item.get("productImage") or item.get("imageUrl")
                    })
                
                print(f"[+] 쿠팡 '{keyword}' 검색 성공: {len(result_links)}개 발견")
                return result_links[:limit]
            else:
                print(f"[!] 쿠팡 API 오류 ({response.status_code}): {response.text}")
                return []
        except Exception as e:
            print(f"[!] 쿠팡 API 예외 발생: {e}")
            return []

if __name__ == "__main__":
    helper = CoupangHelper()
    test_keyword = "비타민 K2"
    print(f"[*] '{test_keyword}' 테스트 검색 중...")
    results = helper.search_products(test_keyword, limit=2)
    if results:
        for res in results:
            print(f"- {res['name']} ({res['price']}원)\n  링크: {res['link']}")
    else:
        print("[!] 검색 결과가 없습니다.")
