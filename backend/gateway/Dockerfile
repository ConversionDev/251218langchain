# ============================================================================
# 통합 Dockerfile
# - Gateway + OAuth Service + User Service 통합 빌드
# - core.kanggyeonggu.store/oauthservice/Dockerfile 통합
# - core.kanggyeonggu.store/userservice/Dockerfile 통합
# ============================================================================

# 1단계: 빌드
# oauthservice/userservice: gradle:8.5-jdk21 사용
# api: eclipse-temurin:21-jdk 사용 (gradlew 사용을 위해 유지)
FROM eclipse-temurin:21-jdk AS builder
WORKDIR /app

# Gradle 파일 복사 (캐시 최적화)
COPY gradle gradle
COPY gradlew .
COPY build.gradle .
COPY settings.gradle .

# 소스 코드 복사
COPY src src

# 빌드 실행
# oauthservice/userservice: gradle build -x test
# api: ./gradlew clean build -x test --no-daemon (gradlew 사용)
RUN chmod +x gradlew && ./gradlew clean build -x test --no-daemon

# 2단계: 실행
# oauthservice/userservice: eclipse-temurin:21-jre-alpine (경량화)
# api: eclipse-temurin:21-jre (wget 설치 필요)
# 통합: eclipse-temurin:21-jre 사용 (healthcheck를 위한 wget 필요)
FROM eclipse-temurin:21-jre
WORKDIR /app

# wget 설치 (healthcheck용 - api의 docker-compose.yaml에서 사용)
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# 빌드된 JAR 파일 복사
COPY --from=builder /app/build/libs/*.jar app.jar

# 포트 노출
EXPOSE 8080

# 실행
# oauthservice/userservice: -XX:MaxRAMPercentage=75.0 옵션 사용 (메모리 최적화)
# api: 기본 옵션 사용
# 통합: 메모리 최적화 옵션 추가
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]