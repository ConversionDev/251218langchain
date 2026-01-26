"""
V10 데이터 로더 - 하이브리드 버전

JSONL 파일에서 데이터를 읽어 관계형 테이블(SQLAlchemy)과 벡터 스토어(PGVector)에 동시에 저장합니다.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from core.database import get_v10_vector_store, V10SessionLocal  # type: ignore
from core.config import get_settings  # type: ignore
from domain.v10.member.bases.player import Player  # type: ignore
from domain.v10.member.bases.team import Team  # type: ignore
from domain.v10.member.bases.schedule import Schedule  # type: ignore
from domain.v10.member.bases.stadium import Stadium  # type: ignore


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """JSONL 파일을 로드합니다."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[WARNING] JSON 파싱 오류 (건너뜀): {e}")
    return data


def player_to_text(item: Dict[str, Any]) -> str:
    """선수 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("player_name"):
        parts.append(f"선수 {item['player_name']}")

    if item.get("team_code"):
        parts.append(f"팀 코드: {item['team_code']}")

    if item.get("position"):
        position_map = {
            "GK": "골키퍼",
            "DF": "수비수",
            "MF": "미드필더",
            "FW": "공격수"
        }
        position_kr = position_map.get(item["position"], item["position"])
        parts.append(f"포지션: {position_kr} ({item['position']})")

    if item.get("back_no"):
        parts.append(f"등번호: {item['back_no']}번")

    if item.get("nation"):
        parts.append(f"국적: {item['nation']}")

    if item.get("join_yyyy"):
        parts.append(f"입단 연도: {item['join_yyyy']}년")

    if item.get("birth_date"):
        parts.append(f"생년월일: {item['birth_date']}")

    if item.get("height"):
        parts.append(f"키: {item['height']}cm")

    if item.get("weight"):
        parts.append(f"몸무게: {item['weight']}kg")

    if item.get("e_player_name"):
        parts.append(f"영문 이름: {item['e_player_name']}")

    if item.get("nickname"):
        parts.append(f"별명: {item['nickname']}")

    return ". ".join(parts) + "."


def team_to_text(item: Dict[str, Any]) -> str:
    """팀 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("team_name"):
        parts.append(f"팀 이름: {item['team_name']}")

    if item.get("e_team_name"):
        parts.append(f"영문 팀명: {item['e_team_name']}")

    if item.get("region_name"):
        parts.append(f"지역: {item['region_name']}")

    if item.get("team_code"):
        parts.append(f"팀 코드: {item['team_code']}")

    if item.get("orig_yyyy"):
        parts.append(f"창단 연도: {item['orig_yyyy']}년")

    if item.get("stadium_code"):
        parts.append(f"홈 경기장 코드: {item['stadium_code']}")

    if item.get("address"):
        parts.append(f"주소: {item['address']}")

    if item.get("tel"):
        parts.append(f"전화번호: {item['tel']}")

    if item.get("homepage"):
        parts.append(f"홈페이지: {item['homepage']}")

    if item.get("owner"):
        parts.append(f"구단주: {item['owner']}")

    return ". ".join(parts) + "."


def stadium_to_text(item: Dict[str, Any]) -> str:
    """경기장 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("statdium_name"):
        parts.append(f"경기장 이름: {item['statdium_name']}")

    if item.get("stadium_code"):
        parts.append(f"경기장 코드: {item['stadium_code']}")

    if item.get("hometeam_code"):
        parts.append(f"홈팀 코드: {item['hometeam_code']}")

    if item.get("seat_count"):
        parts.append(f"좌석 수: {item['seat_count']:,}석")

    if item.get("address"):
        parts.append(f"주소: {item['address']}")

    if item.get("tel"):
        parts.append(f"전화번호: {item['tel']}")

    if item.get("ddd"):
        parts.append(f"지역번호: {item['ddd']}")

    return ". ".join(parts) + "."


def schedule_to_text(item: Dict[str, Any]) -> str:
    """경기 일정 데이터를 자연어 텍스트로 변환합니다."""
    parts = []

    if item.get("sche_date"):
        date_str = item["sche_date"]
        if len(date_str) == 8:
            formatted_date = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:8]}일"
            parts.append(f"경기 일자: {formatted_date}")
        else:
            parts.append(f"경기 일자: {date_str}")

    if item.get("stadium_code"):
        parts.append(f"경기장 코드: {item['stadium_code']}")

    if item.get("hometeam_code"):
        parts.append(f"홈팀 코드: {item['hometeam_code']}")

    if item.get("awayteam_code"):
        parts.append(f"원정팀 코드: {item['awayteam_code']}")

    if item.get("gubun"):
        gubun_map = {"Y": "정규 경기", "N": "비정규 경기"}
        parts.append(f"경기 구분: {gubun_map.get(item['gubun'], item['gubun'])}")

    if item.get("home_score") is not None and item.get("away_score") is not None:
        parts.append(
            f"경기 결과: {item['hometeam_code']} {item['home_score']} : "
            f"{item['away_score']} {item['awayteam_code']}"
        )

    return ". ".join(parts) + "."


def load_teams_hybrid(
    jsonl_path: Path,
    db: Session,
    vector_store,
    batch_size: int = 100
) -> Dict[str, int]:
    """팀 데이터를 관계형 테이블과 벡터 스토어에 동시에 로드합니다."""
    try:
        data = load_jsonl(jsonl_path)
        db_count = 0
        vector_documents = []

        for item in data:
            # 관계형 테이블에 저장
            existing = db.query(Team).filter(Team.id == item["id"]).first()
            if not existing:
                team = Team(
                    id=item["id"],
                    team_code=item.get("team_code", ""),
                    region_name=item.get("region_name"),
                    team_name=item.get("team_name", ""),
                    e_team_name=item.get("e_team_name"),
                    orig_yyyy=item.get("orig_yyyy"),
                    stadium_id=item.get("stadium_id"),
                    zip_code1=item.get("zip_code1"),
                    zip_code2=item.get("zip_code2"),
                    address=item.get("address"),
                    ddd=item.get("ddd"),
                    tel=item.get("tel"),
                    fax=item.get("fax"),
                    homepage=item.get("homepage"),
                    owner=item.get("owner"),
                )
                db.add(team)
                db_count += 1

            # 벡터 스토어용 문서 생성
            text = team_to_text(item)
            metadata = {
                "id": item.get("id"),
                "type": "team",
                "team_code": item.get("team_code"),
                "team_name": item.get("team_name"),
                "region_name": item.get("region_name"),
                "stadium_id": item.get("stadium_id"),
                "stadium_code": item.get("stadium_code"),
                "orig_yyyy": item.get("orig_yyyy"),
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}
            vector_documents.append(Document(page_content=text, metadata=metadata))

            if len(vector_documents) >= batch_size:
                vector_store.add_documents(vector_documents)
                vector_documents = []

        db.commit()

        # 남은 벡터 문서 저장
        if vector_documents:
            vector_store.add_documents(vector_documents)

        return {"db": db_count, "vector": len(data)}
    except Exception as e:
        db.rollback()
        raise Exception(f"팀 데이터 로드 실패: {str(e)}")


def load_stadiums_hybrid(
    jsonl_path: Path,
    db: Session,
    vector_store,
    batch_size: int = 100
) -> Dict[str, int]:
    """경기장 데이터를 관계형 테이블과 벡터 스토어에 동시에 로드합니다."""
    try:
        data = load_jsonl(jsonl_path)
        db_count = 0
        vector_documents = []

        for item in data:
            # 관계형 테이블에 저장
            existing = db.query(Stadium).filter(Stadium.id == item["id"]).first()
            if not existing:
                stadium = Stadium(
                    id=item["id"],
                    stadium_code=item.get("stadium_code", ""),
                    statdium_name=item.get("statdium_name", ""),
                    hometeam_id=item.get("hometeam_id"),
                    hometeam_code=item.get("hometeam_code"),
                    seat_count=item.get("seat_count"),
                    address=item.get("address"),
                    ddd=item.get("ddd"),
                    tel=item.get("tel"),
                )
                db.add(stadium)
                db_count += 1

            # 벡터 스토어용 문서 생성
            text = stadium_to_text(item)
            metadata = {
                "id": item.get("id"),
                "type": "stadium",
                "stadium_code": item.get("stadium_code"),
                "stadium_name": item.get("statdium_name"),
                "hometeam_id": item.get("hometeam_id"),
                "hometeam_code": item.get("hometeam_code"),
                "seat_count": item.get("seat_count"),
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}
            vector_documents.append(Document(page_content=text, metadata=metadata))

            if len(vector_documents) >= batch_size:
                vector_store.add_documents(vector_documents)
                vector_documents = []

        db.commit()

        # 남은 벡터 문서 저장
        if vector_documents:
            vector_store.add_documents(vector_documents)

        return {"db": db_count, "vector": len(data)}
    except Exception as e:
        db.rollback()
        raise Exception(f"경기장 데이터 로드 실패: {str(e)}")


def load_players_hybrid(
    jsonl_path: Path,
    db: Session,
    vector_store,
    batch_size: int = 100
) -> Dict[str, Any]:
    """선수 데이터를 관계형 테이블과 벡터 스토어에 동시에 로드합니다."""
    try:
        data = load_jsonl(jsonl_path)
        db_count = 0
        vector_count = 0
        skipped_count = 0
        skipped_team_ids = set()
        vector_documents = []

        for item in data:
            team_id = item.get("team_id")

            # team_id가 없으면 건너뛰기
            if not team_id:
                skipped_count += 1
                print(f"[WARNING] 선수 ID {item.get('id')} ({item.get('player_name', 'Unknown')}): team_id가 없어 건너뜀")
                continue

            # team_id가 teams 테이블에 존재하는지 확인
            team_exists = db.query(Team).filter(Team.id == team_id).first()
            if not team_exists:
                skipped_count += 1
                skipped_team_ids.add(team_id)
                print(f"[WARNING] 선수 ID {item.get('id')} ({item.get('player_name', 'Unknown')}): team_id={team_id}가 teams 테이블에 존재하지 않아 건너뜀")
                # 벡터 스토어에는 저장 (참조 무결성 문제 없음)
                text = player_to_text(item)
                metadata = {
                    "id": item.get("id"),
                    "type": "player",
                    "team_id": team_id,
                    "team_code": item.get("team_code"),
                    "player_name": item.get("player_name"),
                    "position": item.get("position"),
                    "back_no": item.get("back_no"),
                    "nation": item.get("nation"),
                    "join_yyyy": item.get("join_yyyy"),
                }
                metadata = {k: v for k, v in metadata.items() if v is not None}
                vector_documents.append(Document(page_content=text, metadata=metadata))
                vector_count += 1
                continue

            # 관계형 테이블에 저장
            existing = db.query(Player).filter(Player.id == item["id"]).first()
            if not existing:
                player = Player(
                    id=item["id"],
                    team_id=team_id,
                    player_name=item.get("player_name", ""),
                    e_player_name=item.get("e_player_name"),
                    nickname=item.get("nickname"),
                    join_yyyy=item.get("join_yyyy"),
                    position=item.get("position"),
                    back_no=item.get("back_no"),
                    nation=item.get("nation"),
                    birth_date=item.get("birth_date"),
                    solar=item.get("solar"),
                    height=item.get("height"),
                    weight=item.get("weight"),
                )
                db.add(player)
                db_count += 1

            # 벡터 스토어용 문서 생성
            text = player_to_text(item)
            metadata = {
                "id": item.get("id"),
                "type": "player",
                "team_id": team_id,
                "team_code": item.get("team_code"),
                "player_name": item.get("player_name"),
                "position": item.get("position"),
                "back_no": item.get("back_no"),
                "nation": item.get("nation"),
                "join_yyyy": item.get("join_yyyy"),
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}
            vector_documents.append(Document(page_content=text, metadata=metadata))
            vector_count += 1

            if len(vector_documents) >= batch_size:
                vector_store.add_documents(vector_documents)
                vector_documents = []
                print(f"[INFO] 선수 {db_count}개 처리 중...")

        db.commit()

        # 남은 벡터 문서 저장
        if vector_documents:
            vector_store.add_documents(vector_documents)

        # 경고 메시지 출력
        if skipped_count > 0:
            print(f"[WARNING] 총 {skipped_count}개 선수가 건너뛰어졌습니다.")
            if skipped_team_ids:
                print(f"[WARNING] 존재하지 않는 team_id 목록: {sorted(skipped_team_ids)}")
                print("[INFO] teams 데이터를 먼저 업로드한 후 다시 시도하세요.")

        return {
            "db": db_count,
            "vector": vector_count,
            "skipped": skipped_count,
            "skipped_team_ids": list(skipped_team_ids) if skipped_team_ids else []
        }
    except Exception as e:
        db.rollback()
        raise Exception(f"선수 데이터 로드 실패: {str(e)}")


def load_schedules_hybrid(
    jsonl_path: Path,
    db: Session,
    vector_store,
    batch_size: int = 100
) -> Dict[str, Any]:
    """경기 일정 데이터를 관계형 테이블과 벡터 스토어에 동시에 로드합니다."""
    try:
        data = load_jsonl(jsonl_path)
        db_count = 0
        vector_count = 0
        skipped_count = 0
        skipped_stadium_ids = set()
        skipped_team_ids = set()
        vector_documents = []

        for item in data:
            stadium_id = item.get("stadium_id")
            hometeam_id = item.get("hometeam_id")
            awayteam_id = item.get("awayteam_id")

            # 필수 FK 검증
            skip_reason = None
            if not stadium_id:
                skip_reason = "stadium_id가 없음"
            elif not db.query(Stadium).filter(Stadium.id == stadium_id).first():
                skip_reason = f"stadium_id={stadium_id}가 stadiums 테이블에 존재하지 않음"
                skipped_stadium_ids.add(stadium_id)

            if not skip_reason:
                if not hometeam_id:
                    skip_reason = "hometeam_id가 없음"
                elif not db.query(Team).filter(Team.id == hometeam_id).first():
                    skip_reason = f"hometeam_id={hometeam_id}가 teams 테이블에 존재하지 않음"
                    skipped_team_ids.add(hometeam_id)

            if not skip_reason:
                if not awayteam_id:
                    skip_reason = "awayteam_id가 없음"
                elif not db.query(Team).filter(Team.id == awayteam_id).first():
                    skip_reason = f"awayteam_id={awayteam_id}가 teams 테이블에 존재하지 않음"
                    skipped_team_ids.add(awayteam_id)

            if skip_reason:
                skipped_count += 1
                print(f"[WARNING] 경기 일정 ID {item.get('id')} (날짜: {item.get('sche_date', 'Unknown')}): {skip_reason} - 건너뜀")
                # 벡터 스토어에는 저장 (참조 무결성 문제 없음)
                text = schedule_to_text(item)
                metadata = {
                    "id": item.get("id"),
                    "type": "schedule",
                    "stadium_id": stadium_id,
                    "stadium_code": item.get("stadium_code"),
                    "hometeam_id": hometeam_id,
                    "hometeam_code": item.get("hometeam_code"),
                    "awayteam_id": awayteam_id,
                    "awayteam_code": item.get("awayteam_code"),
                    "sche_date": item.get("sche_date"),
                    "gubun": item.get("gubun"),
                    "home_score": item.get("home_score"),
                    "away_score": item.get("away_score"),
                }
                metadata = {k: v for k, v in metadata.items() if v is not None}
                vector_documents.append(Document(page_content=text, metadata=metadata))
                vector_count += 1
                continue

            # 관계형 테이블에 저장
            existing = db.query(Schedule).filter(Schedule.id == item["id"]).first()
            if not existing:
                schedule = Schedule(
                    id=item["id"],
                    stadium_id=stadium_id,
                    hometeam_id=hometeam_id,
                    awayteam_id=awayteam_id,
                    stadium_code=item.get("stadium_code", ""),
                    sche_date=item.get("sche_date", ""),
                    gubun=item.get("gubun", ""),
                    hometeam_code=item.get("hometeam_code", ""),
                    awayteam_code=item.get("awayteam_code", ""),
                    home_score=item.get("home_score"),
                    away_score=item.get("away_score"),
                )
                db.add(schedule)
                db_count += 1

            # 벡터 스토어용 문서 생성
            text = schedule_to_text(item)
            metadata = {
                "id": item.get("id"),
                "type": "schedule",
                "stadium_id": stadium_id,
                "stadium_code": item.get("stadium_code"),
                "hometeam_id": hometeam_id,
                "hometeam_code": item.get("hometeam_code"),
                "awayteam_id": awayteam_id,
                "awayteam_code": item.get("awayteam_code"),
                "sche_date": item.get("sche_date"),
                "gubun": item.get("gubun"),
                "home_score": item.get("home_score"),
                "away_score": item.get("away_score"),
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}
            vector_documents.append(Document(page_content=text, metadata=metadata))
            vector_count += 1

            if len(vector_documents) >= batch_size:
                vector_store.add_documents(vector_documents)
                vector_documents = []
                print(f"[INFO] 경기 일정 {db_count}개 처리 중...")

        db.commit()

        # 남은 벡터 문서 저장
        if vector_documents:
            vector_store.add_documents(vector_documents)

        # 경고 메시지 출력
        if skipped_count > 0:
            print(f"[WARNING] 총 {skipped_count}개 경기 일정이 건너뛰어졌습니다.")
            if skipped_stadium_ids:
                print(f"[WARNING] 존재하지 않는 stadium_id 목록: {sorted(skipped_stadium_ids)}")
                print("[INFO] stadiums 데이터를 먼저 업로드한 후 다시 시도하세요.")
            if skipped_team_ids:
                print(f"[WARNING] 존재하지 않는 team_id 목록: {sorted(skipped_team_ids)}")
                print("[INFO] teams 데이터를 먼저 업로드한 후 다시 시도하세요.")

        return {
            "db": db_count,
            "vector": vector_count,
            "skipped": skipped_count,
            "skipped_stadium_ids": list(skipped_stadium_ids) if skipped_stadium_ids else [],
            "skipped_team_ids": list(skipped_team_ids) if skipped_team_ids else []
        }
    except Exception as e:
        db.rollback()
        raise Exception(f"경기 일정 데이터 로드 실패: {str(e)}")


def load_all_v10_data(
    data_dir: Optional[Path] = None,
    embeddings_model=None
) -> Dict[str, Any]:
    """
    모든 V10 데이터를 하이브리드 방식으로 로드합니다.
    관계형 테이블(SQLAlchemy)과 벡터 스토어(PGVector)에 동시에 저장합니다.

    Args:
        data_dir: 데이터 디렉토리 경로 (None이면 기본 경로 사용)
        embeddings_model: 임베딩 모델 (None이면 server에서 가져옴)

    Returns:
        각 타입별 로드된 레코드 수 (db와 vector 구분)
    """
    if data_dir is None:
        # app/data/soccer 디렉토리
        data_dir = Path(__file__).parent.parent.parent.parent / "data" / "soccer"

    # 임베딩 모델 가져오기
    if embeddings_model is None:
        try:
            from server import local_embeddings  # type: ignore
            if local_embeddings is None:
                raise ValueError("임베딩 모델이 초기화되지 않았습니다. 서버를 먼저 시작하세요.")
            embeddings_model = local_embeddings
        except ImportError:
            # 서버가 시작되지 않은 경우 직접 초기화
            from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore[import-untyped]
            print("[INFO] 임베딩 모델 초기화 중...")
            embeddings_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            print("[OK] 임베딩 모델 초기화 완료")

    # 벡터 스토어 생성
    settings = get_settings()
    vector_store = get_v10_vector_store(embeddings_model, settings.v10_collection_name)

    # 관계형 DB 세션 생성
    db = V10SessionLocal()
    results = {}

    try:
        # 순서 중요: FK 관계를 고려하여 순서대로 로드
        # 1. Stadiums (FK: hometeam_id -> teams.id, 하지만 nullable이므로 먼저 가능)
        # 2. Teams (FK: stadium_id -> stadiums.id, 하지만 nullable이므로 먼저 가능)
        # 3. Players (FK: team_id -> teams.id)
        # 4. Schedules (FK: stadium_id, hometeam_id, awayteam_id)

        print("[INFO] 경기장 데이터 로드 중 (하이브리드)...")
        stadiums_path = data_dir / "stadiums.jsonl"
        if stadiums_path.exists():
            results["stadiums"] = load_stadiums_hybrid(
                stadiums_path, db, vector_store
            )
            print(f"[OK] 경기장 DB: {results['stadiums']['db']}개, 벡터: {results['stadiums']['vector']}개 로드 완료")
        else:
            print(f"[WARNING] {stadiums_path} 파일을 찾을 수 없습니다.")
            results["stadiums"] = {"db": 0, "vector": 0}

        print("[INFO] 팀 데이터 로드 중 (하이브리드)...")
        teams_path = data_dir / "teams.jsonl"
        if teams_path.exists():
            results["teams"] = load_teams_hybrid(
                teams_path, db, vector_store
            )
            print(f"[OK] 팀 DB: {results['teams']['db']}개, 벡터: {results['teams']['vector']}개 로드 완료")
        else:
            print(f"[WARNING] {teams_path} 파일을 찾을 수 없습니다.")
            results["teams"] = {"db": 0, "vector": 0}

        print("[INFO] 선수 데이터 로드 중 (하이브리드)...")
        players_path = data_dir / "players.jsonl"
        if players_path.exists():
            results["players"] = load_players_hybrid(
                players_path, db, vector_store
            )
            print(f"[OK] 선수 DB: {results['players']['db']}개, 벡터: {results['players']['vector']}개 로드 완료")
        else:
            print(f"[WARNING] {players_path} 파일을 찾을 수 없습니다.")
            results["players"] = {"db": 0, "vector": 0}

        print("[INFO] 경기 일정 데이터 로드 중 (하이브리드)...")
        schedules_path = data_dir / "schedules.jsonl"
        if schedules_path.exists():
            results["schedules"] = load_schedules_hybrid(
                schedules_path, db, vector_store
            )
            print(f"[OK] 경기 일정 DB: {results['schedules']['db']}개, 벡터: {results['schedules']['vector']}개 로드 완료")
        else:
            print(f"[WARNING] {schedules_path} 파일을 찾을 수 없습니다.")
            results["schedules"] = {"db": 0, "vector": 0}

        print("[OK] 모든 V10 데이터 하이브리드 로드 완료!")
        return results

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 데이터 로드 실패: {e}")
        raise
    finally:
        db.close()
