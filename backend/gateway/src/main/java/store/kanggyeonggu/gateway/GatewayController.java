package store.kanggyeonggu.gateway;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

/**
 * Gateway 정보 및 헬스체크 컨트롤러
 * OpenAPI 스펙에 최소한의 operations를 제공하기 위한 엔드포인트
 */
@RestController
@RequestMapping("/api/gateway")
@Tag(name = "Gateway", description = "API Gateway 정보 및 헬스체크")
public class GatewayController {

    @GetMapping(value = "/info", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "Gateway 정보 조회", description = "API Gateway의 기본 정보를 반환합니다.")
    public Mono<Map<String, Object>> getGatewayInfo() {
        Map<String, Object> info = new HashMap<>();
        info.put("service", "Kanggyeonggu Store API Gateway");
        info.put("version", "1.0.0");
        info.put("status", "running");
        info.put("description", "통합 API Gateway - 모든 마이크로서비스 API 문서");
        info.put("documentation", "/docs");
        return Mono.just(info);
    }

    @GetMapping(value = "/health", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(summary = "Gateway 헬스체크", description = "API Gateway의 상태를 확인합니다.")
    public Mono<Map<String, String>> healthCheck() {
        Map<String, String> health = new HashMap<>();
        health.put("status", "UP");
        health.put("service", "gateway");
        return Mono.just(health);
    }
}
