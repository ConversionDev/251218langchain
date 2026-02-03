# Soccer JSONL 업로드: 데이터 흐름 및 기동 방법

## 데이터 흐름 (진입 HTTP 하나로 통일)

```
오케스트레이터(API) → HTTP → 허브(8000) → call_tool → 도메인 MCP(9031) → call_tool → 스포크(9032)
```

- **진입**: 프론트/클라이언트는 `POST /api/soccer/{stadium|team|player|schedule}/upload` 하나의 HTTP 진입만 사용.
- **허브(8000)**: FastAPI 앱. 업로드 요청을 받아 `/internal/soccer/call`로 내부 처리 후, Soccer MCP(9031)에 **call_tool** 위임.
- **도메인 MCP(9031)**: Soccer MCP. 허브의 call_tool을 받아 Soccer Spoke(9032)에 **call_tool**(process_stadium, process_player 등) 위임.
- **스포크(9032)**: Soccer Spoke. 실제 오케스트레이터(StadiumOrchestrator 등) 실행 및 DB/벡터 저장.

## 502 Bad Gateway가 나올 때

1. **Soccer MCP(9031) 미기동**  
   허브가 9031로 연결하지 못하면 502가 납니다. Soccer MCP를 먼저 띄우세요.

2. **Soccer Spoke(9032) 미기동**  
   MCP(9031)가 Spoke(9032)로 call_tool을 보내는데 9032가 꺼져 있으면 실패합니다. Soccer Spoke를 띄우세요.

3. **동기 HTTP 자기 호출**  
   같은 프로세스(8000)가 업로드 처리 중 동기로 `/internal/soccer/call`을 호출하면 이벤트 루프가 막혀 데드락 가능성이 있습니다.  
   이 프로젝트에서는 **비동기 `async_soccer_call`**를 사용해 같은 서버 자기 호출 시에도 데드락을 피합니다.

## 기동 순서 (stadiums → teams → players → schedules 업로드용)

### 단일 프로세스 (권장, env 없이)

1. **허브만 기동** — Soccer MCP·Spoke는 같은 프로세스에 마운트됨.  
   ```bash
   cd app && python main.py
   ```
2. 프론트에서 JSONL 업로드: 스타디움 → 팀 → 선수 → 스케줄 순으로 업로드.

### 별도 프로세스 (SOCCER_MCP_URL / SOCCER_SPOKE_MCP_URL 설정 시)

1. **허브(FastAPI)** — `cd app && python main.py` (기본 8000).
2. **Soccer Spoke(9032)** — `cd app && python -m scripts.run_soccer_spoke`.
3. **Soccer MCP(9031)** — `cd app && python -m scripts.run_soccer_mcp`.
4. 프론트에서 JSONL 업로드.

## 단일 프로세스 (env 없이)

**`python main.py`만 실행**하면 Soccer MCP·Spoke는 **같은 프로세스**에 `/mcp-soccer`, `/mcp-soccer-spoke`로 마운트됩니다.  
`SOCCER_MCP_URL`, `SOCCER_SPOKE_MCP_URL`을 **설정하지 않으면** (빈 문자열 기본값) `http://{host}:{port}/mcp-soccer/server`, `http://{host}:{port}/mcp-soccer-spoke/server`가 사용되므로 **별도 env 없이** 업로드가 동작합니다.

## 환경 변수 (별도 프로세스 시)

| 변수 | 기본값(단일 프로세스) | 설명 |
|------|------------------------|------|
| `HUB_SERVICE_URL` | `http://127.0.0.1:8000` | 허브 Base URL |
| `SOCCER_MCP_URL` | (비어 있음 → 같은 서버 `/mcp-soccer/server`) | Soccer MCP URL. 설정 시 9031 등 별도 프로세스 사용 |
| `SOCCER_SPOKE_MCP_URL` | (비어 있음 → 같은 서버 `/mcp-soccer-spoke/server`) | Soccer Spoke URL. 설정 시 9032 등 별도 프로세스 사용 |
