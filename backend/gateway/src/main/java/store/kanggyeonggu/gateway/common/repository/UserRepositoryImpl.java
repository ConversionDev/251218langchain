package store.kanggyeonggu.gateway.common.repository;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

/**
 * UserRepository 커스텀 구현체 (공통)
 */
@Repository
public class UserRepositoryImpl implements UserRepositoryCustom {

    @PersistenceContext
    private EntityManager entityManager;

    @Override
    @Transactional
    public void resetSequence() {
        entityManager.createNativeQuery("ALTER SEQUENCE users_id_seq RESTART WITH 1")
                .executeUpdate();
    }
}

