/**
 * 벡터 스토어 검색 API
 * 백엔드로 프록시
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("query");
    const collectionName = searchParams.get("collection_name");
    const k = searchParams.get("k") || "5";

    if (!query) {
      return NextResponse.json(
        { error: "query 파라미터가 필요합니다." },
        { status: 400 }
      );
    }

    let url = `${BACKEND_URL}/api/v10/admin/vector-store/search?query=${encodeURIComponent(query)}&k=${k}`;
    if (collectionName) {
      url += `&collection_name=${encodeURIComponent(collectionName)}`;
    }

    const response = await fetch(url, {
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
    console.error("벡터 검색 실패:", error);
    return NextResponse.json(
      { error: "벡터 검색 실패" },
      { status: 500 }
    );
  }
}
