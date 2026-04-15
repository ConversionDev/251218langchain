package store.kanggyeonggu.gateway;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * SpringDoc OpenAPI Groups 설정
 * 여러 마이크로서비스의 API를 하나의 Swagger UI에서 통합 관리
 */
@Configuration
public class OpenApiConfig {

    /**
     * ML Service API 그룹
     * http://mlservice:9002/openapi.json에서 OpenAPI 스펙을 가져옴
     */
    @Bean
    public GroupedOpenApi mlServiceApi() {
        return GroupedOpenApi.builder()
                .group("ml-service")
                .displayName("ML Service")
                .pathsToMatch("/api/ml/**")
                .build();
    }

    /**
     * Review Service API 그룹
     * http://reviewservice:9004/openapi.json에서 OpenAPI 스펙을 가져옴
     */
    @Bean
    public GroupedOpenApi reviewServiceApi() {
        return GroupedOpenApi.builder()
                .group("review-service")
                .displayName("Review Service")
                .pathsToMatch("/api/review/**")
                .build();
    }

    /**
     * Gateway 자체 API 그룹
     */
    @Bean
    public GroupedOpenApi gatewayApi() {
        return GroupedOpenApi.builder()
                .group("gateway")
                .displayName("Gateway")
                .pathsToMatch("/api/gateway/**")
                .build();
    }

    /**
     * 모든 서비스를 통합한 그룹 (기본 그룹)
     */
    @Bean
    public GroupedOpenApi allApis() {
        return GroupedOpenApi.builder()
                .group("all")
                .displayName("All Services")
                .pathsToMatch("/**")
                .build();
    }

    /**
     * 기본 OpenAPI 정보
     */
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Kanggyeonggu Store API Gateway")
                        .description("통합 API Gateway - 모든 마이크로서비스 API 문서")
                        .version("1.0.0"));
    }
}
