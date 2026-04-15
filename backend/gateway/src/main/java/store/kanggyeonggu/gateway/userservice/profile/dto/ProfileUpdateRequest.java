package store.kanggyeonggu.gateway.userservice.profile.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 프로필 수정 요청 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ProfileUpdateRequest {
    private String nickname;
    private String name;
    private String profileImageUrl;
    private String email;
}

