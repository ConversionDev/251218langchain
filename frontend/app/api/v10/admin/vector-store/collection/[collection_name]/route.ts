/**
 * 벡터 스토어 컬렉션 상세 정보 조회 API
 * 백엔드로 프록시
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ collection_name: string }> }
) {
  try {
    const { collection_name: collectionName } = await params;

    const response = await fetch(
      `${BACKEND_URL}/api/v10/admin/vector-store/collection/${collectionName}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("컬렉션 정보 조회 실패:", error);
    return NextResponse.json(
      { error: "컬렉션 정보 조회 실패" },
      { status: 500 }
    );
  }
}
