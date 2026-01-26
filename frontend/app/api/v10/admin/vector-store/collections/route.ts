/**
 * 벡터 스토어 컬렉션 목록 조회 API
 * 백엔드로 프록시
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v10/admin/vector-store/collections`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("벡터 컬렉션 목록 조회 실패:", error);
    return NextResponse.json(
      { error: "벡터 컬렉션 목록 조회 실패" },
      { status: 500 }
    );
  }
}
