package store.kanggyeonggu.gateway.common.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import store.kanggyeonggu.gateway.common.listener.UserEntityListener;

import java.time.LocalDateTime;

/**
 * 소셜 로그인 사용자 정보를 저장하는 Entity (공통)
 */
@Entity
@Table(name = "users", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"provider", "provider_id"})
})
@EntityListeners(UserEntityListener.class)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "provider", nullable = false, length = 20)
    private String provider;

    @Column(name = "provider_id", nullable = false, length = 255)
    private String providerId;

    @Column(name = "nickname", length = 100)
    private String nickname;

    @Column(name = "name", length = 100)
    private String name;

    @Column(name = "profile_image_url", length = 500)
    private String profileImageUrl;

    @Column(name = "email", length = 255)
    private String email;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "last_login_at")
    private LocalDateTime lastLoginAt;

    @Column(name = "enabled", nullable = false)
    @Builder.Default
    private Boolean enabled = true;

    @Column(name = "deleted", nullable = false)
    @Builder.Default
    private Boolean deleted = false;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (lastLoginAt == null) {
            lastLoginAt = LocalDateTime.now();
        }
    }

    @PreUpdate
    protected void onUpdate() {
        lastLoginAt = LocalDateTime.now();
    }

    public void softDelete() {
        this.deleted = true;
        this.deletedAt = LocalDateTime.now();
    }

    public void restore() {
        this.deleted = false;
        this.deletedAt = null;
    }
}

