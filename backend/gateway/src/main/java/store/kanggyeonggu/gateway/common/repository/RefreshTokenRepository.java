package store.kanggyeonggu.gateway.common.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import store.kanggyeonggu.gateway.common.entity.RefreshToken;
import store.kanggyeonggu.gateway.common.entity.User;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Refresh Token Repository
 * 
 * Neon DB (PostgreSQL)에서 Refresh Token 관리
 */
@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {

    /**
     * 토큰 값으로 Refresh Token 조회
     */
    Optional<RefreshToken> findByToken(String token);

    /**
     * 유효한 토큰 조회 (무효화되지 않고, 만료되지 않음)
     */
    @Query("SELECT rt FROM RefreshToken rt WHERE rt.token = :token AND rt.revoked = false AND rt.expiresAt > :now")
    Optional<RefreshToken> findValidToken(@Param("token") String token, @Param("now") LocalDateTime now);

    /**
     * 사용자의 모든 Refresh Token 조회
     */
    List<RefreshToken> findByUser(User user);

    /**
     * 사용자의 모든 유효한 Refresh Token 조회
     */
    @Query("SELECT rt FROM RefreshToken rt WHERE rt.user = :user AND rt.revoked = false AND rt.expiresAt > :now")
    List<RefreshToken> findValidTokensByUser(@Param("user") User user, @Param("now") LocalDateTime now);

    /**
     * 사용자 ID로 모든 Refresh Token 조회
     */
    List<RefreshToken> findByUserId(Long userId);

    /**
     * 토큰 무효화 (revoke)
     */
    @Modifying
    @Query("UPDATE RefreshToken rt SET rt.revoked = true, rt.revokedAt = :now WHERE rt.token = :token")
    int revokeByToken(@Param("token") String token, @Param("now") LocalDateTime now);

    /**
     * 사용자의 모든 토큰 무효화 (전체 로그아웃)
     */
    @Modifying
    @Query("UPDATE RefreshToken rt SET rt.revoked = true, rt.revokedAt = :now WHERE rt.user.id = :userId AND rt.revoked = false")
    int revokeAllByUserId(@Param("userId") Long userId, @Param("now") LocalDateTime now);

    /**
     * 토큰 삭제
     */
    void deleteByToken(String token);

    /**
     * 사용자의 모든 토큰 삭제
     */
    void deleteByUserId(Long userId);

    /**
     * 만료된 토큰 삭제 (정리 작업용)
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.expiresAt < :now")
    int deleteExpiredTokens(@Param("now") LocalDateTime now);

    /**
     * 무효화된 토큰 삭제 (정리 작업용)
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.revoked = true AND rt.revokedAt < :cutoffDate")
    int deleteRevokedTokens(@Param("cutoffDate") LocalDateTime cutoffDate);

    /**
     * 토큰 존재 여부 확인
     */
    boolean existsByToken(String token);
}
