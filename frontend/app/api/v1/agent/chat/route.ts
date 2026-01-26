import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      return NextResponse.json(
        { error: "BACKEND_URL 환경 변수가 설정되지 않았습니다." },
        { status: 500 }
      );
    }

    try {
      const response = await fetch(`${backendUrl}/agent/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || errorData.message || response.statusText;
        return NextResponse.json(
          {
            error: errorMessage || "백엔드 서버 오류가 발생했습니다.",
            status: response.status,
          },
          { status: response.status }
        );
      }

      const data = await response.json();
      return NextResponse.json(data);
    } catch (backendError) {
      console.error("Backend connection error:", backendError);

      if (backendError instanceof TypeError && backendError.message.includes("fetch")) {
        return NextResponse.json(
          {
            error: "백엔드 서버에 연결할 수 없습니다. 백엔드 서비스가 실행 중인지 확인해주세요.",
            status: 503,
          },
          { status: 503 }
        );
      }

      return NextResponse.json(
        {
          error: "백엔드 서버와 통신 중 오류가 발생했습니다.",
          status: 500,
        },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json(
      {
        error: "서버 오류가 발생했습니다.",
        details: error instanceof Error ? error.message : "알 수 없는 오류",
      },
      { status: 500 }
    );
  }
}
