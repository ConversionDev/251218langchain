package store.kanggyeonggu.gateway.userservice.profile;

import lombok.RequiredArgsConstructor;
import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.common.repository.UserRepository;
import store.kanggyeonggu.gateway.userservice.profile.dto.ProfileResponse;
import store.kanggyeonggu.gateway.userservice.profile.dto.ProfileUpdateRequest;
import store.kanggyeonggu.gateway.userservice.user.dto.UserResponse;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

/**
 * 프로필 관리 서비스
 */
@Service
@RequiredArgsConstructor
@Transactional
public class ProfileService {

    private final UserRepository userRepository;

    /**
     * 프로필 조회
     */
    @Transactional(readOnly = true)
    public ProfileResponse getProfile(Long userId) {
        return userRepository.findById(userId)
                .filter(user -> !user.getDeleted())
                .map(ProfileResponse::from)
                .orElse(null);
    }

    /**
     * 프로필 수정
     */
    public UserResponse updateProfile(Long userId, ProfileUpdateRequest request) {
        Optional<User> userOptional = userRepository.findById(userId);

        if (userOptional.isEmpty() || userOptional.get().getDeleted()) {
            return null;
        }

        User user = userOptional.get();

        // 요청된 필드만 업데이트
        if (request.getNickname() != null && !request.getNickname().trim().isEmpty()) {
            user.setNickname(request.getNickname());
        }
        if (request.getName() != null && !request.getName().trim().isEmpty()) {
            user.setName(request.getName());
        }
        if (request.getProfileImageUrl() != null) {
            user.setProfileImageUrl(request.getProfileImageUrl());
        }
        if (request.getEmail() != null && !request.getEmail().trim().isEmpty()) {
            user.setEmail(request.getEmail());
        }

        User updatedUser = userRepository.save(user);
        return UserResponse.from(updatedUser);
    }
}

