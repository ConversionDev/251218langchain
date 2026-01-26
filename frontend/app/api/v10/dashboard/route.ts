import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // 백엔드 API 호출
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/api/v10/dashboard`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Dashboard API error:", error);
    
    // 에러 발생 시 임시 데이터 반환
    return NextResponse.json(
      {
        stats: {
          total_sales: 12450000,
          active_members: 1234,
          reserved_tickets: 5678,
          active_bets: 89,
        },
        activities: [
          {
            id: "1",
            message: "홍길동님이 경기 티켓을 예매했습니다",
            time: "5분 전",
          },
          {
            id: "2",
            message: "김철수님이 베팅을 완료했습니다",
            time: "12분 전",
          },
        ],
      },
      { status: 200 }
    );
  }
}
