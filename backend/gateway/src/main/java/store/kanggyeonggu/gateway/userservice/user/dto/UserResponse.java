package store.kanggyeonggu.gateway.userservice.user.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import store.kanggyeonggu.gateway.common.entity.User;

import java.time.LocalDateTime;

/**
 * 사용자 정보 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserResponse {
    private Long id;
    private String provider;
    private String providerId;
    private String nickname;
    private String name;
    private String profileImageUrl;
    private String email;
    private LocalDateTime createdAt;
    private LocalDateTime lastLoginAt;
    private Boolean enabled;

    public static UserResponse from(User user) {
        return UserResponse.builder()
                .id(user.getId())
                .provider(user.getProvider())
                .providerId(user.getProviderId())
                .nickname(user.getNickname())
                .name(user.getName())
                .profileImageUrl(user.getProfileImageUrl())
                .email(user.getEmail())
                .createdAt(user.getCreatedAt())
                .lastLoginAt(user.getLastLoginAt())
                .enabled(user.getEnabled())
                .build();
    }
}

