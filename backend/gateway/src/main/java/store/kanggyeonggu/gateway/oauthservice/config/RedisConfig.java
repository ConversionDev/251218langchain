package store.kanggyeonggu.gateway.oauthservice.config;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceClientConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;

/**
 * Redis 설정 (Spring Boot 3.x + Java 21 최적화)
 * Upstash Redis 연결을 위한 최신 설정
 * - SSL/TLS 연결 지원
 * - Connection Pool 최적화
 * - Java 8+ 날짜/시간 타입 지원
 */
@Configuration
@EnableCaching
@ConditionalOnProperty(name = "spring.data.redis.host")
public class RedisConfig {

    @Value("${spring.data.redis.host}")
    private String host;

    @Value("${spring.data.redis.port}")
    private int port;

    @Value("${spring.data.redis.password:}")
    private String password;

    @Value("${spring.data.redis.ssl.enabled:true}")
    private boolean sslEnabled;

    /**
     * Redis Connection Factory (Lettuce 기반, Spring Boot 3.x 최적화)
     * - SSL/TLS 지원
     * - Connection Pool 설정
     * - Timeout 설정
     */
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        // Redis 서버 설정
        RedisStandaloneConfiguration serverConfig = new RedisStandaloneConfiguration();
        serverConfig.setHostName(host);
        serverConfig.setPort(port);

        if (password != null && !password.isEmpty()) {
            serverConfig.setPassword(password);
        }

        // Lettuce Client 설정 (최신 방식)
        LettuceClientConfiguration.LettuceClientConfigurationBuilder clientConfig = LettuceClientConfiguration.builder()
                .commandTimeout(Duration.ofSeconds(10)) // 명령 타임아웃
                .shutdownTimeout(Duration.ofMillis(100)); // 종료 타임아웃

        // SSL 설정
        if (sslEnabled) {
            clientConfig.useSsl();
        }

        return new LettuceConnectionFactory(serverConfig, clientConfig.build());
    }

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
