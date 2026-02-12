# domain/shared/vision.py
import google.generativeai as genai
from core.config import settings # 설정 파일에 API_KEY 저장 가정

class VisionAnalyzer:
    def __init__(self):
        # API 키 설정 (무료 티어)
        genai.configure(api_key=settings.gemini_api_key)
        model_id = getattr(settings, "gemini_model", None) or "gemini-2.5-flash"
        self.model = genai.GenerativeModel(model_id)

    async def describe_image_for_rag(self, image_b64: str) -> str:
        """
        이미지를 분석하여 RAG 검색에 최적화된 키워드와 맥락을 추출합니다.
        """
        # 이미지 데이터 처리 (base64 string -> bytes)
        import base64
        image_data = base64.b64decode(image_b64)

        prompt = """
        이 사진을 분석해서 O*NET 직업 역량 데이터베이스에서 검색할 수 있는 키워드를 추출해줘.
        1. 사진 속 주요 도구나 장비
        2. 수행 중인 작업의 종류
        3. 필요한 핵심 역량 (예: 손가락 민첩성, 시력, 수리력 등)
        결과는 RAG 검색 쿼리로 쓸 수 있게 문장으로 요약해줘.
        """

        response = await self.model.generate_content_async([
            prompt,
            {'mime_type': 'image/jpeg', 'data': image_data}
        ])

        return response.text
