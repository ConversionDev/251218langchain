package store.kanggyeonggu.gateway.jwt;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import store.kanggyeonggu.gateway.common.entity.RefreshToken;
import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.common.repository.RefreshTokenRepository;
import store.kanggyeonggu.gateway.common.repository.UserRepository;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

/**
 * Refresh Token 관리 서비스
 * 
 * 저장소:
 * - Neon DB (PostgreSQL): Refresh Token 영구 저장
 * - HttpOnly 쿠키: 브라우저에 토큰 전달
 * 
 * 보안 원칙:
 * - Refresh Token은 HttpOnly 쿠키로만 저장
 * - JavaScript에서 접근 불가 (XSS 방어)
 * - Secure 플래그로 HTTPS에서만 전송 (프로덕션)
 * - SameSite로 CSRF 방어
 * - Token Rotation으로 재사용 공격 방지
 */
@Service
public class RefreshTokenService {

    private final RefreshTokenRepository refreshTokenRepository;
    private final UserRepository userRepository;

    @Value("${jwt.refresh-expiration:604800000}") // 7일 (밀리초)
    private long refreshExpiration;

    @Value("${app.cookie.secure:false}") // 로컬: false, 프로덕션: true
    private boolean cookieSecure;

    @Value("${app.cookie.domain:}") // 프로덕션: .kanggyeonggu.store
    private String cookieDomain;

    private static final String REFRESH_TOKEN_COOKIE_NAME = "refresh_token";

    public RefreshTokenService(RefreshTokenRepository refreshTokenRepository, UserRepository userRepository) {
        this.refreshTokenRepository = refreshTokenRepository;
        this.userRepository = userRepository;
    }

    // ========================================
    // 토큰 생성 및 저장 (Neon DB)
    // ========================================

    /**
     * Refresh Token 생성 (UUID 기반)
     */
    public String generateRefreshToken() {
        return UUID.randomUUID().toString();
    }

    /**
     * Refresh Token 생성 및 Neon DB에 저장
     * 
     * @param user 사용자 엔티티
     * @param deviceInfo 디바이스 정보 (User-Agent)
     * @param ipAddress 클라이언트 IP 주소
     * @return 생성된 Refresh Token 문자열
     */
    @Transactional
    public String createAndSaveRefreshToken(User user, String deviceInfo, String ipAddress) {
        String tokenValue = generateRefreshToken();
        
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expiresAt = now.plusSeconds(refreshExpiration / 1000);
        
        RefreshToken refreshToken = RefreshToken.builder()
                .user(user)
                .token(tokenValue)
                .deviceInfo(deviceInfo)
                .ipAddress(ipAddress)
                .issuedAt(now)
                .expiresAt(expiresAt)
                .revoked(false)
                .build();
        
        refreshTokenRepository.save(refreshToken);
        
        System.out.println("✅ Refresh Token Neon DB 저장 완료: userId=" + user.getId());
        
        return tokenValue;
    }

    /**
     * Refresh Token 생성 및 Neon DB에 저장 (간단 버전)
     */
    @Transactional
    public String createAndSaveRefreshToken(User user) {
        return createAndSaveRefreshToken(user, null, null);
    }

    /**
     * Refresh Token 생성 및 Neon DB에 저장 (userId로)
     */
    @Transactional
    public String createAndSaveRefreshToken(Long userId, String deviceInfo, String ipAddress) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found: " + userId));
        return createAndSaveRefreshToken(user, deviceInfo, ipAddress);
    }

    // ========================================
    // 토큰 검증 및 조회 (Neon DB)
    // ========================================

    /**
     * Refresh Token 검증 및 사용자 ID 반환
     * 
     * @param tokenValue Refresh Token 문자열
     * @return 유효한 경우 userId, 유효하지 않으면 null
     */
    public Long validateRefreshToken(String tokenValue) {
        Optional<RefreshToken> tokenOpt = refreshTokenRepository.findValidToken(
                tokenValue, LocalDateTime.now());
        
        if (tokenOpt.isPresent()) {
            RefreshToken token = tokenOpt.get();
            System.out.println("✅ Refresh Token 검증 성공: userId=" + token.getUser().getId());
            return token.getUser().getId();
        }
        
        System.out.println("❌ Refresh Token 검증 실패: 유효하지 않거나 만료됨");
        return null;
    }

    /**
     * Refresh Token으로 User 엔티티 조회
     */
    public Optional<User> getUserByRefreshToken(String tokenValue) {
        return refreshTokenRepository.findValidToken(tokenValue, LocalDateTime.now())
                .map(RefreshToken::getUser);
    }

    // ========================================
    // 토큰 무효화 (로그아웃)
    // ========================================

    /**
     * 특정 Refresh Token 무효화
     */
    @Transactional
    public boolean revokeRefreshToken(String tokenValue) {
        int updated = refreshTokenRepository.revokeByToken(tokenValue, LocalDateTime.now());
        if (updated > 0) {
            System.out.println("✅ Refresh Token 무효화 완료");
            return true;
        }
        System.out.println("❌ Refresh Token 무효화 실패: 토큰 없음");
        return false;
    }

    /**
     * 사용자의 모든 Refresh Token 무효화 (전체 로그아웃)
     */
    @Transactional
    public int revokeAllUserTokens(Long userId) {
        int count = refreshTokenRepository.revokeAllByUserId(userId, LocalDateTime.now());
        System.out.println("✅ 사용자 전체 토큰 무효화: userId=" + userId + ", count=" + count);
        return count;
    }

    // ========================================
    // Token Rotation (갱신 시 새 토큰 발급)
    // ========================================

    /**
     * Refresh Token Rotation
     * 기존 토큰 무효화 후 새 토큰 발급
     * 
     * @param oldTokenValue 기존 Refresh Token
     * @return 새 Refresh Token (실패 시 null)
     */
    @Transactional
    public String rotateRefreshToken(String oldTokenValue) {
        Optional<RefreshToken> oldTokenOpt = refreshTokenRepository.findValidToken(
                oldTokenValue, LocalDateTime.now());
        
        if (oldTokenOpt.isEmpty()) {
            System.out.println("❌ Token Rotation 실패: 유효하지 않은 토큰");
            return null;
        }
        
        RefreshToken oldToken = oldTokenOpt.get();
        User user = oldToken.getUser();
        
        // 기존 토큰 무효화
        oldToken.revoke();
        refreshTokenRepository.save(oldToken);
        
        // 새 토큰 생성 및 저장
        String newTokenValue = createAndSaveRefreshToken(
                user, 
                oldToken.getDeviceInfo(), 
                oldToken.getIpAddress());
        
        System.out.println("✅ Token Rotation 완료: userId=" + user.getId());
        
        return newTokenValue;
    }

    // ========================================
    // 쿠키 관리
    // ========================================

    /**
     * HttpOnly 쿠키로 Refresh Token 설정
     * 
     * 로컬 개발: SameSite 생략 (cross-port 쿠키 전송 허용)
     * 프로덕션: SameSite=None + Secure (cross-origin 허용, HTTPS 필수)
     */
    public void setRefreshTokenCookie(HttpServletResponse response, String refreshToken) {
        String cookieHeader;
        
        if (cookieSecure) {
            // 프로덕션: HTTPS + SameSite=None
            if (cookieDomain != null && !cookieDomain.isEmpty()) {
                cookieHeader = String.format(
                        "%s=%s; Path=/; Max-Age=%d; HttpOnly; Secure; SameSite=None; Domain=%s",
                        REFRESH_TOKEN_COOKIE_NAME,
                        refreshToken,
                        (int) (refreshExpiration / 1000),
                        cookieDomain);
            } else {
                cookieHeader = String.format(
                        "%s=%s; Path=/; Max-Age=%d; HttpOnly; Secure; SameSite=None",
                        REFRESH_TOKEN_COOKIE_NAME,
                        refreshToken,
                        (int) (refreshExpiration / 1000));
            }
        } else {
            // 로컬 개발: SameSite 생략하여 cross-port 쿠키 전송 허용
            cookieHeader = String.format(
                    "%s=%s; Path=/; Max-Age=%d; HttpOnly",
                    REFRESH_TOKEN_COOKIE_NAME,
                    refreshToken,
                    (int) (refreshExpiration / 1000));
        }
        
        // Set-Cookie 헤더로 직접 설정 (SameSite 속성 지원)
        response.setHeader("Set-Cookie", cookieHeader);

        System.out.println("✅ Refresh Token 쿠키 설정 완료 (HttpOnly): " + 
                (cookieSecure ? "Secure + SameSite=None" : "로컬 개발 모드"));
    }

    /**
     * 쿠키에서 Refresh Token 읽기
     */
    public String getRefreshTokenFromCookie(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            System.out.println("❌ 쿠키 없음");
            return null;
        }

        for (Cookie cookie : cookies) {
            if (REFRESH_TOKEN_COOKIE_NAME.equals(cookie.getName())) {
                System.out.println("✅ Refresh Token 쿠키 발견");
                return cookie.getValue();
            }
        }
        
        System.out.println("❌ Refresh Token 쿠키 없음");
        return null;
    }

    /**
     * Refresh Token 쿠키 삭제 (로그아웃 시)
     */
    public void clearRefreshTokenCookie(HttpServletResponse response) {
        String cookieHeader;
        
        if (cookieSecure && cookieDomain != null && !cookieDomain.isEmpty()) {
            cookieHeader = String.format(
                    "%s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=None; Domain=%s",
                    REFRESH_TOKEN_COOKIE_NAME,
                    cookieDomain);
        } else if (cookieSecure) {
            cookieHeader = String.format(
                    "%s=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=None",
                    REFRESH_TOKEN_COOKIE_NAME);
        } else {
            cookieHeader = String.format(
                    "%s=; Path=/; Max-Age=0; HttpOnly",
                    REFRESH_TOKEN_COOKIE_NAME);
        }
        
        response.setHeader("Set-Cookie", cookieHeader);
        System.out.println("🗑️ Refresh Token 쿠키 삭제 완료");
    }

    /**
     * Refresh Token 만료 시간 반환 (밀리초)
     */
    public long getRefreshExpiration() {
        return refreshExpiration;
    }

    // ========================================
    // 정리 작업 (Scheduled Job용)
    // ========================================

    /**
     * 만료된 토큰 정리
     */
    @Transactional
    public int cleanupExpiredTokens() {
        int deleted = refreshTokenRepository.deleteExpiredTokens(LocalDateTime.now());
        System.out.println("🗑️ 만료된 토큰 정리: " + deleted + "개 삭제");
        return deleted;
    }

    /**
     * 무효화된 토큰 정리 (7일 이상 경과)
     */
    @Transactional
    public int cleanupRevokedTokens() {
        LocalDateTime cutoffDate = LocalDateTime.now().minusDays(7);
        int deleted = refreshTokenRepository.deleteRevokedTokens(cutoffDate);
        System.out.println("🗑️ 무효화된 토큰 정리: " + deleted + "개 삭제");
        return deleted;
    }
}
