import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, history, model_type } = body;

    if (!message) {
      return new Response(
        JSON.stringify({ error: "메시지가 필요합니다." }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      return new Response(
        JSON.stringify({ error: "BACKEND_URL 환경 변수가 설정되지 않았습니다." }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }

    try {
      const response = await fetch(`${backendUrl}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          history: history || [],
          model_type: model_type,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || errorData.message || response.statusText;
        return new Response(
          JSON.stringify({ error: errorMessage || "백엔드 서버 오류가 발생했습니다." }),
          { status: response.status, headers: { "Content-Type": "application/json" } }
        );
      }

      if (!response.body) {
        return new Response(
          JSON.stringify({ error: "스트리밍 응답을 받을 수 없습니다." }),
          { status: 500, headers: { "Content-Type": "application/json" } }
        );
      }

      return new Response(response.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    } catch (backendError) {
      console.error("Backend streaming connection error:", backendError);

      if (backendError instanceof TypeError && backendError.message.includes("fetch")) {
        return new Response(
          JSON.stringify({
            error: "백엔드 서버에 연결할 수 없습니다. 백엔드 서비스가 실행 중인지 확인해주세요.",
          }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        );
      }

      return new Response(
        JSON.stringify({
          error: "백엔드 서버와 통신 중 오류가 발생했습니다.",
          details: backendError instanceof Error ? backendError.message : "알 수 없는 오류",
        }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }
  } catch (error) {
    console.error("Streaming API error:", error);

    return new Response(
      JSON.stringify({
        error: "서버 오류가 발생했습니다.",
        details: error instanceof Error ? error.message : "알 수 없는 오류",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
