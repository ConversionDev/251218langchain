# Vercel ↔ AWS EC2 연결 설정 가이드

## 개요

프론트엔드(Vercel)와 백엔드(AWS EC2)를 연결하여 전체 애플리케이션을 프로덕션 환경에서 운영하기 위한 설정 가이드입니다.

## 아키텍처

```
┌─────────────────────────────────────────┐
│   kanggyeonggu.store (Vercel)           │
│   프론트엔드 (Next.js)                   │
│   - 도메인: kanggyeonggu.store           │
│   - 배포: Vercel 자동 배포               │
└─────────────────────────────────────────┘
              │
              │ API 호출
              │ BACKEND_URL 환경 변수
              ▼
┌─────────────────────────────────────────┐
│   AWS EC2 (FastAPI Backend)             │
│   - Public IP: 15.164.225.70            │
│   - Port: 8000                          │
│   - 배포: GitHub Actions                 │
└─────────────────────────────────────────┘
```

## 사전 준비사항

- ✅ Vercel에 프론트엔드 배포 완료
- ✅ AWS EC2에 백엔드 배포 완료 (GitHub Actions)
- ✅ 개인 도메인 연결 완료 (kanggyeonggu.store)

## 설정 단계

### 1단계: EC2 보안 그룹 설정

EC2 인스턴스의 보안 그룹에 포트 8000을 열어야 Vercel에서 백엔드로 요청을 보낼 수 있습니다.

#### 설정 방법

1. **AWS 콘솔 접속**
   - EC2 → Instances → 인스턴스 선택

2. **Security 탭 확인**
   - 인스턴스 상세 페이지 → **Security** 탭
   - Security groups 링크 클릭

3. **인바운드 규칙 편집**
   - **Edit inbound rules** 클릭
   - **Add rule** 클릭

4. **포트 8000 규칙 추가**
   ```
   Type:        Custom TCP
   Protocol:    TCP
   Port range:  8000
   Source:      0.0.0.0/0 (Anywhere-IPv4)
   Description: FastAPI Backend for Vercel
   ```

5. **저장**
   - **Save rules** 클릭

#### 중요 사항

- **Source를 `0.0.0.0/0`으로 설정**: Vercel은 다양한 IP 주소를 사용하므로 모든 IP에서 접근 가능하도록 설정해야 합니다.
- 특정 IP만 허용하면 Vercel에서 접근할 수 없습니다.

---

### 2단계: EC2 Public IP 확인

Vercel 환경 변수에 EC2의 Public IP 주소가 필요합니다.

#### 확인 방법

1. **EC2 콘솔 접속**
   - EC2 → Instances → 인스턴스 선택

2. **Details 탭 확인**
   - 하단 **Details** 탭에서 다음 정보 확인:
     ```
     Instance ID:           i-0e4e5ccea050d2dc0
     Public IPv4 address:  15.164.225.70  ← 이 값 사용
     Private IPv4 address: 172.31.32.77
     ```

#### 현재 설정값

```
EC2 Public IP: 15.164.225.70
BACKEND_URL:   http://15.164.225.70:8000
```

> **참고**: Elastic IP를 사용하지 않는 경우, 인스턴스를 재시작하면 Public IP가 변경될 수 있습니다. 프로덕션 환경에서는 Elastic IP 사용을 권장합니다.

---

### 3단계: Vercel 환경 변수 설정

프론트엔드에서 백엔드 API를 호출하기 위해 Vercel에 환경 변수를 설정합니다.

#### 설정 방법

1. **Vercel 대시보드 접속**
   - https://vercel.com → 프로젝트 선택

2. **Settings 메뉴**
   - 프로젝트 → **Settings** → **Environment Variables**

3. **환경 변수 추가**
   ```
   Key:   BACKEND_URL
   Value: http://15.164.225.70:8000
   ```

4. **환경 선택**
   - ✅ Production
   - ✅ Preview
   - ✅ Development (로컬 개발용은 localhost 사용 가능)

5. **저장**
   - **Save** 클릭

#### 환경 변수 설명

- **BACKEND_URL**: 프론트엔드에서 백엔드 API를 호출할 때 사용하는 기본 URL
- 프론트엔드 코드 (`frontend/app/api/chat/route.ts`)에서 다음과 같이 사용:
  ```typescript
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  ```

---

### 4단계: Vercel 재배포

환경 변수를 추가한 후에는 재배포해야 변경사항이 적용됩니다.

#### 재배포 방법

1. **Deployments 탭**
   - Vercel 대시보드 → **Deployments** 탭

2. **최근 배포 선택**
   - 가장 최근 배포 항목 클릭

3. **Redeploy 실행**
   - 우측 상단 **⋯** 메뉴 → **Redeploy**

또는

- **Deployments** 탭 → **Redeploy** 버튼 클릭

#### 배포 확인

- 배포 상태가 **Ready**가 될 때까지 대기 (약 1-2분)
- 배포 로그에서 오류가 없는지 확인

---

### 5단계: 연결 테스트

프론트엔드에서 백엔드로의 연결이 정상적으로 작동하는지 확인합니다.

#### 테스트 방법

1. **프론트엔드 접속**
   - https://kanggyeonggu.store 접속

2. **챗봇 테스트**
   - 챗봇에 메시지 전송
   - 예: "한국 수도가 뭐야"

3. **정상 응답 확인**
   - ✅ 정상: 챗봇이 응답을 반환
   - ❌ 오류: "백엔드 서버에 연결할 수 없습니다" 메시지 표시

#### 트러블슈팅

**오류 발생 시 확인사항:**

1. **EC2 보안 그룹**
   - 포트 8000이 `0.0.0.0/0`으로 열려있는지 확인

2. **EC2 인스턴스 상태**
   - 인스턴스가 **Running** 상태인지 확인
   - 백엔드 서버가 정상 실행 중인지 확인

3. **Vercel 환경 변수**
   - `BACKEND_URL`이 올바르게 설정되었는지 확인
   - 재배포가 완료되었는지 확인

4. **백엔드 로그 확인**
   - EC2에서 백엔드 로그 확인:
     ```bash
     tail -f /home/ubuntu/app.log
     ```

---

## 현재 설정 요약

### 프론트엔드 (Vercel)
- **도메인**: kanggyeonggu.store
- **배포 플랫폼**: Vercel
- **환경 변수**: `BACKEND_URL=http://15.164.225.70:8000`

### 백엔드 (AWS EC2)
- **인스턴스 ID**: i-0e4e5ccea050d2dc0
- **Public IP**: 15.164.225.70
- **포트**: 8000
- **배포**: GitHub Actions (자동)
- **보안 그룹**: 포트 8000 (0.0.0.0/0 허용)

---

## 향후 개선 사항

### 1. HTTPS 적용 (권장)

현재는 HTTP로 연결되어 있습니다. 프로덕션 환경에서는 HTTPS를 사용하는 것이 좋습니다.

**방법:**
- 서브도메인 사용: `api.kanggyeonggu.store`
- Nginx + Let's Encrypt로 SSL 인증서 적용
- Vercel 환경 변수: `BACKEND_URL=https://api.kanggyeonggu.store`

### 2. Elastic IP 사용

EC2 인스턴스를 재시작하면 Public IP가 변경될 수 있습니다. Elastic IP를 사용하면 IP 주소를 고정할 수 있습니다.

**설정 방법:**
1. EC2 → Elastic IPs → Allocate Elastic IP address
2. 인스턴스에 할당
3. Vercel 환경 변수 업데이트

### 3. 도메인 기반 연결

서브도메인을 사용하면 IP 변경에 대응하기 쉽습니다.

**예시:**
- 프론트엔드: `kanggyeonggu.store`
- 백엔드: `api.kanggyeonggu.store`

### 4. CORS 설정 확인

백엔드에서 Vercel 도메인을 허용하도록 CORS 설정이 되어 있는지 확인:

```python
# api/app/api_server.py
origins = [
    "https://kanggyeonggu.store",
    "https://www.kanggyeonggu.store",
    "http://localhost:3000",  # 로컬 개발용
]
```

---

## 관련 파일

- **프론트엔드 API 라우트**: `frontend/app/api/chat/route.ts`
- **백엔드 API 서버**: `api/app/api_server.py`
- **GitHub Actions 배포**: `.github/workflows/deploy.yml`

---

## 참고 자료

- [Vercel 환경 변수 문서](https://vercel.com/docs/concepts/projects/environment-variables)
- [AWS EC2 보안 그룹 문서](https://docs.aws.amazon.com/AEC2/latest/UserGuide/working-with-security-groups.html)
- [Next.js 환경 변수 문서](https://nextjs.org/docs/basic-features/environment-variables)

---

**작성일**: 2025-12-22
**상태**: ✅ 정상 작동 확인 완료

