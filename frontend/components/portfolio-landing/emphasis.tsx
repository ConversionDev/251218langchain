import React from "react";

/**
 * 이력서(.hl)와 동일한 키워드 강조 — 문자열 내 **텍스트** 를 굵고 밝게 렌더링.
 * About·프로젝트 카드·모달·Career 등 포트폴리오 전역에서 공용.
 */
export function renderEmphasis(text: string): React.ReactNode {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  if (parts.length === 1) return text;
  return parts.map((p, i) =>
    i % 2 === 1 ? (
      <strong key={i} style={{ fontWeight: 800, color: "#ffffff" }}>
        {p}
      </strong>
    ) : (
      p
    )
  );
}
