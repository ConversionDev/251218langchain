package store.kanggyeonggu.gateway.oauthservice.config;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

/**
 * Redis 설정 (Spring Boot 3.x + Java 21 최적화)
 * Upstash Redis 연결을 위한 최신 설정
 * - 연결(호스트/포트/비밀번호/SSL)은 spring.data.redis.url(UPSTASH_REDIS_URL) 하나로 통합.
 *   rediss:// 스킴이면 Spring Boot가 SSL을 자동 활성화하므로 ConnectionFactory는 자동 구성에 위임.
 * - 여기서는 직렬화(Java 8 날짜/시간, 타입 안전성)만 담당하는 RedisTemplate만 정의.
 */
@Configuration
@EnableCaching
@ConditionalOnProperty(name = "spring.data.redis.url")
public class RedisConfig {

    /**
     * Redis Template (Spring Boot 3.x + Java 21 최적화)
     * - Java 8+ 날짜/시간 타입 지원 (LocalDateTime, Instant 등)
     * - 타입 안전성 보장
     * - JSON 직렬화 최적화
     */
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);

        // ObjectMapper 설정 (최신 방식)
        ObjectMapper objectMapper = new ObjectMapper();

        // Java 8+ 날짜/시간 모듈 등록
        objectMapper.registerModule(new JavaTimeModule());

        // 타입 안전성을 위한 Polymorphic Type Validator (Spring Boot 3.x)
        BasicPolymorphicTypeValidator typeValidator = BasicPolymorphicTypeValidator
                .builder()
                .allowIfBaseType(Object.class)
                .build();

        objectMapper.activateDefaultTyping(
                typeValidator,
                ObjectMapper.DefaultTyping.NON_FINAL,
                JsonTypeInfo.As.PROPERTY);

        // JSON Serializer 생성
        GenericJackson2JsonRedisSerializer jsonSerializer = new GenericJackson2JsonRedisSerializer(objectMapper);

        // Key Serializer (String)
        StringRedisSerializer stringSerializer = new StringRedisSerializer();

        // Serializer 설정
        template.setKeySerializer(stringSerializer);
        template.setHashKeySerializer(stringSerializer);
        template.setValueSerializer(jsonSerializer);
        template.setHashValueSerializer(jsonSerializer);

        // 기본 Serializer 설정
        template.setDefaultSerializer(jsonSerializer);

        template.afterPropertiesSet();
        return template;
    }
}
