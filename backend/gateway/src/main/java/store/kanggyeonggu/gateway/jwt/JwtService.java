package store.kanggyeonggu.gateway.jwt;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Date;

/**
 * JWT 토큰 생성 및 검증 서비스 (공통)
 */
@Service
public class JwtService {

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private Long jwtExpiration;

    /**
     * JWT Secret Key 생성
     * 키가 짧을 경우 SHA-256 해시를 사용하여 256 bits로 확장
     */
    private SecretKey getSecretKey() {
        try {
            byte[] keyBytes = jwtSecret.getBytes(StandardCharsets.UTF_8);

            // 키가 32 bytes (256 bits) 미만이면 SHA-256으로 해시하여 확장
            if (keyBytes.length < 32) {
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                keyBytes = digest.digest(keyBytes);
            }

            return Keys.hmacShaKeyFor(keyBytes);
        } catch (Exception e) {
            throw new RuntimeException("JWT Secret Key 생성 실패", e);
        }
    }

    public String generateToken(Long userId, String nickname) {
        SecretKey key = getSecretKey();
        Date now = new Date();
        Date expirationDate = new Date(now.getTime() + jwtExpiration);

        return Jwts.builder()
                .claim("userId", userId)
                .claim("nickname", nickname)
                .subject(userId.toString())
                .issuedAt(now)
                .expiration(expirationDate)
                .signWith(key)
                .compact();
    }

    public Claims parseToken(String token) {
        SecretKey key = getSecretKey();
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public Long getUserIdFromToken(String token) {
        Claims claims = parseToken(token);
        return Long.parseLong(claims.getSubject());
    }

    public boolean validateToken(String token) {
        try {
            parseToken(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * JWT 만료 시간 반환 (밀리초)
     */
    public long getExpiration() {
        return jwtExpiration;
    }

    /**
     * 토큰의 남은 만료 시간 계산 (밀리초)
     */
    public long getRemainingExpiration(String token) {
        try {
            Claims claims = parseToken(token);
            Date expiration = claims.getExpiration();
            long remaining = expiration.getTime() - System.currentTimeMillis();
            return Math.max(0, remaining);
        } catch (Exception e) {
            return 0;
        }
    }
}
