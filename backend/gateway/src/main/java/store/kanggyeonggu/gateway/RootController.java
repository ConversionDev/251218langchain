package store.kanggyeonggu.gateway;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * 루트 경로 컨트롤러
 */
@RestController
@Tag(name = "Root", description = "API Gateway 루트 엔드포인트")
public class RootController {

    @GetMapping(value = "/", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "루트 경로", description = "API Gateway 루트 엔드포인트")
    public ResponseEntity<Map<String, Object>> root() {
        Map<String, Object> info = new HashMap<>();
        info.put("service", "Kanggyeonggu Store API Gateway");
        info.put("version", "1.0.0");
        info.put("status", "UP");
        info.put("message", "API Gateway is running");
        info.put("documentation", "/docs");
        info.put("health", "/actuator/health");
        return ResponseEntity.ok(info);
    }
}

