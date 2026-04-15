package store.kanggyeonggu.gateway.oauthservice.google;

// 구글 사용자 정보 DTO
public class GoogleUserInfo {

    private String id;
    private String name;
    private String picture;

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getPicture() {
        return picture;
    }

    public void setPicture(String picture) {
        this.picture = picture;
    }
}

