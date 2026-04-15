package store.kanggyeonggu.gateway.common.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Refresh Token Entity
 * 
 * Neon DB (PostgreSQL)에 저장되는 Refresh Token 정보
 * - 사용자별 여러 개의 Refresh Token 가능 (다중 디바이스)
 * - 토큰 무효화(revoke) 지원
 * - Token Rotation 지원
 */
@Entity
@Table(name = "refresh_tokens", indexes = {
        @Index(name = "idx_refresh_tokens_user_id", columnList = "user_id"),
        @Index(name = "idx_refresh_tokens_token", columnList = "token"),
        @Index(name = "idx_refresh_tokens_expires_at", columnList = "expires_at")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RefreshToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 토큰 소유자 (User FK)
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    /**
     * Refresh Token 값 (UUID)
     */
    @Column(name = "token", nullable = false, unique = true, length = 255)
    private String token;

    /**
     * 디바이스 정보 (User-Agent 등)
     */
    @Column(name = "device_info", length = 500)
    private String deviceInfo;

    /**
     * 클라이언트 IP 주소
     */
    @Column(name = "ip_address", length = 45)
    private String ipAddress;

    /**
     * 토큰 발급 시간
     */
    @Column(name = "issued_at", nullable = false)
    private LocalDateTime issuedAt;

    /**
     * 토큰 만료 시간
     */
    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    /**
     * 토큰 무효화 여부 (로그아웃, 강제 만료 시 true)
     */
    @Column(name = "revoked", nullable = false)
    @Builder.Default
    private Boolean revoked = false;

    /**
     * 토큰 무효화 시간
     */
    @Column(name = "revoked_at")
    private LocalDateTime revokedAt;

    /**
     * 레코드 생성 시간
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (issuedAt == null) {
            issuedAt = LocalDateTime.now();
        }
    }

    /**
     * 토큰 무효화 (로그아웃 시)
     */
    public void revoke() {
        this.revoked = true;
        this.revokedAt = LocalDateTime.now();
    }

    /**
     * 토큰이 유효한지 확인
     * - 무효화되지 않음
     * - 만료되지 않음
     */
    public boolean isValid() {
        return !revoked && expiresAt.isAfter(LocalDateTime.now());
    }
}
