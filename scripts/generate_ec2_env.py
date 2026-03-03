#!/usr/bin/env python3
"""로컬 .env를 읽어 EC2에서 쓸 env 파일을 생성합니다.

로컬에서 먼저 테스트 권장:
  - 프로젝트 루트에서 .env 로드된 상태로 API 실행 (예: cd app && python main.py)
  - Mailgun 웹훅 테스트: POST http://localhost:8000/api/mail/receive/webhook/mailgun
  - 검증 후 EC2 배포 및 scripts/ec2.env 또는 GitHub Secrets 사용

실행: 프로젝트 루트(RAG/)에서
  python scripts/generate_ec2_env.py

생성 파일: scripts/ec2.env (KEY=value 형식, .gitignore에 의해 커밋 제외)

EC2 반영: .env에 EC2_HOST=IP또는호스트 한 줄 넣으면 스크립트가 scp 명령 출력.
  --upload 옵션으로 scp 자동 실행 (RSA.pem 필요). 코드에 IP 넣지 않음.
"""

from pathlib import Path
import re
import subprocess
import sys


def _get_ec2_host(env_path: Path) -> str | None:
    """Read EC2_HOST from .env (for local use only; not written to ec2.env)."""
    if not env_path.exists():
        return None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("EC2_HOST="):
                val = line.split("=", 1)[1].strip().strip("'\"")
                return val if val else None
    return None


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"
    out_path = root / "scripts" / "ec2.env"
    do_upload = "--upload" in sys.argv or "-u" in sys.argv

    if not env_path.exists():
        print(f"[ERROR] .env not found: {env_path}", file=sys.stderr)
        sys.exit(1)

    lines: list[str] = []
    with open(env_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n\r")
            if not line.strip() or line.strip().startswith("#"):
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", line):
                if line.split("=", 1)[0].strip() == "EC2_HOST":
                    continue
                lines.append(line)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")

    print(f"OK Generated: {out_path} ({len(lines)} vars)")
    print()

    ec2_host = _get_ec2_host(env_path)
    if ec2_host:
        key_path = root / "RSA.pem"
        scp_cmd = ["scp"]
        if key_path.exists():
            scp_cmd.extend(["-i", str(key_path)])
        scp_cmd.extend([str(out_path), f"ubuntu@{ec2_host}:/home/ubuntu/.env"])
        print("EC2 .env 올리기:")
        print("  " + " ".join(scp_cmd))
        if do_upload:
            r = subprocess.run(scp_cmd)
            sys.exit(r.returncode)
        print("  (한 번에 올리려면: python scripts/generate_ec2_env.py --upload)")
    else:
        print(".env에 EC2_HOST=IP또는호스트 한 줄 넣으면 위에 scp 명령이 자동으로 채워집니다.")
        print("  예: EC2_HOST=3.37.129.223  (코드 수정 없이 .env만 유지)")


if __name__ == "__main__":
    main()
