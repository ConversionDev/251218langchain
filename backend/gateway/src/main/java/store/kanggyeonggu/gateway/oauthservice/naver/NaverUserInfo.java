package store.kanggyeonggu.gateway.oauthservice.naver;

import com.fasterxml.jackson.annotation.JsonProperty;

// 네이버 사용자 정보 DTO
public class NaverUserInfo {

    @JsonProperty("resultcode")
    private String resultcode;

    @JsonProperty("message")
    private String message;

    @JsonProperty("response")
    private Response response;

    // Getters and Setters
    public String getResultcode() {
        return resultcode;
    }

    public void setResultcode(String resultcode) {
        this.resultcode = resultcode;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Response getResponse() {
        return response;
    }

    public void setResponse(Response response) {
        this.response = response;
    }

    // 네이버 사용자 정보 응답
    public static class Response {
        private String id;
        private String nickname;
        private String name;
        private String profile_image;

        // Getters and Setters
        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
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

        public String getProfile_image() {
            return profile_image;
        }

        public void setProfile_image(String profile_image) {
            this.profile_image = profile_image;
        }
    }
}

