"""
app/data — 도메인별 데이터 패키지.

폴더 구조는 도메인마다 prepared / raw / sft 를 통일해 사용합니다.
경로는 core.paths.get_data_dir() 으로만 사용하고, 이 패키지에서는 경로를 export하지 않습니다.

서브패키지:
- disclosure: 공시 문서 (prepared 텍스트 등)
- spam: 스팸 SFT (sft/exaone_synthetic.jsonl, train.jsonl, val.jsonl 등)
- competency_anchors: 역량 앵커
"""

__all__: list[str] = []
