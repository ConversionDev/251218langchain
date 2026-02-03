"use client";

import { useState } from "react";
import type { EmailMetadata } from "@/lib/types/spam";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface SpamDetectionFormProps {
  onSubmit: (emailMetadata: EmailMetadata) => void;
  isLoading?: boolean;
}

// 샘플 데이터
const SAMPLE_SPAM: EmailMetadata = {
  subject: "[긴급] 계좌 정지 예정! 지금 즉시 확인하세요!!!",
  sender: "security-alert@bank-kr.xyz",
  body: `긴급 안내드립니다!

고객님의 계좌가 비정상 거래로 인해 24시간 내 정지될 예정입니다.
즉시 아래 링크를 클릭하여 본인 인증을 완료하세요.

▶ 본인 인증하기: http://bank-verify.xyz/auth?id=38291

인증하지 않으시면 모든 금융 서비스가 중단됩니다.
카드번호, 비밀번호, 주민번호를 준비해주세요.

※ 이 메일은 발송 전용이며 회신되지 않습니다.`,
  date: "2026-01-20",
};

const SAMPLE_NORMAL: EmailMetadata = {
  subject: "이번 주 스터디 모임 일정 공유드립니다",
  sender: "kku1031@naver.com",
  body: `안녕하세요, 김규영입니다.

이번 주 토요일(1/25) 오후 2시에 강남역 스타벅스에서 스터디 모임이 있습니다.
이번 주제는 "LangGraph를 활용한 에이전트 개발"입니다.

참석 가능하신 분은 답장 부탁드립니다.
간단한 간식은 제가 준비할게요!

감사합니다.
김규영 드림`,
  date: "2026-01-20",
};

const SAMPLE_UNCERTAIN: EmailMetadata = {
  subject: "Re: 지난번 문의하신 건 관련",
  sender: "support@service-center.co.kr",
  body: `안녕하세요 고객님,

지난번 문의하신 환불 건에 대해 안내드립니다.
환불 처리를 위해 아래 정보가 필요합니다:

1. 주문번호
2. 결제하신 카드 마지막 4자리
3. 환불받으실 계좌번호

회신 부탁드립니다.

※ 본 메일은 고객센터 문의에 대한 답변입니다.
문의하신 적 없으시면 무시해주세요.`,
  date: "2026-01-20",
};

export default function SpamDetectionForm({
  onSubmit,
  isLoading = false,
}: SpamDetectionFormProps) {
  const [formData, setFormData] = useState<EmailMetadata>({
    subject: "",
    sender: "",
    body: "",
    date: "",
    attachments: [],
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.subject || !formData.sender) {
      alert("제목과 발신자는 필수 입력 항목입니다.");
      return;
    }
    onSubmit(formData);
  };

  const loadSample = (sample: EmailMetadata) => {
    setFormData(sample);
  };

  const inputClass =
    "px-3 py-3 rounded-lg text-sm font-inherit transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-300 bg-white text-slate-900 placeholder:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-400";
  const labelClass = "text-sm font-medium text-slate-700 dark:text-slate-300";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div className="flex flex-col gap-2">
        <Label htmlFor="subject" className={labelClass}>이메일 제목 *</Label>
        <Input
          type="text"
          id="subject"
          name="subject"
          value={formData.subject}
          onChange={handleChange}
          placeholder="예: 회의 일정 안내"
          required
          disabled={isLoading}
          className={inputClass}
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="sender" className={labelClass}>발신자 *</Label>
        <Input
          type="text"
          id="sender"
          name="sender"
          value={formData.sender}
          onChange={handleChange}
          placeholder="예: sender@example.com"
          required
          disabled={isLoading}
          className={inputClass}
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="body" className={labelClass}>이메일 본문</Label>
        <Textarea
          id="body"
          name="body"
          value={formData.body}
          onChange={handleChange}
          placeholder="이메일 내용을 입력하세요..."
          rows={6}
          disabled={isLoading}
          className={`${inputClass} resize-y min-h-[120px]`}
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="date" className={labelClass}>날짜</Label>
        <Input
          type="date"
          id="date"
          name="date"
          value={formData.date}
          onChange={handleChange}
          disabled={isLoading}
          className={inputClass}
        />
      </div>

      <div className="flex flex-col gap-4 pt-2">
        <Button
          type="submit"
          className="w-full sm:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 border-none rounded-lg text-white text-base font-semibold cursor-pointer transition-all shadow-sm hover:shadow disabled:opacity-60 disabled:cursor-not-allowed dark:bg-blue-600 dark:hover:bg-blue-700"
          disabled={isLoading || !formData.subject || !formData.sender}
        >
          {isLoading ? "분석 중..." : "스팸 감지 실행"}
        </Button>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-slate-500 dark:text-slate-400">샘플 데이터:</span>
          <Button
            type="button"
            variant="outline"
            className="px-3 py-1.5 border border-slate-300 rounded-lg bg-white text-slate-700 text-sm cursor-pointer transition-all hover:bg-slate-50 hover:border-slate-400 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            onClick={() => loadSample(SAMPLE_SPAM)}
            disabled={isLoading}
          >
            명확한 스팸
          </Button>
          <Button
            type="button"
            variant="outline"
            className="px-3 py-1.5 border border-slate-300 rounded-lg bg-white text-slate-700 text-sm cursor-pointer transition-all hover:bg-slate-50 hover:border-slate-400 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            onClick={() => loadSample(SAMPLE_NORMAL)}
            disabled={isLoading}
          >
            명확한 정상
          </Button>
          <Button
            type="button"
            variant="outline"
            className="px-3 py-1.5 border border-slate-300 rounded-lg bg-white text-slate-700 text-sm cursor-pointer transition-all hover:bg-slate-50 hover:border-slate-400 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            onClick={() => loadSample(SAMPLE_UNCERTAIN)}
            disabled={isLoading}
          >
            애매한 케이스
          </Button>
        </div>
      </div>
    </form>
  );
}
