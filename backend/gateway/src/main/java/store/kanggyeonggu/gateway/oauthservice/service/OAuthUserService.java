package store.kanggyeonggu.gateway.oauthservice.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.common.repository.UserRepository;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

/**
 * OAuth 사용자 관리 서비스
 * - DB Upsert (생성 또는 업데이트)
 * - Upstash Redis 저장
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OAuthUserService {

    private final UserRepository userRepository;
    private final RedisTemplate<String, Object> redisTemplate;

    /**
     * OAuth 로그인 시 사용자 정보를 DB와 Redis에 저장
     */
    @Transactional
    public User upsertUser(String provider, String providerId, String nickname, String profileImageUrl) {
        log.info("🔄 사용자 Upsert 시작: provider={}, providerId={}", provider, providerId);

        Optional<User> existingUser = userRepository
                .findByProviderAndProviderIdAndDeletedFalse(provider, providerId);

        User user;
        if (existingUser.isPresent()) {
            user = existingUser.get();
            log.info("✅ 기존 사용자 발견: id={}, nickname={}", user.getId(), user.getNickname());

            user.setNickname(nickname);
            user.setProfileImageUrl(profileImageUrl);
            user.setLastLoginAt(LocalDateTime.now());

            log.info("📝 사용자 정보 업데이트 완료");
        } else {
            user = User.builder()
                    .provider(provider)
                    .providerId(providerId)
                    .nickname(nickname)
                    .profileImageUrl(profileImageUrl)
                    .enabled(true)
                    .deleted(false)
                    .build();

            log.info("🆕 신규 사용자 생성");
        }

        user = userRepository.save(user);
        log.info("💾 Neon DB 저장 완료: id={}", user.getId());

        saveToRedis(user);

        return user;
    }

    private void saveToRedis(User user) {
        try {
            String key = "user:" + user.getId();
            redisTemplate.opsForValue().set(key, user);
            redisTemplate.expire(key, 24, TimeUnit.HOURS);
            log.info("✅ Upstash Redis 저장 완료: key={}", key);
        } catch (Exception e) {
            log.error("❌ Redis 저장 실패: {}", e.getMessage(), e);
        }
    }

    public Optional<User> getUserFromRedis(Long userId) {
        try {
            String key = "user:" + userId;
            Object value = redisTemplate.opsForValue().get(key);

            if (value instanceof User) {
                log.info("✅ Redis에서 사용자 조회 성공: userId={}", userId);
                return Optional.of((User) value);
            }

            log.info("⚠️ Redis에 사용자 없음: userId={}", userId);
            return Optional.empty();
        } catch (Exception e) {
            log.error("❌ Redis 조회 실패: {}", e.getMessage(), e);
            return Optional.empty();
        }
    }

    public void deleteFromRedis(Long userId) {
        try {
            String key = "user:" + userId;
            redisTemplate.delete(key);
            log.info("✅ Redis에서 사용자 삭제 완료: userId={}", userId);
        } catch (Exception e) {
            log.error("❌ Redis 삭제 실패: {}", e.getMessage(), e);
        }
    }

    public Optional<User> getUserFromDB(Long userId) {
        return userRepository.findById(userId);
    }

    public Optional<User> getUser(Long userId) {
        Optional<User> userFromRedis = getUserFromRedis(userId);
        if (userFromRedis.isPresent()) {
            return userFromRedis;
        }

        Optional<User> userFromDB = getUserFromDB(userId);
        if (userFromDB.isPresent()) {
            saveToRedis(userFromDB.get());
        }

        return userFromDB;
    }
}
