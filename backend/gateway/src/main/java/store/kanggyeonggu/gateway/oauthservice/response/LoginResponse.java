package store.kanggyeonggu.gateway.oauthservice.response;

// 로그인 응답
public class LoginResponse {

    private boolean success;
    private String message;
    private String authUrl;

    public LoginResponse() {
    }

    public LoginResponse(boolean success, String message, String authUrl) {
        this.success = success;
        this.message = message;
        this.authUrl = authUrl;
    }

    // Static factory methods
    public static LoginResponse success(String authUrl) {
        return new LoginResponse(true, "카카오 로그인 URL 생성 성공", authUrl);
    }

    public static LoginResponse error(String message) {
        return new LoginResponse(false, message, null);
    }

    // Getters and Setters
    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getAuthUrl() {
        return authUrl;
    }

    public void setAuthUrl(String authUrl) {
        this.authUrl = authUrl;
    }
}

