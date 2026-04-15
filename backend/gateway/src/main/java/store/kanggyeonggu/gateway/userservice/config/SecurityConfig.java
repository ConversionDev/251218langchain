package store.kanggyeonggu.gateway.userservice.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

/**
 * Spring Security 설정
 */
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

        private final JwtAuthenticationFilter jwtAuthenticationFilter;

        @Bean
        public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
                http
                                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                                .csrf(csrf -> csrf.disable())
                                .sessionManagement(session -> session
                                                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                                .authorizeHttpRequests(auth -> auth
                                                // 공개 엔드포인트 (인증 불필요)
                                                .requestMatchers(
                                                                "/",
                                                                "/user/health",
                                                                "/actuator/**",
                                                                "/docs/**", // Swagger UI
                                                                "/swagger-ui/**", // Swagger UI (대체 경로)
                                                                "/swagger-ui.html", // Swagger UI (구버전)
                                                                "/docs/api-docs/**", // OpenAPI JSON
                                                                "/auth/**", // OAuth 로그인 (카카오, 네이버, 구글)
                                                                "/oauth2/**", // OAuth 콜백
                                                                "/api/auth/refresh", // Access Token 갱신
                                                                "/api/auth/logout" // 로그아웃
                                                ).permitAll()
                                                // 나머지 요청은 인증 필요
                                                .anyRequest().authenticated())
                                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

                return http.build();
        }

        @Bean
        public CorsConfigurationSource corsConfigurationSource() {
                CorsConfiguration configuration = new CorsConfiguration();
                configuration.setAllowedOrigins(List.of(
                                "http://localhost:3000",
                                "http://127.0.0.1:3000",
                                "https://www.kanggyeonggu.store",
                                "https://kanggyeonggu.store",
                                "https://251203-erp.vercel.app"));
                configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
                configuration.setAllowedHeaders(List.of("*"));
                configuration.setAllowCredentials(true);
                configuration.setMaxAge(3600L);

                UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
                source.registerCorsConfiguration("/**", configuration);
                return source;
        }
}
