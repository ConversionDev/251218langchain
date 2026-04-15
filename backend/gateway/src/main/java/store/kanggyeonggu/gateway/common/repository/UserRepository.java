package store.kanggyeonggu.gateway.common.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import store.kanggyeonggu.gateway.common.entity.User;

import java.util.Optional;

/**
 * 사용자 정보를 관리하는 Repository (공통)
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long>, UserRepositoryCustom {

    Optional<User> findByProviderAndProviderIdAndDeletedFalse(String provider, String providerId);

    Optional<User> findByProviderAndProviderId(String provider, String providerId);

    Optional<User> findByEmailAndDeletedFalse(String email);

    Optional<User> findByEmail(String email);

    long countByDeletedFalse();
}

