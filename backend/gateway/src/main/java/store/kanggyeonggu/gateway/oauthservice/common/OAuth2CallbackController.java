package store.kanggyeonggu.gateway.oauthservice.common;

import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.common.repository.UserRepository;
import store.kanggyeonggu.gateway.jwt.JwtService;
import store.kanggyeonggu.gateway.oauthservice.google.GoogleOAuthService;
import store.kanggyeonggu.gateway.oauthservice.google.GoogleTokenResponse;
import store.kanggyeonggu.gateway.oauthservice.google.GoogleUserInfo;
import store.kanggyeonggu.gateway.oauthservice.kakao.KakaoOAuthService;
import store.kanggyeonggu.gateway.oauthservice.kakao.KakaoTokenResponse;
import store.kanggyeonggu.gateway.oauthservice.kakao.KakaoUserInfo;
import store.kanggyeonggu.gateway.oauthservice.naver.NaverOAuthService;
import store.kanggyeonggu.gateway.oauthservice.naver.NaverTokenResponse;
import store.kanggyeonggu.gateway.oauthservice.naver.NaverUserInfo;

// OAuth2 콜백 컨트롤러
// 카카오, 네이버, 구글 OAuth2 콜백 처리
@RestController
@RequestMapping("/oauth2")
public class OAuth2CallbackController {

    private final KakaoOAuthService kakaoOAuthService;
    private final NaverOAuthService naverOAuthService;
    private final GoogleOAuthService googleOAuthService;
    private final JwtService jwtService;
    private final UserRepository userRepository;

    @Autowired(required = false)
    private RedisTemplate<String, Object> redisTemplate;

    @Value("${frontend.callback-url}")
    private String frontendCallbackUrl;

    @Value("${jwt.expiration:86400000}")
    private long jwtExpiration; // JWT 만료 시간 (밀리초)

    public OAuth2CallbackController(
            KakaoOAuthService kakaoOAuthService,
            NaverOAuthService naverOAuthService,
            GoogleOAuthService googleOAuthService,
            JwtService jwtService,
            UserRepository userRepository) {
        this.kakaoOAuthService = kakaoOAuthService;
        this.naverOAuthService = naverOAuthService;
        this.googleOAuthService = googleOAuthService;
        this.jwtService = jwtService;
        this.userRepository = userRepository;
    }

    // 카카오 OAuth2 콜백 처리
    @GetMapping("/kakao/callback")
    public ResponseEntity<Void> kakaoCallback(@RequestParam(required = false) String code) {
        if (code != null) {
            return processKakaoCallback(code);
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

    // 네이버 OAuth2 콜백 처리
    @GetMapping("/naver/callback")
    public ResponseEntity<Void> naverCallback(
            @RequestParam(required = false) String code,
            @RequestParam(required = false) String state,
            @RequestParam(required = false) String error,
            @RequestParam(required = false) String error_description) {

        // 네이버에서 에러를 반환한 경우
        if (error != null) {
            System.err.println("ERROR: 네이버에서 에러 반환: " + error + " - " + error_description);
            String errorUrl = String.format(
                    "%s?error=%s&error_description=%s",
                    frontendCallbackUrl,
                    URLEncoder.encode(error, StandardCharsets.UTF_8),
                    URLEncoder.encode(error_description != null ? error_description : "", StandardCharsets.UTF_8));
            HttpHeaders headers = new HttpHeaders();
            headers.setLocation(URI.create(errorUrl));
            return new ResponseEntity<>(headers, HttpStatus.FOUND);
        }

        if (code != null) {
            return processNaverCallback(code);
        }

        // code가 없는 경우 에러
        System.err.println("ERROR: 네이버 콜백에 code가 없습니다.");
        String errorUrl = String.format(
                "%s?error=%s",
                frontendCallbackUrl,
                URLEncoder.encode("missing_code", StandardCharsets.UTF_8));
        HttpHeaders headers = new HttpHeaders();
        headers.setLocation(URI.create(errorUrl));
        return new ResponseEntity<>(headers, HttpStatus.FOUND);
    }

    // 구글 OAuth2 콜백 처리
    @GetMapping("/google/callback")
    public ResponseEntity<Void> googleCallback(
            @RequestParam(required = false) String code,
            @RequestParam(required = false) String error) {

        // 구글에서 에러를 반환한 경우
        if (error != null) {
            System.err.println("ERROR: 구글에서 에러 반환: " + error);
            String errorUrl = String.format(
                    "%s?error=%s",
                    frontendCallbackUrl,
                    URLEncoder.encode(error, StandardCharsets.UTF_8));
            HttpHeaders headers = new HttpHeaders();
            headers.setLocation(URI.create(errorUrl));
            return new ResponseEntity<>(headers, HttpStatus.FOUND);
        }

        if (code != null) {
            return processGoogleCallback(code);
        }

        // code가 없는 경우 에러
        System.err.println("ERROR: 구글 콜백에 code가 없습니다.");
        String errorUrl = String.format(
                "%s?error=%s",
                frontendCallbackUrl,
                URLEncoder.encode("missing_code", StandardCharsets.UTF_8));
        HttpHeaders headers = new HttpHeaders();
        headers.setLocation(URI.create(errorUrl));
        return new ResponseEntity<>(headers, HttpStatus.FOUND);
    }

    // 카카오 콜백 처리 메서드
    private ResponseEntity<Void> processKakaoCallback(String code) {
        try {
            // frontendCallbackUrl 유효성 검사
            if (frontendCallbackUrl == null || frontendCallbackUrl.trim().isEmpty()) {
                System.err.println("ERROR: frontend.callback-url이 설정되지 않았습니다.");
                return createErrorResponse("FRONTEND_CALLBACK_URL_NOT_CONFIGURED");
            }

            // 1. 액세스 토큰 요청
            KakaoTokenResponse tokenResponse = kakaoOAuthService.getAccessToken(code);
            String accessToken = tokenResponse.getAccessToken();

            // 카카오 액세스 토큰 출력
            System.out.println("Access Token: " + accessToken);

            // 2. 사용자 정보 조회
            KakaoUserInfo userInfo = kakaoOAuthService.getUserInfo(accessToken);

            // 3. 카카오 사용자 정보 추출
            Long kakaoId = userInfo.getId();
            KakaoUserInfo.KakaoAccount kakaoAccount = userInfo.getKakaoAccount();
            KakaoUserInfo.Profile profile = kakaoAccount != null ? kakaoAccount.getProfile() : null;

            String nickname = profile != null ? profile.getNickname() : "사용자";
            String profileImageUrl = profile != null
                    ? (profile.getProfileImageUrl() != null ? profile.getProfileImageUrl() : null)
                    : null;

            // 4. DB에 사용자 정보 저장 또는 업데이트
            User user = userRepository.findByProviderAndProviderId("kakao", String.valueOf(kakaoId))
                    .map(existingUser -> {
                        // 기존 사용자 정보 업데이트
                        existingUser.setNickname(nickname);
                        existingUser.setProfileImageUrl(profileImageUrl);
                        existingUser.setLastLoginAt(java.time.LocalDateTime.now());
                        // 삭제된 사용자인 경우 복구
                        if (existingUser.getDeleted()) {
                            existingUser.restore();
                        }
                        return existingUser;
                    })
                    .orElseGet(() -> {
                        // 새 사용자 생성
                        return User.builder()
                                .provider("kakao")
                                .providerId(String.valueOf(kakaoId))
                                .nickname(nickname)
                                .name(nickname)
                                .profileImageUrl(profileImageUrl)
                                .enabled(true)
                                .deleted(false)
                                .build();
                    });

            // 4. DB에 사용자 정보 저장 또는 업데이트
            user = userRepository.save(user);
            System.out.println("User saved to DB: " + user.getId() + " - " + user.getNickname());

            // 5. JWT 토큰 생성 (DB의 user ID 사용)
            String jwtToken = jwtService.generateToken(user.getId(), user.getNickname());

            // 생성된 JWT 토큰 출력
            System.out.println("JWT Token: " + jwtToken);

            // 6. Redis에 JWT 토큰 및 사용자 정보 저장 (확인용)
            saveToRedis(user, jwtToken);

            // 7. 프론트엔드로 리다이렉트 (토큰 포함)
            return createRedirectResponse(frontendCallbackUrl, jwtToken, null);

        } catch (Exception e) {
            // 에러 로깅
            System.err.println("ERROR: 콜백 처리 중 예외 발생: " + e.getMessage());
            e.printStackTrace();

            // 에러 발생 시 프론트엔드로 리다이렉트
            return createRedirectResponse(frontendCallbackUrl, null, "login_failed");
        }
    }

    // 네이버 콜백 처리 메서드
    private ResponseEntity<Void> processNaverCallback(String code) {
        try {
            // frontendCallbackUrl 유효성 검사
            if (frontendCallbackUrl == null || frontendCallbackUrl.trim().isEmpty()) {
                System.err.println("ERROR: frontend.callback-url이 설정되지 않았습니다.");
                return createErrorResponse("FRONTEND_CALLBACK_URL_NOT_CONFIGURED");
            }

            // 1. 액세스 토큰 요청
            NaverTokenResponse tokenResponse = naverOAuthService.getAccessToken(code);
            String accessToken = tokenResponse.getAccessToken();

            // 네이버 액세스 토큰 출력
            System.out.println("Access Token: " + accessToken);

            // 2. 사용자 정보 조회
            NaverUserInfo userInfo = naverOAuthService.getUserInfo(accessToken);

            // 3. 네이버 사용자 정보 추출
            NaverUserInfo.Response response = userInfo.getResponse();
            String naverId = response.getId();
            String nickname = response.getNickname() != null ? response.getNickname() : "사용자";
            String name = response.getName() != null ? response.getName() : nickname;
            String profileImageUrl = response.getProfile_image() != null ? response.getProfile_image() : null;

            // 4. DB에 사용자 정보 저장 또는 업데이트
            User user = userRepository.findByProviderAndProviderId("naver", naverId)
                    .map(existingUser -> {
                        // 기존 사용자 정보 업데이트
                        existingUser.setNickname(nickname);
                        existingUser.setName(name);
                        existingUser.setProfileImageUrl(profileImageUrl);
                        existingUser.setLastLoginAt(java.time.LocalDateTime.now());
                        // 삭제된 사용자인 경우 복구
                        if (existingUser.getDeleted()) {
                            existingUser.restore();
                        }
                        return existingUser;
                    })
                    .orElseGet(() -> {
                        // 새 사용자 생성
                        return User.builder()
                                .provider("naver")
                                .providerId(naverId)
                                .nickname(nickname)
                                .name(name)
                                .profileImageUrl(profileImageUrl)
                                .enabled(true)
                                .deleted(false)
                                .build();
                    });

            // 4. DB에 사용자 정보 저장 또는 업데이트
            user = userRepository.save(user);
            System.out.println("User saved to DB: " + user.getId() + " - " + user.getNickname());

            // 5. JWT 토큰 생성 (DB의 user ID 사용)
            String jwtToken = jwtService.generateToken(user.getId(), user.getNickname());

            // 생성된 JWT 토큰 출력
            System.out.println("JWT Token: " + jwtToken);

            // 6. Redis에 JWT 토큰 및 사용자 정보 저장 (확인용)
            saveToRedis(user, jwtToken);

            // 7. 프론트엔드로 리다이렉트 (토큰 포함)
            return createRedirectResponse(frontendCallbackUrl, jwtToken, null);

        } catch (Exception e) {
            // 에러 로깅
            System.err.println("ERROR: 네이버 콜백 처리 중 예외 발생: " + e.getMessage());
            e.printStackTrace();

            // 에러 발생 시 프론트엔드로 리다이렉트
            return createRedirectResponse(frontendCallbackUrl, null, "login_failed");
        }
    }

    // 구글 콜백 처리 메서드
    private ResponseEntity<Void> processGoogleCallback(String code) {
        try {
            // frontendCallbackUrl 유효성 검사
            if (frontendCallbackUrl == null || frontendCallbackUrl.trim().isEmpty()) {
                System.err.println("ERROR: frontend.callback-url이 설정되지 않았습니다.");
                return createErrorResponse("FRONTEND_CALLBACK_URL_NOT_CONFIGURED");
            }

            // 1. 액세스 토큰 요청
            GoogleTokenResponse tokenResponse = googleOAuthService.getAccessToken(code);
            String accessToken = tokenResponse.getAccessToken();

            // 구글 액세스 토큰 출력
            System.out.println("Access Token: " + accessToken);

            // 2. 사용자 정보 조회
            GoogleUserInfo userInfo = googleOAuthService.getUserInfo(accessToken);

            // 3. 구글 사용자 정보 추출
            String googleId = userInfo.getId();
            String name = userInfo.getName() != null ? userInfo.getName() : "사용자";
            String nickname = name; // 구글은 별명이 없으므로 이름을 별명으로 사용
            String profileImageUrl = userInfo.getPicture() != null ? userInfo.getPicture() : null;

            // 4. DB에 사용자 정보 저장 또는 업데이트
            User user = userRepository.findByProviderAndProviderId("google", googleId)
                    .map(existingUser -> {
                        // 기존 사용자 정보 업데이트
                        existingUser.setNickname(nickname);
                        existingUser.setName(name);
                        existingUser.setProfileImageUrl(profileImageUrl);
                        existingUser.setLastLoginAt(java.time.LocalDateTime.now());
                        // 삭제된 사용자인 경우 복구
                        if (existingUser.getDeleted()) {
                            existingUser.restore();
                        }
                        return existingUser;
                    })
                    .orElseGet(() -> {
                        // 새 사용자 생성
                        return User.builder()
                                .provider("google")
                                .providerId(googleId)
                                .nickname(nickname)
                                .name(name)
                                .profileImageUrl(profileImageUrl)
                                .enabled(true)
                                .deleted(false)
                                .build();
                    });

            // 4. DB에 사용자 정보 저장 또는 업데이트
            user = userRepository.save(user);
            System.out.println("User saved to DB: " + user.getId() + " - " + user.getNickname());

            // 5. JWT 토큰 생성 (DB의 user ID 사용)
            String jwtToken = jwtService.generateToken(user.getId(), user.getNickname());

            // 생성된 JWT 토큰 출력
            System.out.println("JWT Token: " + jwtToken);

            // 6. Redis에 JWT 토큰 및 사용자 정보 저장 (확인용)
            saveToRedis(user, jwtToken);

            // 7. 프론트엔드로 리다이렉트 (토큰 포함)
            return createRedirectResponse(frontendCallbackUrl, jwtToken, null);

        } catch (Exception e) {
            // 에러 로깅
            System.err.println("ERROR: 구글 콜백 처리 중 예외 발생: " + e.getMessage());
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

    // Redis 테스트 엔드포인트 (확인용)
    @GetMapping("/test/redis")
    public ResponseEntity<Map<String, Object>> testRedis() {
        Map<String, Object> response = new java.util.HashMap<>();

        if (redisTemplate == null) {
            response.put("status", "error");
            response.put("message", "Redis가 설정되지 않았습니다. REDIS_HOST 환경 변수를 확인하세요.");
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
        }

        try {
            // 테스트 데이터 저장
            String testKey = "test:redis:connection";
            String testValue = "Redis connection test - " + System.currentTimeMillis();
            redisTemplate.opsForValue().set(testKey, testValue, 60, TimeUnit.SECONDS);

            // 저장된 데이터 조회
            Object retrievedValue = redisTemplate.opsForValue().get(testKey);

            response.put("status", "success");
            response.put("message", "Redis 연결 성공");
            response.put("testKey", testKey);
            response.put("savedValue", testValue);
            response.put("retrievedValue", retrievedValue);

            // 모든 키 조회 (테스트용)
            java.util.Set<String> keys = redisTemplate.keys("jwt:user:*");
            response.put("jwtTokenKeys", keys != null ? keys.size() : 0);

            java.util.Set<String> userKeys = redisTemplate.keys("user:info:*");
            response.put("userInfoKeys", userKeys != null ? userKeys.size() : 0);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            response.put("status", "error");
            response.put("message", "Redis 연결 실패: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    // Redis에 JWT 토큰 및 사용자 정보 저장
    private void saveToRedis(User user, String jwtToken) {
        try {
            // JWT 토큰 저장
            String jwtKey = "jwt:user:" + user.getId();
            redisTemplate.opsForValue().set(jwtKey, jwtToken, jwtExpiration, TimeUnit.MILLISECONDS);
            System.out.println("JWT Token saved to Redis: " + jwtKey);

            // 사용자 정보 저장 (확인용)
            String userInfoKey = "user:info:" + user.getId();
            java.util.Map<String, Object> userInfo = new java.util.HashMap<>();
            userInfo.put("id", user.getId());
            userInfo.put("nickname", user.getNickname() != null ? user.getNickname() : "");
            userInfo.put("provider", user.getProvider());
            userInfo.put("providerId", user.getProviderId());
            if (user.getProfileImageUrl() != null) {
                userInfo.put("profileImageUrl", user.getProfileImageUrl());
            }
            redisTemplate.opsForValue().set(userInfoKey, userInfo, jwtExpiration, TimeUnit.MILLISECONDS);
            System.out.println("User info saved to Redis: " + userInfoKey);
        } catch (Exception e) {
            System.err.println("ERROR: Redis 저장 실패: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
