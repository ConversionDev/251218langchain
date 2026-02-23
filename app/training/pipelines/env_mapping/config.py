"""
환경 데이터 매핑 파이프라인 설정.

- 언어 3단계 (ESG·공급망 커버리지)
- 검증 상태 라벨
"""

# 1단계: 글로벌 + 동아시아
STAGE_1_LANGUAGES = [
    ("en", "English"),
    ("ko", "Korean"),
    ("zh", "Chinese (Simplified)"),
    ("ja", "Japanese"),
]

# 2단계: EU·라틴
STAGE_2_LANGUAGES = [
    ("de", "German"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("pt", "Portuguese"),
]

# 3단계: ASEAN·중동 등
STAGE_3_LANGUAGES = [
    ("vi", "Vietnamese"),
    ("th", "Thai"),
    ("id", "Indonesian"),
    ("ar", "Arabic"),
]

ALL_LANGUAGES: list[tuple[str, str]] = (
    STAGE_1_LANGUAGES + STAGE_2_LANGUAGES + STAGE_3_LANGUAGES
)

LANGUAGE_CODES: list[str] = [code for code, _ in ALL_LANGUAGES]

# Excel 컬럼명용 언어 라벨 (코드 -> 한글)
LANG_CODE_TO_LABEL: dict[str, str] = {
    "en": "영문",
    "ko": "국문",
    "zh": "중국어",
    "ja": "일본어",
    "de": "독일어",
    "fr": "프랑스어",
    "es": "스페인어",
    "pt": "포르투갈어",
    "vi": "베트남어",
    "th": "태국어",
    "id": "인도네시아어",
    "ar": "아랍어",
}

def excel_col_name(field: str, lang_label: str) -> str:
    """field: '물질명' | '동의어' | '검증', lang_label: '영문' 등."""
    return f"{field}({lang_label})"

# 검증 상태
STATUS_OFFICIAL_MATCH = "공식DB일치"
STATUS_EXAONE_CANDIDATE = "ExaOne후보"
STATUS_UNVERIFIED = "미검증"
