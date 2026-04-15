package store.kanggyeonggu.gateway.oauthservice.common;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.jwt.JwtService;
import store.kanggyeonggu.gateway.oauthservice.response.UserInfoResponse;
import store.kanggyeonggu.gateway.oauthservice.service.OAuthUserService;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

/**
 * OAuth 사용자 정보 조회 컨트롤러
 * JWT 토큰만으로 사용자 정보를 조회 (provider 구분 불필요)
 */
@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class OAuthUserController {

    private final JwtService jwtService;
    private final OAuthUserService userService;

    /**
     * 통합 사용자 정보 조회
     * GET /auth/user
     * 
     * JWT 토큰에서 userId를 추출하여 사용자 정보를 조회합니다.
     * Provider 구분 없이 동작합니다.
     * 
     * @param authorization Authorization 헤더 (Bearer {token})
     * @return 사용자 정보
     */
    @GetMapping("/user")
    public ResponseEntity<UserInfoResponse> getUserInfo(
            @RequestHeader(value = "Authorization", required = false) String authorization) {

        try {
            // 1. Authorization 헤더 확인
            if (authorization == null || !authorization.startsWith("Bearer ")) {
                log.warn("⚠️ Authorization 헤더 없음 또는 형식 오류");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(UserInfoResponse.error("인증 토큰이 필요합니다."));
            }

            // 2. JWT 토큰 추출
            String token = authorization.substring(7); // "Bearer " 제거

            // 3. JWT 토큰 검증
            if (!jwtService.validateToken(token)) {
                log.warn("⚠️ JWT 토큰 검증 실패");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(UserInfoResponse.error("유효하지 않은 토큰입니다."));
            }

            // 4. JWT 토큰에서 userId 추출
            Map<String, Object> claims = jwtService.parseToken(token);

            // subject에 userId가 저장되어 있음 (generateToken에서 .subject(kakaoId.toString()) 사용)
            String subject = (String) claims.get("sub");
            Long userId;

            try {
                userId = Long.parseLong(subject);
            } catch (NumberFormatException e) {
                // kakaoId claim도 확인 (하위 호환성)
                Object kakaoIdObj = claims.get("kakaoId");
                if (kakaoIdObj instanceof Number) {
                    userId = ((Number) kakaoIdObj).longValue();
                } else {
                    log.error("❌ JWT 토큰에서 userId 추출 실패: subject={}, kakaoId={}", subject, kakaoIdObj);
                    return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                            .body(UserInfoResponse.error("토큰에서 사용자 ID를 찾을 수 없습니다."));
                }
            }

            log.info("🔍 사용자 정보 조회: userId={}", userId);

            // 5. 사용자 정보 조회 (Redis → DB)
            Optional<User> userOptional = userService.getUser(userId);

            if (userOptional.isEmpty()) {
                log.warn("⚠️ 사용자 정보 없음: userId={}", userId);
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(UserInfoResponse.error("사용자 정보를 찾을 수 없습니다."));
            }

            User user = userOptional.get();

            // 6. UserInfoResponse 생성
            UserInfoResponse.UserData userData = new UserInfoResponse.UserData(
                    user.getId().toString(),
                    null, // provider별 ID는 필요시 추가
                    user.getNickname(),
                    user.getName(),
                    user.getProvider(),
                    user.getProfileImageUrl());

            log.info("✅ 사용자 정보 조회 성공: userId={}, provider={}, nickname={}",
                    user.getId(), user.getProvider(), user.getNickname());

            return ResponseEntity.ok(UserInfoResponse.success(userData));

        } catch (Exception e) {
            log.error("❌ 사용자 정보 조회 오류: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(UserInfoResponse.error("사용자 정보 조회 중 오류가 발생했습니다."));
        }
    }
}
