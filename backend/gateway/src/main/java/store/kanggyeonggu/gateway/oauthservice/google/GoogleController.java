package store.kanggyeonggu.gateway.oauthservice.google;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import store.kanggyeonggu.gateway.jwt.AccessTokenService;
import store.kanggyeonggu.gateway.jwt.JwtService;
import store.kanggyeonggu.gateway.jwt.RefreshTokenService;
import store.kanggyeonggu.gateway.oauthservice.response.*;
import store.kanggyeonggu.gateway.oauthservice.service.OAuthUserService;

import jakarta.servlet.http.HttpServletResponse;

import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

// 구글 OAuth2 인증 컨트롤러 (Spring MVC)
@RestController
@RequestMapping("/auth/google")
public class GoogleController {

    private final GoogleOAuthService googleOAuthService;
    private final JwtService jwtService;
    private final OAuthUserService userService;
    private final RefreshTokenService refreshTokenService;
    private final AccessTokenService accessTokenService;

    @Value("${google.client-id}")
    private String googleClientId;

    @Value("${google.redirect-uri}")
    private String googleRedirectUri;

    @Value("${google.authorization-uri}")
    private String googleAuthorizationUri;

    @Value("${frontend.callback-url}")
    private String frontendCallbackUrl;

    public GoogleController(
            GoogleOAuthService googleOAuthService,
            JwtService jwtService,
            OAuthUserService userService,
            RefreshTokenService refreshTokenService,
            AccessTokenService accessTokenService) {
        this.googleOAuthService = googleOAuthService;
        this.jwtService = jwtService;
        this.userService = userService;
        this.refreshTokenService = refreshTokenService;
        this.accessTokenService = accessTokenService;
    }

    // 구글 로그인 URL 생성
    // POST /auth/google/login
    // RESTful API 방식: JSON 응답으로 구글 로그인 URL 반환
    // 프론트엔드에서 받아서 처리
    // 로그인은 상태를 변경하는 작업이므로 POST 메서드 사용
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> googleLogin() {
        String scope = "openid profile email";
        String googleAuthUrl = String.format(
                "%s?client_id=%s&redirect_uri=%s&response_type=code&scope=%s",
                googleAuthorizationUri,
                googleClientId,
                URLEncoder.encode(googleRedirectUri, StandardCharsets.UTF_8),
                URLEncoder.encode(scope, StandardCharsets.UTF_8));

        return ResponseEntity.ok(LoginResponse.success(googleAuthUrl));
    }

    // 구글 OAuth2 콜백 처리 (동기 방식)
    // GET /auth/google/callback?code=xxx (구글 표준)
    @GetMapping("/callback")
    public ResponseEntity<Void> googleCallback(
            @RequestParam(required = false) String code,
            HttpServletResponse httpResponse) {
        // GET 방식 (구글 표준)
        if (code != null) {
            return processCallback(code, httpResponse);
        }

        // code가 없는 경우 에러
        String errorUrl = String.format(
                "%s?error=%s",
                frontendCallbackUrl,
                URLEncoder.encode("missing_code", StandardCharsets.UTF_8));
        HttpHeaders headers = new HttpHeaders();
        headers.setLocation(URI.create(errorUrl));
        return new ResponseEntity<>(headers, HttpStatus.FOUND);
    }

    // 공통 콜백 처리 메서드
    private ResponseEntity<Void> processCallback(String code, HttpServletResponse httpResponse) {
        try {
            // frontendCallbackUrl 유효성 검사
            if (frontendCallbackUrl == null || frontendCallbackUrl.trim().isEmpty()) {
                System.err.println("ERROR: frontend.callback-url이 설정되지 않았습니다.");
                return createErrorResponse("FRONTEND_CALLBACK_URL_NOT_CONFIGURED");
            }

            // 1. 액세스 토큰 요청 (동기 처리)
            GoogleTokenResponse tokenResponse = googleOAuthService.getAccessToken(code);
            String accessToken = tokenResponse.getAccessToken();

            // 구글 액세스 토큰 출력
            System.out.println("Access Token: " + accessToken);

            // 2. 사용자 정보 조회 (동기 처리)
            GoogleUserInfo userInfo = googleOAuthService.getUserInfo(accessToken);

            // 3. 구글 사용자 정보 추출
            String googleId = userInfo.getId();
            String name = userInfo.getName() != null ? userInfo.getName() : "사용자";
            String nickname = name; // 구글은 별명이 없으므로 이름을 별명으로 사용
            String profileImageUrl = userInfo.getPicture();

            // 4. DB Upsert + Redis 저장 (핵심!)
            store.kanggyeonggu.gateway.common.entity.User user = userService.upsertUser(
                    "google",
                    googleId,
                    nickname,
                    profileImageUrl);

            // 5. JWT Access Token 생성 (DB에 저장된 user.id 사용)
            String jwtToken = jwtService.generateToken(user.getId(), user.getNickname());
            System.out.println("JWT Access Token 생성 완료");

            // 6. Access Token을 Redis에 저장 (Upstash)
            accessTokenService.saveAccessToken(jwtToken, user.getId(), jwtService.getExpiration());

            // 7. Refresh Token 생성 및 Neon DB에 저장
            String refreshToken = refreshTokenService.createAndSaveRefreshToken(user);

            // HttpOnly 쿠키로 Refresh Token 설정
            refreshTokenService.setRefreshTokenCookie(httpResponse, refreshToken);

            // 7. 프론트엔드로 리다이렉트 (Access Token은 URL 파라미터로)
            return createRedirectResponse(frontendCallbackUrl, jwtToken, null);

        } catch (Exception e) {
            // 에러 로깅
            System.err.println("ERROR: 콜백 처리 중 예외 발생: " + e.getMessage());
            e.printStackTrace();

            // 에러 발생 시 프론트엔드로 리다이렉트
            return createRedirectResponse(frontendCallbackUrl, null, "login_failed");
        }
    }

    // 안전한 리다이렉트 응답 생성
    private ResponseEntity<Void> createRedirectResponse(String baseUrl, String token, String error) {
        try {
            // baseUrl 유효성 검사
            if (baseUrl == null || baseUrl.trim().isEmpty()) {
                System.err.println("ERROR: 리다이렉트 URL이 설정되지 않았습니다.");
                baseUrl = "http://localhost:3000/dashboard"; // 기본값
            }

            // URL 생성
            String redirectUrl;
            if (token != null) {
                // 성공: 토큰 포함
                String encodedToken = URLEncoder.encode(token, StandardCharsets.UTF_8);
                redirectUrl = String.format("%s?token=%s", baseUrl, encodedToken);
            } else if (error != null) {
                // 실패: 에러 포함
                redirectUrl = String.format("%s?error=%s", baseUrl, URLEncoder.encode(error, StandardCharsets.UTF_8));
            } else {
                // 기본 리다이렉트
                redirectUrl = baseUrl;
            }

            // URI 생성 및 검증
            URI redirectUri;
            try {
                redirectUri = URI.create(redirectUrl);
            } catch (IllegalArgumentException e) {
                System.err.println("ERROR: 잘못된 리다이렉트 URL 형식: " + redirectUrl);
                System.err.println("ERROR: " + e.getMessage());
                // 기본 URL로 폴백
                redirectUri = URI.create("http://localhost:3000/dashboard?error=redirect_url_invalid");
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setLocation(redirectUri);

            return new ResponseEntity<>(headers, HttpStatus.FOUND);

        } catch (Exception e) {
            // 리다이렉트 생성 실패 시 기본 에러 응답
            System.err.println("ERROR: 리다이렉트 응답 생성 실패: " + e.getMessage());
            e.printStackTrace();

            HttpHeaders headers = new HttpHeaders();
            try {
                headers.setLocation(URI.create("http://localhost:3000/dashboard?error=redirect_failed"));
            } catch (Exception ex) {
                System.err.println("ERROR: 기본 리다이렉트 URL도 실패: " + ex.getMessage());
            }

            return new ResponseEntity<>(headers, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // 에러 응답 생성
    private ResponseEntity<Void> createErrorResponse(String errorMessage) {
        return createRedirectResponse(frontendCallbackUrl, null, errorMessage);
    }

    // 사용자 정보 조회
    // GET /auth/google/user
    // Gateway에서 이미 JWT 검증을 완료하고 헤더에 사용자 정보를 추가했으므로,
    // 중복 검증 없이 헤더에서 직접 사용자 정보를 추출합니다.
    @GetMapping("/user")
    public ResponseEntity<UserInfoResponse> getUserInfo(
            @RequestHeader("X-User-Id") String userId,
            @RequestHeader("X-User-Nickname") String nickname) {

        // Gateway에서 이미 검증 완료, 헤더에서 사용자 정보 추출만 수행
        UserInfoResponse.UserData userData = new UserInfoResponse.UserData(
                userId,
                null, // 구글은 별도의 구글 ID 헤더가 없을 수 있음
                nickname);

        return ResponseEntity.ok(UserInfoResponse.success(userData));
    }

    // 로그아웃
    // POST /auth/google/logout
    // Authorization 헤더에 JWT 토큰을 포함하여 요청
    @PostMapping("/logout")
    public ResponseEntity<ApiResponse> logout(
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        try {
            // Authorization 헤더 확인
            if (authorization == null || !authorization.startsWith("Bearer ")) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponse.error("JWT 토큰이 필요합니다."));
            }

            // JWT 토큰 추출
            String jwtToken = authorization.substring(7);

            // JWT 토큰 검증
            if (!jwtService.validateToken(jwtToken)) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponse.error("유효하지 않은 토큰입니다."));
            }

            // JWT 토큰 검증 완료 (파싱은 validateToken에서 이미 수행됨)

            // 로그아웃 성공 응답
            return ResponseEntity.ok(ApiResponse.success("로그아웃 성공"));

        } catch (Exception e) {
            System.err.println("ERROR: 로그아웃 처리 중 예외 발생: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("로그아웃 처리 중 오류가 발생했습니다."));
        }
    }
}
