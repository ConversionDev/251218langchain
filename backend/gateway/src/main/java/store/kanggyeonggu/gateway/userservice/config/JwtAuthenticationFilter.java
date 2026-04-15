package store.kanggyeonggu.gateway.userservice.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import store.kanggyeonggu.gateway.jwt.AccessTokenService;
import store.kanggyeonggu.gateway.jwt.JwtService;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.ArrayList;

/**
 * JWT 토큰을 검증하고 SecurityContext에 인증 정보를 설정하는 필터
 * 
 * 검증 순서:
 * 1. JWT 서명 검증 (JwtService)
 * 2. Redis 화이트리스트 확인 (AccessTokenService)
 * - Redis에 토큰이 없으면 무효 (로그아웃된 토큰)
 * - Redis 장애 시 JWT 검증만으로 진행 (Graceful Degradation)
 */
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final AccessTokenService accessTokenService;

    public JwtAuthenticationFilter(JwtService jwtService, AccessTokenService accessTokenService) {
        this.jwtService = jwtService;
        this.accessTokenService = accessTokenService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        // 공개 엔드포인트는 인증 불필요
        String requestUri = request.getRequestURI();
        if (requestUri.equals("/user/health") ||
                requestUri.startsWith("/actuator/") ||
                requestUri.startsWith("/docs/") ||
                requestUri.startsWith("/swagger-ui/") ||
                requestUri.startsWith("/auth/") ||
                requestUri.startsWith("/oauth2/") ||
                requestUri.startsWith("/api/auth/") ||
                "OPTIONS".equalsIgnoreCase(request.getMethod())) {
            filterChain.doFilter(request, response);
            return;
        }

        String authHeader = request.getHeader("Authorization");

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = authHeader.substring(7);

        try {
            // 1. JWT 서명 검증
            if (jwtService.validateToken(token)) {
                Long userId = jwtService.getUserIdFromToken(token);

                // 2. Redis 화이트리스트 확인 (토큰이 유효한지)
                boolean isValidInRedis = accessTokenService.isTokenValid(token);

                if (!isValidInRedis) {
                    // 토큰이 Redis에 없음 = 로그아웃된 토큰
                    logger.warn("Access Token이 Redis에 없음 (로그아웃됨): userId=" + userId);
                    filterChain.doFilter(request, response);
                    return;
                }

                // SecurityContext에 인증 정보 설정
                UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                        userId,
                        null,
                        new ArrayList<>());
                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authentication);

                logger.debug("JWT 인증 성공: userId=" + userId);
            }
        } catch (Exception e) {
            // 토큰 검증 실패 시 로그만 남기고 계속 진행
            logger.warn("JWT 토큰 검증 실패: " + e.getMessage());
        }

        filterChain.doFilter(request, response);
    }
}
