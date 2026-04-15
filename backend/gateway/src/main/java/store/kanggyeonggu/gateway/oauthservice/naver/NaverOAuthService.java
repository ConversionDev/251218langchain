package store.kanggyeonggu.gateway.oauthservice.naver;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

// 네이버 OAuth2 API 호출 서비스 (WebClient를 HTTP 클라이언트로만 사용)
@Service
public class NaverOAuthService {

    private final WebClient webClient;

    @Value("${naver.client-id}")
    private String naverClientId;

    @Value("${naver.client-secret}")
    private String naverClientSecret;

    @Value("${naver.redirect-uri}")
    private String naverRedirectUri;

    public NaverOAuthService(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.build();
    }

    // 네이버 인가 코드로 액세스 토큰 요청 (동기 방식)
    public NaverTokenResponse getAccessToken(String authorizationCode) {
        String tokenUrl = "https://nid.naver.com/oauth2.0/token";

        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("grant_type", "authorization_code");
        body.add("client_id", naverClientId);
        body.add("client_secret", naverClientSecret);
        body.add("redirect_uri", naverRedirectUri);
        body.add("code", authorizationCode);

        return webClient.post()
                .uri(tokenUrl)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(NaverTokenResponse.class)
                .block(); // 동기 방식으로 변환
    }

    // 액세스 토큰으로 네이버 사용자 정보 조회 (동기 방식)
    public NaverUserInfo getUserInfo(String accessToken) {
        String userInfoUrl = "https://openapi.naver.com/v1/nid/me";

        return webClient.get()
                .uri(userInfoUrl)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                .retrieve()
                .bodyToMono(NaverUserInfo.class)
                .block(); // 동기 방식으로 변환
    }

    // 네이버 로그아웃 (동기 방식)
    @SuppressWarnings("unchecked")
    public Map<String, Object> logout(String accessToken) {
        String logoutUrl = "https://nid.naver.com/oauth2.0/token";

        MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
        body.add("grant_type", "delete");
        body.add("client_id", naverClientId);
        body.add("client_secret", naverClientSecret);
        body.add("access_token", accessToken);
        body.add("service_provider", "NAVER");

        return webClient.post()
                .uri(logoutUrl)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .bodyValue(body)
                .retrieve()
                .bodyToMono((Class<Map<String, Object>>) (Class<?>) Map.class)
                .block(); // 동기 방식으로 변환
    }
}

