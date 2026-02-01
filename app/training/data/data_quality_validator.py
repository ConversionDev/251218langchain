"""
ETL Transform: Data Quality Validation

데이터 품질 검증 및 정제 모듈 (Transform 단계 유틸리티).

역할: Transform (변환 - 검증 유틸리티)
1. JSONL 파일 형식 검증
2. 필수 필드 검증
3. 데이터 타입 및 값 유효성 검증
4. 이상치 탐지
5. 통계 정보 수집
6. 문제 샘플 필터링 및 정제

사용처: sft_to_train_val_split.py에서 사용
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DataQualityValidator:
    """데이터 품질 검증 및 정제 클래스."""

    def __init__(self):
        """초기화."""
        self.stats = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "errors": defaultdict(int),
            "warnings": defaultdict(int),
        }

    def validate_json_structure(self, item: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """JSON 구조 검증.

        Args:
            item: 검증할 데이터 항목

        Returns:
            (유효성 여부, 오류 메시지)
        """
        # 필수 키 확인
        required_keys = ["instruction", "input", "output"]
        missing_keys = [key for key in required_keys if key not in item]

        if missing_keys:
            return False, f"필수 키 누락: {missing_keys}"

        # instruction 검증
        if not isinstance(item.get("instruction"), str) or not item.get("instruction").strip():
            return False, "instruction이 유효한 문자열이 아님"

        # input 검증
        input_data = item.get("input")
        if not isinstance(input_data, dict):
            return False, "input이 딕셔너리가 아님"

        input_required = ["subject", "attachments", "received_at"]
        input_missing = [key for key in input_required if key not in input_data]

        if input_missing:
            return False, f"input 필수 키 누락: {input_missing}"

        # output 검증
        output_data = item.get("output")
        if not isinstance(output_data, dict):
            return False, "output이 딕셔너리가 아님"

        output_required = ["action", "reason", "confidence"]
        output_missing = [key for key in output_required if key not in output_data]

        if output_missing:
            return False, f"output 필수 키 누락: {output_missing}"

        return True, None

    def validate_data_types(self, item: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """데이터 타입 검증.

        Args:
            item: 검증할 데이터 항목

        Returns:
            (유효성 여부, 오류 메시지)
        """
        input_data = item.get("input", {})
        output_data = item.get("output", {})

        # input 타입 검증
        if not isinstance(input_data.get("subject"), str):
            return False, "input.subject가 문자열이 아님"

        if not isinstance(input_data.get("attachments"), list):
            return False, "input.attachments가 리스트가 아님"

        if not isinstance(input_data.get("received_at"), str):
            return False, "input.received_at이 문자열이 아님"

        # output 타입 검증
        action = output_data.get("action")
        if not isinstance(action, str):
            return False, "output.action이 문자열이 아님"

        if action not in ["BLOCK", "ALLOW"]:
            return False, f"output.action이 유효하지 않음: {action}"

        if not isinstance(output_data.get("reason"), str):
            return False, "output.reason이 문자열이 아님"

        confidence = output_data.get("confidence")
        if not isinstance(confidence, (int, float)):
            return False, "output.confidence가 숫자가 아님"

        if not (0.0 <= confidence <= 1.0):
            return False, f"output.confidence가 범위를 벗어남: {confidence}"

        return True, None

    def validate_data_values(self, item: Dict[str, Any]) -> Tuple[bool, Optional[str], List[str]]:
        """데이터 값 유효성 검증.

        Args:
            item: 검증할 데이터 항목

        Returns:
            (유효성 여부, 오류 메시지, 경고 메시지 리스트)
        """
        warnings = []
        input_data = item.get("input", {})
        output_data = item.get("output", {})

        # subject 검증
        subject = input_data.get("subject", "").strip()
        if not subject:
            return False, "subject가 비어있음", warnings

        if len(subject) > 500:
            warnings.append(f"subject가 과도하게 김: {len(subject)}자")

        if len(subject) < 2:
            warnings.append("subject가 과도하게 짧음")

        # received_at 검증
        received_at = input_data.get("received_at", "").strip()
        if not received_at:
            return False, "received_at이 비어있음", warnings

        # 날짜 형식 간단 검증 (YYYY-MM-DD HH:MM:SS)
        if len(received_at) < 10:
            return False, "received_at 형식이 올바르지 않음", warnings

        # attachments 검증
        attachments = input_data.get("attachments", [])
        if not isinstance(attachments, list):
            return False, "attachments가 리스트가 아님", warnings

        for att in attachments:
            if not isinstance(att, str):
                return False, "attachments 항목이 문자열이 아님", warnings

        # reason 검증
        reason = output_data.get("reason", "").strip()
        if not reason:
            return False, "reason이 비어있음", warnings

        if len(reason) > 1000:
            warnings.append(f"reason이 과도하게 김: {len(reason)}자")

        # confidence 검증
        confidence = output_data.get("confidence")
        if confidence < 0.5:
            warnings.append(f"confidence가 낮음: {confidence}")

        return True, None, warnings

    def detect_outliers(self, item: Dict[str, Any]) -> List[str]:
        """이상치 탐지.

        Args:
            item: 검증할 데이터 항목

        Returns:
            경고 메시지 리스트
        """
        warnings = []
        input_data = item.get("input", {})

        # 제목 이상치
        subject = input_data.get("subject", "")
        if len(subject) > 300:
            warnings.append("제목이 매우 김 (300자 초과)")

        # 특수 문자 과다
        special_chars = sum(1 for c in subject if not c.isalnum() and c not in " .,!?()[]-")
        if special_chars > len(subject) * 0.3:
            warnings.append("제목에 특수 문자가 과다")

        # 첨부파일 개수
        attachments = input_data.get("attachments", [])
        if len(attachments) > 10:
            warnings.append(f"첨부파일이 과다: {len(attachments)}개")

        return warnings

    def validate_item(self, item: Dict[str, Any]) -> Tuple[bool, Optional[str], List[str]]:
        """단일 항목 전체 검증.

        Args:
            item: 검증할 데이터 항목

        Returns:
            (유효성 여부, 오류 메시지, 경고 메시지 리스트)
        """
        # 1. JSON 구조 검증
        is_valid, error = self.validate_json_structure(item)
        if not is_valid:
            return False, error, []

        # 2. 데이터 타입 검증
        is_valid, error = self.validate_data_types(item)
        if not is_valid:
            return False, error, []

        # 3. 데이터 값 검증
        is_valid, error, warnings = self.validate_data_values(item)
        if not is_valid:
            return False, error, warnings

        # 4. 이상치 탐지
        outlier_warnings = self.detect_outliers(item)
        warnings.extend(outlier_warnings)

        return True, None, warnings

    def validate_jsonl_file(
        self, file_path: Path, collect_stats: bool = True
    ) -> Tuple[List[Dict], List[Dict], Dict[str, Any]]:
        """JSONL 파일 전체 검증.

        Args:
            file_path: 검증할 JSONL 파일 경로
            collect_stats: 통계 수집 여부

        Returns:
            (유효한 데이터 리스트, 무효한 데이터 리스트, 통계 딕셔너리)
        """
        valid_items = []
        invalid_items = []

        self.stats = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "errors": defaultdict(int),
            "warnings": defaultdict(int),
        }

        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                self.stats["total"] += 1

                try:
                    item = json.loads(line)
                except json.JSONDecodeError as e:
                    self.stats["invalid"] += 1
                    self.stats["errors"]["JSON 파싱 오류"] += 1
                    invalid_items.append(
                        {
                            "line": line_num,
                            "item": None,
                            "error": f"JSON 파싱 실패: {str(e)}",
                        }
                    )
                    continue

                # 검증 수행
                is_valid, error, warnings = self.validate_item(item)

                if is_valid:
                    self.stats["valid"] += 1
                    valid_items.append(item)

                    # 경고 기록
                    for warning in warnings:
                        self.stats["warnings"][warning] += 1
                else:
                    self.stats["invalid"] += 1
                    if error:
                        self.stats["errors"][error] += 1
                    invalid_items.append(
                        {
                            "line": line_num,
                            "item": item,
                            "error": error,
                            "warnings": warnings,
                        }
                    )

        return valid_items, invalid_items, dict(self.stats)

    def clean_and_save(
        self,
        input_path: Path,
        output_path: Path,
        save_invalid: bool = False,
        invalid_output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """데이터 정제 및 저장.

        Args:
            input_path: 입력 JSONL 파일 경로
            output_path: 출력 JSONL 파일 경로 (정제된 데이터)
            save_invalid: 무효한 데이터도 저장할지 여부
            invalid_output_path: 무효한 데이터 저장 경로

        Returns:
            통계 딕셔너리
        """
        print(f"[INFO] 데이터 품질 검증 시작: {input_path}")

        # 검증 수행
        valid_items, invalid_items, stats = self.validate_jsonl_file(input_path)

        print(f"[INFO] 검증 완료:")
        print(f"  - 총 샘플: {stats['total']}개")
        print(f"  - 유효 샘플: {stats['valid']}개")
        print(f"  - 무효 샘플: {stats['invalid']}개")

        if stats["errors"]:
            print(f"[INFO] 오류 유형:")
            for error_type, count in stats["errors"].items():
                print(f"  - {error_type}: {count}개")

        if stats["warnings"]:
            print(f"[INFO] 경고 유형:")
            for warning_type, count in list(stats["warnings"].items())[:10]:  # 상위 10개만
                print(f"  - {warning_type}: {count}개")

        # 유효한 데이터 저장
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            for item in valid_items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"[OK] 정제된 데이터 저장: {output_path} ({len(valid_items)}개)")

        # 무효한 데이터 저장 (선택적)
        if save_invalid and invalid_items and invalid_output_path:
            invalid_output_path.parent.mkdir(parents=True, exist_ok=True)
            with invalid_output_path.open("w", encoding="utf-8") as f:
                for invalid_item in invalid_items:
                    f.write(json.dumps(invalid_item, ensure_ascii=False) + "\n")
            print(f"[INFO] 무효한 데이터 저장: {invalid_output_path} ({len(invalid_items)}개)")

        return stats


# 주의: 이 파일의 main 함수는 transform_jsonl.py로 통합되었습니다.
# 개별 검증이 필요한 경우에만 아래 주석을 해제하여 사용하세요.

# def main():
#     """메인 실행 함수 (선택적 사용)."""
#     # 경로 설정
#     current_dir = Path(__file__).parent.parent.parent  # spam_agent -> service -> api
#     data_dir = current_dir / "data" / "sft_dataset"
#
#     # 입력 파일
#     input_file = data_dir / "sft_train.jsonl"
#
#     if not input_file.exists():
#         print(f"[ERROR] 파일을 찾을 수 없습니다: {input_file}")
#         return
#
#     # 출력 파일
#     output_file = data_dir / "sft_train_cleaned.jsonl"
#     invalid_file = data_dir / "sft_train_invalid.jsonl"
#
#     # 검증 및 정제 실행
#     validator = DataQualityValidator()
#     stats = validator.clean_and_save(
#         input_path=input_file,
#         output_path=output_file,
#         save_invalid=True,
#         invalid_output_path=invalid_file,
#     )
#
#     print()
#     print("[OK] 데이터 품질 검증 및 정제 완료!")
#     print(f"[INFO] 최종 통계:")
#     print(f"  - 유효 샘플: {stats['valid']}개 ({stats['valid']/stats['total']*100:.2f}%)")
#     print(f"  - 무효 샘플: {stats['invalid']}개 ({stats['invalid']/stats['total']*100:.2f}%)")
#
#
# if __name__ == "__main__":
#     main()

