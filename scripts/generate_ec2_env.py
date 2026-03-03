#!/usr/bin/env python3
"""로컬 .env를 읽어 EC2에서 쓸 env 파일을 생성합니다.

로컬에서 먼저 테스트 권장:
  - 프로젝트 루트에서 .env 로드된 상태로 API 실행 (예: cd app && python main.py)
  - Mailgun 웹훅 테스트: POST http://localhost:8000/api/mail/receive/webhook/mailgun
  - 검증 후 EC2 배포 및 scripts/ec2.env 또는 GitHub Secrets 사용

실행: 프로젝트 루트(RAG/)에서
  python scripts/generate_ec2_env.py

생성 파일: scripts/ec2.env (KEY=value 형식, .gitignore에 의해 커밋 제외)

EC2 반영 방법 (둘 중 하나):
  1) 생성된 파일을 EC2로 복사 후 ~/.env 로 두기 (앱이 get_project_root()/.env 로 로드)
     scp scripts/ec2.env ubuntu@<EC2_HOST>:/home/ubuntu/.env

  2) EC2에서 nano로 열어서 확인/수정 후 저장
     nano /home/ubuntu/.env
     (내용은 이미 ec2.env에 있으므로 scp 후 nano로 열면 동일 내용이 보임)
"""

from pathlib import Path
import re
import sys


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"
    out_path = root / "scripts" / "ec2.env"

    if not env_path.exists():
        print(f"[ERROR] .env not found: {env_path}", file=sys.stderr)
        sys.exit(1)

    lines: list[str] = []
    with open(env_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n\r")
            # 주석·빈 줄 제외
            if not line.strip() or line.strip().startswith("#"):
                continue
            # KEY=value 형태만 (KEY는 영문/숫자/밑줄)
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", line):
                lines.append(line)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")

    print(f"OK Generated: {out_path} ({len(lines)} vars)")
    print()
    print("EC2: scp scripts/ec2.env ubuntu@<EC2_HOST>:/home/ubuntu/.env")
    print("      then on EC2: nano /home/ubuntu/.env to review/edit")


if __name__ == "__main__":
    main()
