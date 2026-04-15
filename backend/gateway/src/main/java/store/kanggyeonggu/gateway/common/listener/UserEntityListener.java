package store.kanggyeonggu.gateway.common.listener;

import jakarta.persistence.PostRemove;
import lombok.extern.slf4j.Slf4j;
import store.kanggyeonggu.gateway.common.entity.User;
import store.kanggyeonggu.gateway.common.repository.UserRepository;
import store.kanggyeonggu.gateway.common.repository.UserRepositoryCustom;

import org.springframework.beans.BeansException;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

/**
 * User 엔티티의 생명주기 이벤트를 처리하는 리스너 (공통)
 */
@Slf4j
@Component
@Profile({ "dev", "test", "local" })
public class UserEntityListener implements ApplicationContextAware {

    private static ApplicationContext applicationContext;

    @Override
    public void setApplicationContext(ApplicationContext applicationContext) throws BeansException {
        UserEntityListener.applicationContext = applicationContext;
    }

    @PostRemove
    public void afterUserRemoved(User user) {
        try {
            if (applicationContext == null) {
                log.warn("ApplicationContext가 설정되지 않아 시퀀스 리셋을 건너뜁니다.");
                return;
            }

            UserRepository userRepository = applicationContext.getBean(UserRepository.class);
            long remainingCount = userRepository.countByDeletedFalse();

            log.info("User 삭제됨: ID={}, 닉네임={}, 남은 활성 사용자 수={}",
                    user.getId(), user.getNickname(), remainingCount);

            if (remainingCount == 0) {
                log.info("모든 활성 사용자가 삭제되어 시퀀스를 1로 리셋합니다.");
                if (userRepository instanceof UserRepositoryCustom) {
                    ((UserRepositoryCustom) userRepository).resetSequence();
                }
            }
        } catch (Exception e) {
            log.error("시퀀스 리셋 중 오류 발생: {}", e.getMessage(), e);
        }
    }
}

