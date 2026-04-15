package store.kanggyeonggu.gateway.oauthservice.kakao;

import com.fasterxml.jackson.annotation.JsonProperty;

// 카카오 사용자 정보 DTO
public class KakaoUserInfo {

    private Long id;

    @JsonProperty("connected_at")
    private String connectedAt;

    @JsonProperty("kakao_account")
    private KakaoAccount kakaoAccount;

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getConnectedAt() {
        return connectedAt;
    }

    public void setConnectedAt(String connectedAt) {
        this.connectedAt = connectedAt;
    }

    public KakaoAccount getKakaoAccount() {
        return kakaoAccount;
    }

    public void setKakaoAccount(KakaoAccount kakaoAccount) {
        this.kakaoAccount = kakaoAccount;
    }

    // 카카오 계정 정보
    public static class KakaoAccount {
        private Profile profile;

        @JsonProperty("profile_nickname_needs_agreement")
        private Boolean profileNicknameNeedsAgreement;

        @JsonProperty("profile_image_needs_agreement")
        private Boolean profileImageNeedsAgreement;

        // Getters and Setters
        public Profile getProfile() {
            return profile;
        }

        public void setProfile(Profile profile) {
            this.profile = profile;
        }

        public Boolean getProfileNicknameNeedsAgreement() {
            return profileNicknameNeedsAgreement;
        }

        public void setProfileNicknameNeedsAgreement(Boolean profileNicknameNeedsAgreement) {
            this.profileNicknameNeedsAgreement = profileNicknameNeedsAgreement;
        }

        public Boolean getProfileImageNeedsAgreement() {
            return profileImageNeedsAgreement;
        }

        public void setProfileImageNeedsAgreement(Boolean profileImageNeedsAgreement) {
            this.profileImageNeedsAgreement = profileImageNeedsAgreement;
        }
    }

    // 프로필 정보
    public static class Profile {
        private String nickname;

        @JsonProperty("thumbnail_image_url")
        private String thumbnailImageUrl;

        @JsonProperty("profile_image_url")
        private String profileImageUrl;

        @JsonProperty("is_default_image")
        private Boolean isDefaultImage;

        // Getters and Setters
        public String getNickname() {
            return nickname;
        }

        public void setNickname(String nickname) {
            this.nickname = nickname;
        }

        public String getThumbnailImageUrl() {
            return thumbnailImageUrl;
        }

        public void setThumbnailImageUrl(String thumbnailImageUrl) {
            this.thumbnailImageUrl = thumbnailImageUrl;
        }

        public String getProfileImageUrl() {
            return profileImageUrl;
        }

        public void setProfileImageUrl(String profileImageUrl) {
            this.profileImageUrl = profileImageUrl;
        }

        public Boolean getIsDefaultImage() {
            return isDefaultImage;
        }

        public void setIsDefaultImage(Boolean isDefaultImage) {
            this.isDefaultImage = isDefaultImage;
        }
    }
}

