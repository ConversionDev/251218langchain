# SSH 키 확인 가이드

## SSH 키 형식 확인

올바른 SSH 키 형식은 다음과 같습니다:

```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(여러 줄의 암호화된 키 데이터)
...
-----END RSA PRIVATE KEY-----
```

또는 OpenSSH 형식:

```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

## GitHub Secrets에 올바르게 설정하는 방법

1. **로컬에서 .pem 파일 열기**
   ```bash
   # Windows: 메모장이나 VS Code로 열기
   # 파일 경로 예: C:\Users\hi\Documents\project\RAG\Kjun.pem
   ```

2. **전체 내용 복사**
   - `-----BEGIN`부터 `-----END`까지 모든 줄 포함
   - 앞뒤 공백 제거
   - 줄바꿈은 그대로 유지

3. **GitHub Secrets에 붙여넣기**
   - Repository → Settings → Secrets and variables → Actions
   - `EC2_SSH_KEY` 선택 또는 생성
   - 복사한 키 전체를 Value에 붙여넣기
   - Save 클릭

## 주의사항

- ❌ 키 파일 경로를 입력하지 마세요 (예: `Kjun.pem`)
- ❌ 키 파일 이름을 입력하지 마세요
- ✅ 키 파일의 **전체 내용**을 복사해야 합니다
- ✅ BEGIN과 END 줄도 포함해야 합니다

## 새 EC2 인스턴스인 경우

EC2 인스턴스를 새로 생성했다면:
1. 새 키 페어(.pem 파일) 다운로드 필요
2. 해당 키 파일의 전체 내용을 `EC2_SSH_KEY`에 설정
3. 기존 키와 새 키는 다르므로 기존 키로는 접속 불가

