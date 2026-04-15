package store.kanggyeonggu.gateway.userservice.user;

import lombok.RequiredArgsConstructor;
import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.common.repository.UserRepository;
import store.kanggyeonggu.gateway.userservice.user.dto.UserResponse;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 사용자 정보 조회 서비스
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserQueryService {

    private final UserRepository userRepository;

    /**
     * ID로 사용자 조회
     */
    public UserResponse getUserById(Long userId) {
        return userRepository.findById(userId)
                .filter(user -> !user.getDeleted())
                .map(UserResponse::from)
                .orElse(null);
    }

    /**
     * 모든 사용자 조회 (삭제되지 않은 사용자만)
     */
    public List<UserResponse> getAllUsers() {
        return userRepository.findAll().stream()
                .filter(user -> !user.getDeleted())
                .map(UserResponse::from)
                .collect(Collectors.toList());
    }

    /**
     * OAuth 제공자별 사용자 조회
     */
    public List<UserResponse> getUsersByProvider(String provider) {
        return userRepository.findAll().stream()
                .filter(user -> !user.getDeleted())
                .filter(user -> user.getProvider().equalsIgnoreCase(provider))
                .map(UserResponse::from)
                .collect(Collectors.toList());
    }
}

