package store.kanggyeonggu.gateway.userservice.profile;

import lombok.RequiredArgsConstructor;
import store.kanggyeonggu.gateway.userservice.common.ApiResponse;
import store.kanggyeonggu.gateway.userservice.profile.dto.ProfileResponse;
import store.kanggyeonggu.gateway.userservice.profile.dto.ProfileUpdateRequest;
import store.kanggyeonggu.gateway.userservice.user.dto.UserResponse;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

/**
 * 프로필 관리 API
 * - 프로필 수정
 * - 프로필 조회
 */
@RestController
@RequiredArgsConstructor
public class ProfileController {

    private final ProfileService profileService;

    /**
     * 프로필 수정 (기존 호환성 유지)
     * PUT /api/users/me
     */
    @PutMapping("/api/users/me")
    public ResponseEntity<ApiResponse<UserResponse>> updateProfile(
            @RequestBody ProfileUpdateRequest request,
            Authentication authentication) {
        return updateProfileDetail(request, authentication);
    }

    /**
     * 현재 사용자 프로필 조회
     * GET /api/users/me/profile
     */
    @GetMapping("/api/users/me/profile")
    public ResponseEntity<ApiResponse<ProfileResponse>> getCurrentProfile(Authentication authentication) {
        try {
            if (authentication == null || authentication.getPrincipal() == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponse.error("인증이 필요합니다."));
            }

            Long userId = Long.parseLong(authentication.getPrincipal().toString());
            ProfileResponse profile = profileService.getProfile(userId);

            if (profile == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(ApiResponse.error("프로필을 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(ApiResponse.success(profile));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("프로필 조회 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * 프로필 수정
     * PUT /api/users/me/profile
     */
    @PutMapping("/api/users/me/profile")
    public ResponseEntity<ApiResponse<UserResponse>> updateProfileDetail(
            @RequestBody ProfileUpdateRequest request,
            Authentication authentication) {
        try {
            if (authentication == null || authentication.getPrincipal() == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponse.error("인증이 필요합니다."));
            }

            Long userId = Long.parseLong(authentication.getPrincipal().toString());
            UserResponse updatedUser = profileService.updateProfile(userId, request);

            if (updatedUser == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(ApiResponse.error("사용자를 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(ApiResponse.success("프로필이 수정되었습니다.", updatedUser));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("프로필 수정 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }
}

