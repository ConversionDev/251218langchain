package store.kanggyeonggu.gateway.userservice.user;

import lombok.RequiredArgsConstructor;
import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.common.repository.UserRepository;
import store.kanggyeonggu.gateway.userservice.common.ApiResponse;
import store.kanggyeonggu.gateway.userservice.user.dto.UserResponse;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

/**
 * 사용자 정보 조회 API
 * - 현재 로그인한 사용자 정보 조회
 * - 전체 사용자 조회 (관리자용)
 * - 특정 사용자 조회
 */
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserQueryService userService;
    private final UserRepository userRepository;

    /**
     * 현재 로그인한 사용자 정보 조회
     * GET /api/users/me
     */
    @GetMapping("/me")
    public ResponseEntity<ApiResponse<UserResponse>> getCurrentUser(Authentication authentication) {
        try {
            if (authentication == null || authentication.getPrincipal() == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(ApiResponse.error("인증이 필요합니다."));
            }

            Long userId = Long.parseLong(authentication.getPrincipal().toString());
            UserResponse userResponse = userService.getUserById(userId);

            if (userResponse == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(ApiResponse.error("사용자를 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(ApiResponse.success(userResponse));

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("사용자 정보 조회 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * 모든 사용자 조회 (관리자용)
     * GET /api/users
     */
    @GetMapping
    public ResponseEntity<ApiResponse<List<UserResponse>>> getAllUsers() {
        try {
            List<UserResponse> users = userService.getAllUsers();
            return ResponseEntity.ok(ApiResponse.success(users));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("사용자 목록 조회 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * 특정 사용자 조회
     * GET /api/users/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<UserResponse>> getUserById(@PathVariable Long id) {
        try {
            UserResponse userResponse = userService.getUserById(id);
            
            if (userResponse == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(ApiResponse.error("사용자를 찾을 수 없습니다."));
            }

            return ResponseEntity.ok(ApiResponse.success(userResponse));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("사용자 조회 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * OAuth 제공자별 사용자 조회
     * GET /api/users/provider/{provider}
     */
    @GetMapping("/provider/{provider}")
    public ResponseEntity<ApiResponse<List<UserResponse>>> getUsersByProvider(@PathVariable String provider) {
        try {
            List<UserResponse> users = userService.getUsersByProvider(provider);
            return ResponseEntity.ok(ApiResponse.success(users));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("사용자 조회 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * 사용자 수 조회
     * GET /api/users/count
     */
    @GetMapping("/count")
    public ResponseEntity<ApiResponse<Long>> getUserCount() {
        try {
            long count = userRepository.countByDeletedFalse();
            return ResponseEntity.ok(ApiResponse.success(count));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error("사용자 수 조회 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }
}

