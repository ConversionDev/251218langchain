package store.kanggyeonggu.gateway.oauthservice.kakao;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

// 카카오 OAuth2 API 호출 서비스 (WebClient를 HTTP 클라이언트로만 사용)
@Service
public class KakaoOAuthService {

    private final WebClient webClient;

    @Value("${kakao.rest-api-key}")
    private String kakaoRestApiKey;

    @Value("${kakao.redirect-uri}")
    private String kakaoRedirectUri;

    @Value("${kakao.client-secret:}")
    private String kakaoClientSecret;

    public KakaoOAuthService(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.build();
    }

    // 카카오 인가 코드로 액세스 토큰 요청 (동기 방식)
    public KakaoTokenResponse getAccessToken(String authorizationCode) {
        String tokenUrl = "https://kauth.kakao.com/oauth/token";

        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("grant_type", "authorization_code");
        body.add("client_id", kakaoRestApiKey);
        body.add("redirect_uri", kakaoRedirectUri);
        body.add("code", authorizationCode);

        if (kakaoClientSecret != null && !kakaoClientSecret.isEmpty()) {
            body.add("client_secret", kakaoClientSecret);
        }

        return webClient.post()
                .uri(tokenUrl)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(KakaoTokenResponse.class)
                .block(); // 동기 방식으로 변환
    }

    // 액세스 토큰으로 카카오 사용자 정보 조회 (동기 방식)
    public KakaoUserInfo getUserInfo(String accessToken) {
        String userInfoUrl = "https://kapi.kakao.com/v2/user/me";

        return webClient.get()
                .uri(userInfoUrl)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                .retrieve()
                .bodyToMono(KakaoUserInfo.class)
                .block(); // 동기 방식으로 변환
    }

    // 카카오 로그아웃 (동기 방식)
    @SuppressWarnings("unchecked")
    public Map<String, Object> logout(String accessToken) {
        String logoutUrl = "https://kapi.kakao.com/v1/user/logout";

        return webClient.post()
                .uri(logoutUrl)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                .retrieve()
                .bodyToMono((Class<Map<String, Object>>) (Class<?>) Map.class)
                .block(); // 동기 방식으로 변환
    }

    // 카카오 연결 끊기 (회원 탈퇴) (동기 방식)
    @SuppressWarnings("unchecked")
    public Map<String, Object> unlink(String accessToken) {
        String unlinkUrl = "https://kapi.kakao.com/v1/user/unlink";

        return webClient.post()
                .uri(unlinkUrl)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                .retrieve()
                .bodyToMono((Class<Map<String, Object>>) (Class<?>) Map.class)
                .block(); // 동기 방식으로 변환
    }
}

