package store.kanggyeonggu.gateway.jwt;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Access Token 관리 서비스 (Upstash Redis)
 * 
 * 저장소: Upstash Redis
 * 
 * 기능:
 * - Access Token 화이트리스트 관리
 * - 로그아웃 시 즉시 토큰 무효화
 * - 활성 세션 추적
 * - 강제 로그아웃 지원
 * 
 * 키 구조:
 * - access_token:{token} → userId (토큰 → 사용자 매핑)
 * - user_tokens:{userId} → Set<token> (사용자 → 토큰 목록)
 */
@Service
public class AccessTokenService {

    private final RedisTemplate<String, String> redisTemplate;
    private final JwtService jwtService;

    private static final String ACCESS_TOKEN_PREFIX = "access_token:";
    private static final String USER_TOKENS_PREFIX = "user_tokens:";

    public AccessTokenService(RedisTemplate<String, String> redisTemplate, JwtService jwtService) {
        this.redisTemplate = redisTemplate;
        this.jwtService = jwtService;
    }

    /**
     * Access Token을 Redis에 저장 (로그인 시)
     * 
     * @param token Access Token
     * @param userId 사용자 ID
     * @param expirationMs 만료 시간 (밀리초)
     */
    public void saveAccessToken(String token, Long userId, long expirationMs) {
        try {
            String tokenKey = ACCESS_TOKEN_PREFIX + token;
            String userTokensKey = USER_TOKENS_PREFIX + userId;

            // 1. 토큰 → userId 매핑 저장
            redisTemplate.opsForValue().set(
                    tokenKey,
                    userId.toString(),
                    expirationMs,
                    TimeUnit.MILLISECONDS);

            // 2. 사용자 → 토큰 목록에 추가 (다중 디바이스 지원)
            redisTemplate.opsForSet().add(userTokensKey, token);
            // 토큰 목록도 만료 설정 (가장 긴 토큰 수명 기준)
            redisTemplate.expire(userTokensKey, expirationMs * 2, TimeUnit.MILLISECONDS);

            System.out.println("✅ Access Token Redis 저장: userId=" + userId);

        } catch (Exception e) {
            System.err.println("❌ Access Token Redis 저장 실패: " + e.getMessage());
            // Redis 장애 시에도 로그인은 진행 (Graceful Degradation)
        }
    }

    /**
     * Access Token이 유효한지 확인 (Redis에 존재하는지)
     * 
     * @param token Access Token
     * @return 유효하면 userId, 무효하면 null
     */
    public Long validateAccessToken(String token) {
        try {
            String tokenKey = ACCESS_TOKEN_PREFIX + token;
            String userIdStr = redisTemplate.opsForValue().get(tokenKey);

            if (userIdStr != null) {
                return Long.parseLong(userIdStr);
            }

            return null;

        } catch (Exception e) {
            System.err.println("❌ Access Token Redis 검증 실패: " + e.getMessage());
            // Redis 장애 시 JWT 자체 검증으로 폴백
            return null;
        }
    }

    /**
     * Access Token이 Redis에 존재하는지 확인
     */
    public boolean isTokenValid(String token) {
        try {
            String tokenKey = ACCESS_TOKEN_PREFIX + token;
            return Boolean.TRUE.equals(redisTemplate.hasKey(tokenKey));
        } catch (Exception e) {
            System.err.println("❌ Access Token 존재 확인 실패: " + e.getMessage());
            return true; // Redis 장애 시 JWT 검증으로 폴백
        }
    }

    /**
     * Access Token 삭제 (로그아웃 시)
     * 
     * @param token Access Token
     */
    public void revokeAccessToken(String token) {
        try {
            String tokenKey = ACCESS_TOKEN_PREFIX + token;

            // userId 조회
            String userIdStr = redisTemplate.opsForValue().get(tokenKey);

            // 토큰 삭제
            redisTemplate.delete(tokenKey);

            // 사용자 토큰 목록에서도 제거
            if (userIdStr != null) {
                String userTokensKey = USER_TOKENS_PREFIX + userIdStr;
                redisTemplate.opsForSet().remove(userTokensKey, token);
            }

            System.out.println("✅ Access Token Redis 삭제 완료");

        } catch (Exception e) {
            System.err.println("❌ Access Token Redis 삭제 실패: " + e.getMessage());
        }
    }

    /**
     * 사용자의 모든 Access Token 삭제 (전체 로그아웃)
     * 
     * @param userId 사용자 ID
     * @return 삭제된 토큰 수
     */
    public int revokeAllUserTokens(Long userId) {
        try {
            String userTokensKey = USER_TOKENS_PREFIX + userId;

            // 사용자의 모든 토큰 조회
            Set<String> tokens = redisTemplate.opsForSet().members(userTokensKey);

            if (tokens == null || tokens.isEmpty()) {
                return 0;
            }

            int count = 0;

            // 각 토큰 삭제
            for (String token : tokens) {
                String tokenKey = ACCESS_TOKEN_PREFIX + token;
                redisTemplate.delete(tokenKey);
                count++;
            }

            // 사용자 토큰 목록 삭제
            redisTemplate.delete(userTokensKey);

            System.out.println("✅ 사용자 전체 Access Token 삭제: userId=" + userId + ", count=" + count);

            return count;

        } catch (Exception e) {
            System.err.println("❌ 사용자 전체 토큰 삭제 실패: " + e.getMessage());
            return 0;
        }
    }

    /**
     * 사용자의 활성 세션(토큰) 수 조회
     */
    public long getActiveSessionCount(Long userId) {
        try {
            String userTokensKey = USER_TOKENS_PREFIX + userId;
            Long count = redisTemplate.opsForSet().size(userTokensKey);
            return count != null ? count : 0;
        } catch (Exception e) {
            System.err.println("❌ 활성 세션 수 조회 실패: " + e.getMessage());
            return 0;
        }
    }

    /**
     * JWT에서 만료 시간까지 남은 시간 계산 (밀리초)
     */
    public long getRemainingExpiration(String token) {
        try {
            return jwtService.getRemainingExpiration(token);
        } catch (Exception e) {
            return 0;
        }
    }
}

