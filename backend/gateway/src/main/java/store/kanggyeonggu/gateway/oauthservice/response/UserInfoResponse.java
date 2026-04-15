package store.kanggyeonggu.gateway.oauthservice.response;

// 사용자 정보 응답
public class UserInfoResponse {

    private boolean success;
    private String message;
    private UserData user;

    public UserInfoResponse() {
    }

    public UserInfoResponse(boolean success, String message, UserData user) {
        this.success = success;
        this.message = message;
        this.user = user;
    }

    // Static factory methods
    public static UserInfoResponse success(UserData user) {
        return new UserInfoResponse(true, "사용자 정보 조회 성공", user);
    }

    public static UserInfoResponse error(String message) {
        return new UserInfoResponse(false, message, null);
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

    public UserData getUser() {
        return user;
    }

    public void setUser(UserData user) {
        this.user = user;
    }

    // 사용자 데이터
    public static class UserData {
        private String id;
        private Long kakaoId;
        private String nickname;
        private String name;
        private String provider;
        private String profileImageUrl;

        public UserData() {
        }

        public UserData(String id, Long kakaoId, String nickname) {
            this.id = id;
            this.kakaoId = kakaoId;
            this.nickname = nickname;
        }

        public UserData(String id, Long kakaoId, String nickname, String name, String provider,
                String profileImageUrl) {
            this.id = id;
            this.kakaoId = kakaoId;
            this.nickname = nickname;
            this.name = name;
            this.provider = provider;
            this.profileImageUrl = profileImageUrl;
        }

        // Getters and Setters
        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public Long getKakaoId() {
            return kakaoId;
        }

        public void setKakaoId(Long kakaoId) {
            this.kakaoId = kakaoId;
        }

        public String getNickname() {
            return nickname;
        }

        public void setNickname(String nickname) {
            this.nickname = nickname;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getProvider() {
            return provider;
        }

        public void setProvider(String provider) {
            this.provider = provider;
        }

        public String getProfileImageUrl() {
            return profileImageUrl;
        }

        public void setProfileImageUrl(String profileImageUrl) {
            this.profileImageUrl = profileImageUrl;
        }
    }
}
