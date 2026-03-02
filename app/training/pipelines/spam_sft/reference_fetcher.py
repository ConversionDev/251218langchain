"""
한국어 스팸 참고 데이터 수집 (3개 출처).

1. 공공데이터포털 (data.go.kr): 불법 스팸 URL, 피싱사이트 데이터
2. GitHub: KoreanSpamDataPool, KOR_phishing_Detect-Dataset 등
3. KISA 보고서/자료실: 스팸 유형별 패턴·키워드

ExaOne 생성 시 few-shot 예시로 사용.
출력 형식: {"subject", "sender", "body", "label"} (label: spam/ham)
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import httpx


# =============================================================================
# 1. 공공데이터포털 (data.go.kr)
# =============================================================================

# 불법 스팸 URL 데이터 (KISA 제공) - 공공데이터포털 파일 데이터
# 실제 다운로드는 로그인/API 키 필요한 경우가 있어, 샘플 URL 패턴만 추출
DATA_GO_KR_SPAM_URL_INFO = "https://www.data.go.kr/data/15134609/fileData.do"
DATA_GO_KR_PHISHING_INFO = "https://www.data.go.kr/data/15143094/fileData.do"

# 공공데이터포털에서 직접 다운로드 가능한 CSV (있을 경우)
# 참고: 실제로는 로그인 후 다운로드해야 하는 경우가 많음
# 여기서는 패턴/유형 정보만 하드코딩으로 제공

SPAM_URL_PATTERNS = [
    # KISA 불법 스팸 URL 데이터에서 자주 나오는 패턴들
    {"pattern": "bit.ly/", "type": "단축URL", "description": "단축 URL로 악성 사이트 유도"},
    {"pattern": "tinyurl.com/", "type": "단축URL", "description": "단축 URL 피싱"},
    {"pattern": ".xyz/", "type": "의심도메인", "description": "저렴한 도메인 사용 스팸"},
    {"pattern": ".top/", "type": "의심도메인", "description": "스팸에 자주 쓰이는 TLD"},
    {"pattern": ".click/", "type": "의심도메인", "description": "클릭 유도형 도메인"},
    {"pattern": "카카오", "type": "사칭", "description": "카카오 사칭 피싱"},
    {"pattern": "네이버", "type": "사칭", "description": "네이버 사칭 피싱"},
    {"pattern": "국세청", "type": "정부사칭", "description": "국세청 사칭 피싱"},
    {"pattern": "건강보험", "type": "정부사칭", "description": "건강보험공단 사칭"},
    {"pattern": "택배", "type": "택배사칭", "description": "택배 배송 사칭 스미싱"},
]


def fetch_data_go_kr_patterns() -> list[dict[str, str]]:
    """공공데이터포털 기반 스팸 패턴 반환 (하드코딩).
    
    실제 CSV 다운로드는 로그인 필요. 여기서는 알려진 패턴만 반환.
    """
    samples = []
    for p in SPAM_URL_PATTERNS:
        samples.append({
            "subject": f"[{p['type']}] {p['description']}",
            "sender": "unknown@spam.com",
            "body": f"스팸 패턴: {p['pattern']} 포함된 URL 클릭 유도. {p['description']}",
            "label": "spam",
            "source": "data.go.kr",
        })
    print(f"[reference_fetcher] 공공데이터포털 패턴: {len(samples)}건")
    return samples


# =============================================================================
# 2. GitHub 공개 저장소
# =============================================================================

GITHUB_SOURCES = [
    {
        "name": "KoreanSpamDataPool",
        "url": "https://raw.githubusercontent.com/idjoopal/KoreanSpamDataPool/master/%EB%B6%88%EB%9F%89%EC%9C%A0%EC%A0%80%20%EC%B2%98%EB%A6%AC%EC%9A%A9%20%EB%8D%B0%EC%9D%B4%ED%84%B0%20%ED%92%80.xlsx",
        "type": "xlsx",
    },
    {
        "name": "KOR_phishing_Detect",
        "url": "https://raw.githubusercontent.com/Ez-Sy01/KOR_phishing_Detect-Dataset/main/data/phishing_data.csv",
        "type": "csv",
    },
]

# GitHub에서 가져올 수 있는 한국어 스팸 예시 (하드코딩 백업)
GITHUB_SPAM_EXAMPLES = [
    {
        "subject": "[긴급] 계정이 정지됩니다",
        "sender": "security@fake-bank.com",
        "body": "고객님의 계정에서 비정상적인 활동이 감지되었습니다. 24시간 내에 본인 확인을 하지 않으면 계정이 영구 정지됩니다. 아래 링크를 클릭하여 확인하세요.",
        "label": "spam",
    },
    {
        "subject": "축하합니다! 100만원 당첨",
        "sender": "event@promo-win.com",
        "body": "회원님께서 이벤트에 당첨되셨습니다! 경품 수령을 위해 개인정보를 입력해 주세요. 기한 내 미수령 시 자동 소멸됩니다.",
        "label": "spam",
    },
    {
        "subject": "[CJ대한통운] 배송 불가 안내",
        "sender": "delivery@cj-fake.com",
        "body": "고객님의 택배가 주소 불명으로 배송 불가 상태입니다. 정확한 주소 확인을 위해 아래 링크에서 정보를 업데이트해 주세요.",
        "label": "spam",
    },
    {
        "subject": "국세청 세금 환급 안내",
        "sender": "tax@nts-fake.go.kr",
        "body": "귀하의 종합소득세 환급금 320,000원이 발생하였습니다. 환급 계좌 등록을 위해 홈택스에 접속하여 본인 인증을 완료해 주세요.",
        "label": "spam",
    },
    {
        "subject": "카카오 계정 로그인 알림",
        "sender": "no-reply@kakaocorp-fake.com",
        "body": "새로운 기기에서 로그인이 감지되었습니다. 본인이 아닌 경우 즉시 비밀번호를 변경해 주세요. [비밀번호 변경하기]",
        "label": "spam",
    },
    {
        "subject": "건강보험료 환급금 안내",
        "sender": "nhis@health-fake.or.kr",
        "body": "2024년 건강보험료 정산 결과 환급금이 발생하였습니다. 환급 신청은 아래 링크에서 진행해 주세요. 미신청 시 국고 환수됩니다.",
        "label": "spam",
    },
    {
        "subject": "[네이버] 비밀번호 변경 요청",
        "sender": "security@naver-fake.com",
        "body": "회원님의 계정 보안을 위해 비밀번호 변경이 필요합니다. 7일 이내 변경하지 않으면 계정 이용이 제한됩니다.",
        "label": "spam",
    },
    {
        "subject": "대출 승인 완료 - 즉시 입금 가능",
        "sender": "loan@easy-money.com",
        "body": "축하합니다! 신용등급 관계없이 최대 5천만원까지 대출이 승인되었습니다. 지금 바로 신청하세요. 당일 입금!",
        "label": "spam",
    },
]

GITHUB_HAM_EXAMPLES = [
    {
        "subject": "주간 업무 보고",
        "sender": "kim.manager@company.com",
        "body": "안녕하세요, 이번 주 진행 상황 공유드립니다. 프로젝트 A는 80% 완료되었고, 다음 주 중 마무리 예정입니다. 궁금한 점 있으시면 말씀해 주세요.",
        "label": "ham",
    },
    {
        "subject": "회의 일정 안내",
        "sender": "hr@company.com",
        "body": "내일 오후 2시에 3층 회의실에서 분기 리뷰 회의가 있습니다. 참석 부탁드립니다. 자료는 첨부파일 확인해 주세요.",
        "label": "ham",
    },
    {
        "subject": "점심 뭐 먹을까?",
        "sender": "friend@gmail.com",
        "body": "오늘 점심 같이 먹자! 새로 생긴 파스타집 가볼까? 12시에 로비에서 만나.",
        "label": "ham",
    },
    {
        "subject": "주문하신 상품이 배송 시작되었습니다",
        "sender": "no-reply@coupang.com",
        "body": "고객님이 주문하신 [무선 이어폰]이 오늘 출고되어 내일 도착 예정입니다. 배송 조회는 쿠팡 앱에서 확인하세요.",
        "label": "ham",
    },
]


def fetch_github_samples(max_spam: int = 20, max_ham: int = 10) -> tuple[list[dict], list[dict]]:
    """GitHub에서 한국어 스팸/햄 예시 가져오기.
    
    실제 저장소 접근이 안 되면 하드코딩된 예시 반환.
    """
    spam_list = []
    ham_list = []
    
    # GitHub 저장소에서 실제 데이터 시도
    for source in GITHUB_SOURCES:
        if len(spam_list) >= max_spam:
            break
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                r = client.get(source["url"])
                if r.status_code != 200:
                    continue
                
                content = r.text
                if source["type"] == "csv" and content.strip():
                    reader = csv.DictReader(io.StringIO(content))
                    for row in reader:
                        if len(spam_list) >= max_spam:
                            break
                        # 다양한 컬럼명 처리
                        text = ""
                        label = ""
                        for k, v in row.items():
                            if v and k.lower() in ("text", "message", "body", "content", "본문"):
                                text = str(v).strip()
                            if v and k.lower() in ("label", "class", "type", "spam"):
                                label = str(v).strip().lower()
                        if text and ("spam" in label or "phishing" in label or "1" == label):
                            spam_list.append({
                                "subject": text[:50] + "..." if len(text) > 50 else text,
                                "sender": "unknown@spam.com",
                                "body": text,
                                "label": "spam",
                                "source": source["name"],
                            })
        except Exception as e:
            print(f"[reference_fetcher] GitHub {source['name']} 접근 실패: {e}")
            continue
    
    # 하드코딩된 예시로 보충
    for ex in GITHUB_SPAM_EXAMPLES:
        if len(spam_list) >= max_spam:
            break
        spam_list.append({**ex, "source": "github_hardcoded"})
    
    for ex in GITHUB_HAM_EXAMPLES:
        if len(ham_list) >= max_ham:
            break
        ham_list.append({**ex, "source": "github_hardcoded"})
    
    print(f"[reference_fetcher] GitHub: 스팸 {len(spam_list)}건, 햄 {len(ham_list)}건")
    return spam_list, ham_list


# =============================================================================
# 3. KISA 불법스팸대응센터 보고서/패턴
# =============================================================================

# KISA 연간 보고서 및 자료실에서 추출한 스팸 유형별 키워드/패턴
KISA_SPAM_PATTERNS = {
    "피싱": [
        "계정 정지", "본인 확인", "비밀번호 변경", "로그인 시도", "보안 경고",
        "OTP 입력", "인증번호", "해외 결제", "이상 거래", "접속 차단",
    ],
    "당첨/이벤트": [
        "축하합니다", "당첨", "경품", "무료 쿠폰", "이벤트 당첨",
        "선물 증정", "100만원", "포인트 지급", "깜짝 선물",
    ],
    "대출/금융": [
        "대출 승인", "신용등급 무관", "당일 입금", "저금리", "한도 증액",
        "무담보", "무직자 가능", "정부지원", "서민대출",
    ],
    "택배/배송": [
        "배송 불가", "주소 확인", "반송 예정", "통관 보류", "수취인 부재",
        "재배송 신청", "운송장 확인",
    ],
    "정부/공공기관": [
        "국세청", "세금 환급", "건강보험", "과태료", "법원 출석",
        "경찰 조사", "검찰 소환", "주민센터",
    ],
    "성인/도박": [
        "성인", "카지노", "바카라", "슬롯", "토토", "배팅", "첫충",
    ],
}

KISA_SPAM_TEMPLATES = [
    {
        "type": "피싱",
        "subject": "[긴급] {keyword} 필요",
        "body": "고객님의 계정에서 {keyword}이(가) 필요합니다. 24시간 내 조치하지 않으면 이용이 제한됩니다. 아래 링크를 클릭하세요.",
    },
    {
        "type": "당첨/이벤트",
        "subject": "{keyword}되셨습니다!",
        "body": "회원님께서 {keyword}되셨습니다! 경품 수령을 위해 개인정보 확인이 필요합니다. 기한 내 미수령 시 자동 소멸됩니다.",
    },
    {
        "type": "대출/금융",
        "subject": "{keyword} 안내",
        "body": "{keyword} 가능합니다. 신용등급 관계없이 최대 5천만원까지 즉시 지급! 지금 바로 상담 신청하세요.",
    },
    {
        "type": "택배/배송",
        "subject": "[택배] {keyword}",
        "body": "고객님의 택배가 {keyword} 상태입니다. 정확한 정보 확인을 위해 아래 링크에서 업데이트해 주세요.",
    },
    {
        "type": "정부/공공기관",
        "subject": "[{keyword}] 안내문",
        "body": "{keyword}에서 알려드립니다. 귀하의 환급금/과태료 관련 사항이 있으니 아래 링크에서 확인해 주세요.",
    },
]


def fetch_kisa_patterns(max_samples: int = 30) -> list[dict[str, str]]:
    """KISA 보고서 기반 스팸 패턴으로 샘플 생성."""
    samples = []
    
    for template in KISA_SPAM_TEMPLATES:
        spam_type = template["type"]
        keywords = KISA_SPAM_PATTERNS.get(spam_type, [])
        
        for keyword in keywords[:5]:  # 유형당 5개씩
            if len(samples) >= max_samples:
                break
            samples.append({
                "subject": template["subject"].format(keyword=keyword),
                "sender": f"spam@{spam_type.replace('/', '-')}.com",
                "body": template["body"].format(keyword=keyword),
                "label": "spam",
                "source": "kisa_pattern",
                "spam_type": spam_type,
            })
    
    print(f"[reference_fetcher] KISA 패턴: {len(samples)}건")
    return samples


# =============================================================================
# 통합 API
# =============================================================================

def fetch_all_references(
    max_spam: int = 50,
    max_ham: int = 20,
) -> tuple[list[dict], list[dict]]:
    """세 곳에서 참고 데이터 수집.
    
    Returns:
        (spam_samples, ham_samples) - ExaOne few-shot용
    """
    print("=" * 60)
    print("[reference_fetcher] 한국어 스팸 참고 데이터 수집 시작")
    print("=" * 60)
    
    all_spam: list[dict] = []
    all_ham: list[dict] = []
    
    # 1. 공공데이터포털 패턴
    try:
        data_go_samples = fetch_data_go_kr_patterns()
        all_spam.extend(data_go_samples)
    except Exception as e:
        print(f"[reference_fetcher] 공공데이터포털 실패: {e}")
    
    # 2. GitHub
    try:
        github_spam, github_ham = fetch_github_samples(
            max_spam=max(10, max_spam // 3),
            max_ham=max(5, max_ham // 2),
        )
        all_spam.extend(github_spam)
        all_ham.extend(github_ham)
    except Exception as e:
        print(f"[reference_fetcher] GitHub 실패: {e}")
    
    # 3. KISA 패턴
    try:
        kisa_samples = fetch_kisa_patterns(max_samples=max(15, max_spam // 3))
        all_spam.extend(kisa_samples)
    except Exception as e:
        print(f"[reference_fetcher] KISA 실패: {e}")
    
    # 중복 제거 (body 기준)
    seen_bodies = set()
    unique_spam = []
    for s in all_spam:
        body = s.get("body", "")[:100]
        if body and body not in seen_bodies:
            seen_bodies.add(body)
            unique_spam.append(s)
    
    unique_ham = []
    for h in all_ham:
        body = h.get("body", "")[:100]
        if body and body not in seen_bodies:
            seen_bodies.add(body)
            unique_ham.append(h)
    
    print()
    print("=" * 60)
    print(f"[reference_fetcher] 수집 완료: 스팸 {len(unique_spam)}건, 햄 {len(unique_ham)}건")
    print("=" * 60)
    
    return unique_spam[:max_spam], unique_ham[:max_ham]


def get_few_shot_examples(n_spam: int = 3, n_ham: int = 2) -> str:
    """ExaOne 프롬프트에 넣을 few-shot 예시 문자열 생성."""
    spam_samples, ham_samples = fetch_all_references(max_spam=n_spam * 2, max_ham=n_ham * 2)
    
    lines = ["다음은 실제 한국어 스팸/정상 메일 예시입니다. 비슷한 패턴으로 생성하세요.\n"]
    
    lines.append("### 스팸 예시:")
    for i, s in enumerate(spam_samples[:n_spam], 1):
        lines.append(f"{i}. 제목: {s['subject']}")
        lines.append(f"   본문: {s['body'][:200]}")
        lines.append("")
    
    lines.append("### 정상(햄) 예시:")
    for i, h in enumerate(ham_samples[:n_ham], 1):
        lines.append(f"{i}. 제목: {h['subject']}")
        lines.append(f"   본문: {h['body'][:200]}")
        lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# 테스트
# =============================================================================

if __name__ == "__main__":
    spam, ham = fetch_all_references(max_spam=30, max_ham=10)
    print(f"\n스팸 샘플 {len(spam)}건:")
    for s in spam[:3]:
        print(f"  - [{s.get('source', '?')}] {s['subject'][:40]}...")
    print(f"\n햄 샘플 {len(ham)}건:")
    for h in ham[:3]:
        print(f"  - [{h.get('source', '?')}] {h['subject'][:40]}...")
    
    print("\n" + "=" * 60)
    print("Few-shot 예시:")
    print("=" * 60)
    print(get_few_shot_examples(n_spam=2, n_ham=1))
