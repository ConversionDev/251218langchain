package store.kanggyeonggu.gateway.jwt;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import store.kanggyeonggu.gateway.common.entity.User;

import java.util.Map;
import java.util.Optional;

/**
 * Refresh Token 관련 API 컨트롤러
 * 
 * 저장소:
 * - Access Token: Upstash Redis
 * - Refresh Token: Neon DB (PostgreSQL)
 * 
 * 엔드포인트:
 * - POST /api/auth/refresh : Access Token 갱신
 * - POST /api/auth/logout : 로그아웃
 * - POST /api/auth/logout-all : 전체 로그아웃
 */
@RestController
@RequestMapping("/api/auth")
public class RefreshTokenController {

    private final RefreshTokenService refreshTokenService;
    private final AccessTokenService accessTokenService;
    private final JwtService jwtService;

    public RefreshTokenController(
            RefreshTokenService refreshTokenService,
            AccessTokenService accessTokenService,
            JwtService jwtService) {
        this.refreshTokenService = refreshTokenService;
        this.accessTokenService = accessTokenService;
        this.jwtService = jwtService;
    }

    /**
     * Access Token 갱신
     * 
     * HttpOnly 쿠키에서 Refresh Token을 읽어 Neon DB에서 검증 후 새 Access Token 발급
     * Token Rotation 적용 (보안 강화)
     * 
     * POST /api/auth/refresh
     * Cookie: refresh_token=xxx (자동 전송)
     * 
     * Response:
     * {
     *   "success": true,
     *   "accessToken": "eyJ..."
     * }
     */
    @PostMapping("/refresh")
    public ResponseEntity<?> refreshToken(
            HttpServletRequest request,
            HttpServletResponse response) {
        try {
            // 1. 쿠키에서 Refresh Token 읽기
            String refreshToken = refreshTokenService.getRefreshTokenFromCookie(request);

            if (refreshToken == null || refreshToken.isEmpty()) {
                System.out.println("❌ Refresh Token 쿠키 없음");
                return ResponseEntity.status(401).body(Map.of(
                        "success", false,
                        "message", "Refresh token not found"));
            }

            System.out.println("🔍 Refresh Token 확인: " + 
                    refreshToken.substring(0, Math.min(8, refreshToken.length())) + "...");

            // 2. Neon DB에서 Refresh Token 검증 및 User 조회
            Optional<User> userOptional = refreshTokenService.getUserByRefreshToken(refreshToken);

            if (userOptional.isEmpty()) {
                System.out.println("❌ Refresh Token이 Neon DB에 없거나 만료됨");
                refreshTokenService.clearRefreshTokenCookie(response);
                return ResponseEntity.status(401).body(Map.of(
                        "success", false,
                        "message", "Invalid or expired refresh token"));
            }

            User user = userOptional.get();
            System.out.println("✅ Refresh Token 검증 성공, userId: " + user.getId());

            // 3. 새 Access Token 발급
            String newAccessToken = jwtService.generateToken(user.getId(), user.getNickname());
            System.out.println("✅ 새 Access Token 발급 완료");

            // 4. 새 Access Token을 Redis에 저장 (Upstash)
            accessTokenService.saveAccessToken(newAccessToken, user.getId(), jwtService.getExpiration());
            System.out.println("✅ 새 Access Token Redis 저장 완료");

            // 5. Token Rotation: 기존 Refresh Token 무효화 + 새 토큰 발급 (Neon DB)
            String newRefreshToken = refreshTokenService.rotateRefreshToken(refreshToken);
            
            if (newRefreshToken == null) {
                System.out.println("❌ Token Rotation 실패");
                refreshTokenService.clearRefreshTokenCookie(response);
                return ResponseEntity.status(401).body(Map.of(
                        "success", false,
                        "message", "Token rotation failed"));
            }

            // 6. 새 Refresh Token 쿠키 설정
            refreshTokenService.setRefreshTokenCookie(response, newRefreshToken);
            System.out.println("✅ 새 Refresh Token 발급 및 쿠키 설정 완료");

            // 7. 응답
            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "accessToken", newAccessToken));

        } catch (Exception e) {
            System.err.println("❌ Token refresh 오류: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(500).body(Map.of(
                    "success", false,
                    "message", "Token refresh failed: " + e.getMessage()));
        }
    }

    /**
     * 로그아웃
     * 
     * - Access Token: Redis에서 삭제 (Upstash)
     * - Refresh Token: Neon DB에서 무효화 + 쿠키 삭제
     * 
     * POST /api/auth/logout
     * Header: Authorization: Bearer {accessToken}
     */
    @PostMapping("/logout")
    public ResponseEntity<?> logout(
            HttpServletRequest request,
            HttpServletResponse response) {
        try {
            // 1. Access Token 삭제 (Redis)
            String authHeader = request.getHeader("Authorization");
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String accessToken = authHeader.substring(7);
                accessTokenService.revokeAccessToken(accessToken);
                System.out.println("🗑️ Access Token Redis 삭제 완료");
            }

            // 2. Refresh Token 무효화 (Neon DB)
            String refreshToken = refreshTokenService.getRefreshTokenFromCookie(request);
            if (refreshToken != null && !refreshToken.isEmpty()) {
                boolean revoked = refreshTokenService.revokeRefreshToken(refreshToken);
                System.out.println("🗑️ Refresh Token Neon DB 무효화: " + revoked);
            }

            // 3. 쿠키 삭제
            refreshTokenService.clearRefreshTokenCookie(response);

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "로그아웃 성공"));

        } catch (Exception e) {
            System.err.println("❌ 로그아웃 오류: " + e.getMessage());
            e.printStackTrace();

            // 오류가 발생해도 쿠키는 삭제
            refreshTokenService.clearRefreshTokenCookie(response);

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "로그아웃 완료"));
        }
    }

    /**
     * 전체 로그아웃 (모든 디바이스에서 로그아웃)
     * 
     * - Access Token: 사용자의 모든 토큰 Redis에서 삭제
     * - Refresh Token: 사용자의 모든 토큰 Neon DB에서 무효화
     * 
     * POST /api/auth/logout-all
     */
    @PostMapping("/logout-all")
    public ResponseEntity<?> logoutAll(
            HttpServletRequest request,
            HttpServletResponse response) {
        try {
            // 1. 쿠키에서 Refresh Token 읽기
            String refreshToken = refreshTokenService.getRefreshTokenFromCookie(request);

            if (refreshToken != null && !refreshToken.isEmpty()) {
                // 2. User 조회
                Optional<User> userOptional = refreshTokenService.getUserByRefreshToken(refreshToken);
                
                if (userOptional.isPresent()) {
                    Long userId = userOptional.get().getId();
                    
                    // 3. 사용자의 모든 Access Token 삭제 (Redis)
                    int accessTokensRevoked = accessTokenService.revokeAllUserTokens(userId);
                    System.out.println("🗑️ Access Token 전체 삭제: " + accessTokensRevoked + "개");
                    
                    // 4. 사용자의 모든 Refresh Token 무효화 (Neon DB)
                    int refreshTokensRevoked = refreshTokenService.revokeAllUserTokens(userId);
                    System.out.println("🗑️ Refresh Token 전체 무효화: " + refreshTokensRevoked + "개");
                }
            }

            // 5. 쿠키 삭제
            refreshTokenService.clearRefreshTokenCookie(response);

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "모든 디바이스에서 로그아웃 완료"));

        } catch (Exception e) {
            System.err.println("❌ 전체 로그아웃 오류: " + e.getMessage());
            e.printStackTrace();

            refreshTokenService.clearRefreshTokenCookie(response);

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "로그아웃 완료"));
        }
    }
}
