package store.kanggyeonggu.gateway.oauthservice.google;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

// 구글 OAuth2 API 호출 서비스 (WebClient를 HTTP 클라이언트로만 사용)
@Service
public class GoogleOAuthService {

    private final WebClient webClient;

    @Value("${google.client-id}")
    private String googleClientId;

    @Value("${google.client-secret}")
    private String googleClientSecret;

    @Value("${google.redirect-uri}")
    private String googleRedirectUri;

    public GoogleOAuthService(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.build();
    }

    // 구글 인가 코드로 액세스 토큰 요청 (동기 방식)
    public GoogleTokenResponse getAccessToken(String authorizationCode) {
        String tokenUrl = "https://oauth2.googleapis.com/token";

        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("grant_type", "authorization_code");
        body.add("client_id", googleClientId);
        body.add("client_secret", googleClientSecret);
        body.add("redirect_uri", googleRedirectUri);
        body.add("code", authorizationCode);

        return webClient.post()
                .uri(tokenUrl)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(GoogleTokenResponse.class)
                .block(); // 동기 방식으로 변환
    }

    // 액세스 토큰으로 구글 사용자 정보 조회 (동기 방식)
    public GoogleUserInfo getUserInfo(String accessToken) {
        String userInfoUrl = "https://www.googleapis.com/oauth2/v2/userinfo";

        return webClient.get()
                .uri(userInfoUrl)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                .retrieve()
                .bodyToMono(GoogleUserInfo.class)
                .block(); // 동기 방식으로 변환
    }

    // 구글 로그아웃 (동기 방식)
    @SuppressWarnings("unchecked")
    public Map<String, Object> logout(String accessToken) {
        String logoutUrl = "https://oauth2.googleapis.com/revoke";

        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("token", accessToken);

        return webClient.post()
                .uri(logoutUrl)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .bodyValue(body)
                .retrieve()
                .bodyToMono((Class<Map<String, Object>>) (Class<?>) Map.class)
                .block(); // 동기 방식으로 변환
    }
}

