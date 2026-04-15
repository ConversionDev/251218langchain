package store.kanggyeonggu.gateway.userservice.common;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * Health Check 및 공통 API
 */
@RestController
@RequestMapping("/user")
public class HealthController {

    /**
     * Health Check Endpoint
     * GET /user/health
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "ok");
        response.put("service", "user-service");
        response.put("message", "User Service is running");

        return ResponseEntity.ok(response);
    }
}

