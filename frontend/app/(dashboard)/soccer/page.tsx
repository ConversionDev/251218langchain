"use client";

import { SoccerUploadSection, EmbeddingSyncSection } from "@/modules/soccer/components";
import type { SoccerDataType } from "@/modules/soccer/services";

/** FK 의존 순서: 경기장 → 팀 → 선수 → 일정 */
const DATA_TYPES: SoccerDataType[] = ["stadiums", "teams", "players", "schedules"];

export default function SoccerPage() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Soccer</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          아래 순서대로 진행하세요: 1) 데이터 업로드 → 2) 임베딩 동기화
        </p>
      </div>

      {/* 1단계: 선수·팀·일정·경기장 테이블에 데이터 넣기 */}
      <section className="space-y-3">
        <div>
          <h2 className="text-lg font-medium text-foreground">
            <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
              1
            </span>
            데이터 업로드
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            JSONL 파일을 업로드하면 선수·팀·일정·경기장 테이블에 저장됩니다. 필요한 항목만 순서대로 업로드하세요.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {DATA_TYPES.map((type) => (
            <SoccerUploadSection key={type} dataType={type} />
          ))}
        </div>
      </section>

      {/* 2단계: 업로드된 데이터를 임베딩 테이블로 동기화 */}
      <section className="space-y-3">
        <div>
          <h2 className="text-lg font-medium text-foreground">
            <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
              2
            </span>
            임베딩 동기화
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            위에서 넣은 데이터를 벡터화해 RAG 검색용 임베딩 테이블에 반영합니다. 1단계 완료 후 실행하세요.
          </p>
        </div>
        <EmbeddingSyncSection />
      </section>
    </div>
  );
}
