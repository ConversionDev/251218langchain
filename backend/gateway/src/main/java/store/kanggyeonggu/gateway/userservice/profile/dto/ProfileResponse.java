package store.kanggyeonggu.gateway.userservice.profile.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import store.kanggyeonggu.gateway.common.entity.User;

import java.time.LocalDateTime;

/**
 * 프로필 정보 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProfileResponse {
    private Long id;
    private String nickname;
    private String name;
    private String profileImageUrl;
    private String email;
    private LocalDateTime createdAt;
    private LocalDateTime lastLoginAt;

    public static ProfileResponse from(User user) {
        return ProfileResponse.builder()
                .id(user.getId())
                .nickname(user.getNickname())
                .name(user.getName())
                .profileImageUrl(user.getProfileImageUrl())
                .email(user.getEmail())
                .createdAt(user.getCreatedAt())
                .lastLoginAt(user.getLastLoginAt())
                .build();
    }
}

