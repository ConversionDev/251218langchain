'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BrainCircuit, ArrowLeft, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { RadarChartComponent } from '@/components/v20/intelligence/RadarChart';

// Mock 데이터: 특정 직원의 AI 분석 결과
const mockEmployeeAnalysis = {
  id: 1,
  name: '홍길동',
  employeeId: 'EMP001',
  department: '개발팀',
  position: '시니어 개발자',
  analyzedDate: '2024-01-15',
  successDnaMatch: 87.5,
  // 5개 역량 지표 (0-100 점수)
  capabilities: {
    leadership: 85,
    collaboration: 90,
    creativity: 78,
    problemSolving: 92,
    communication: 88,
  },
  // AI가 생성한 행동 패턴 요약
  behaviorSummary: `홍길동 직원은 강한 기술적 역량과 협업 능력을 보유하고 있습니다. 특히 문제 해결 능력이 뛰어나며, 복잡한 기술적 도전 과제를 체계적으로 접근합니다.

리더십 측면에서는 팀 내 기술적 의사결정을 주도하며, 주니어 개발자들을 멘토링하는 데 적극적입니다. 협업 능력은 매우 높아서 크로스 펑셔널 팀과의 소통이 원활하며, 프로젝트 진행 시 다른 팀원들의 의견을 적극 수렴합니다.

창의성은 보통 수준이지만, 실용적인 솔루션을 찾는 데 강점이 있습니다. 커뮤니케이션 능력도 우수하여 기술적 내용을 비기술자에게도 명확하게 전달할 수 있습니다.

전반적으로 Success DNA 모델과 87.5%의 높은 일치율을 보이며, 특히 문제 해결 능력과 협업 능력이 모델과 매우 유사한 패턴을 보입니다.`,
};

export default function IntelligenceDetailPage({ params }: { params: { id: string } }) {
  // Radar Chart 데이터 변환
  const radarData = [
    { subject: '리더십', value: mockEmployeeAnalysis.capabilities.leadership },
    { subject: '협업 능력', value: mockEmployeeAnalysis.capabilities.collaboration },
    { subject: '창의성', value: mockEmployeeAnalysis.capabilities.creativity },
    { subject: '문제 해결', value: mockEmployeeAnalysis.capabilities.problemSolving },
    { subject: '커뮤니케이션', value: mockEmployeeAnalysis.capabilities.communication },
  ];

  const getMatchColor = (match: number) => {
    if (match >= 90) return 'text-green-600 dark:text-green-400';
    if (match >= 80) return 'text-blue-600 dark:text-blue-400';
    return 'text-yellow-600 dark:text-yellow-400';
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" asChild>
            <Link href="/v20/intelligence">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              AI 분석 상세
            </h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              {mockEmployeeAnalysis.name} ({mockEmployeeAnalysis.employeeId}) - EXAONE AI 분석 결과
            </p>
          </div>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          <BrainCircuit className="mr-2 h-4 w-4" />
          Success DNA 일치율: <span className={`ml-2 font-bold ${getMatchColor(mockEmployeeAnalysis.successDnaMatch)}`}>
            {mockEmployeeAnalysis.successDnaMatch.toFixed(1)}%
          </span>
        </Badge>
      </div>

      {/* 기본 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>직원 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">이름</p>
              <p className="text-base font-semibold">{mockEmployeeAnalysis.name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">사번</p>
              <p className="text-base font-semibold">{mockEmployeeAnalysis.employeeId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">부서</p>
              <p className="text-base font-semibold">{mockEmployeeAnalysis.department}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">분석 완료일</p>
              <p className="text-base font-semibold">{mockEmployeeAnalysis.analyzedDate}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Radar Chart - 역량 분석 */}
        <Card>
          <CardHeader>
            <CardTitle>역량 분석 (Radar Chart)</CardTitle>
            <CardDescription>5개 핵심 역량 지표 시각화</CardDescription>
          </CardHeader>
          <CardContent>
            <RadarChartComponent data={radarData} employeeName={mockEmployeeAnalysis.name} />
            <div className="mt-4 grid grid-cols-2 gap-4">
              {radarData.map((item) => (
                <div key={item.subject} className="flex items-center justify-between rounded-lg border border-slate-200 p-3 dark:border-slate-800">
                  <span className="text-sm font-medium">{item.subject}</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-16 rounded-full bg-slate-200 dark:bg-slate-800">
                      <div
                        className="h-2 rounded-full bg-blue-500"
                        style={{ width: `${item.value}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold">{item.value}점</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 행동 패턴 요약 */}
        <Card>
          <CardHeader>
            <CardTitle>행동 패턴 요약</CardTitle>
            <CardDescription>AI(EXAONE)가 생성한 분석 요약</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                <div className="flex items-start gap-3">
                  <BrainCircuit className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium mb-2">AI 분석 결과</p>
                    <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
                      {mockEmployeeAnalysis.behaviorSummary}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* 역량 점수 요약 */}
              <div className="space-y-2">
                <p className="text-sm font-medium">역량 점수 요약</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600 dark:text-slate-400">최고 역량</span>
                    <Badge variant="outline" className="bg-green-50 dark:bg-green-900">
                      문제 해결: {mockEmployeeAnalysis.capabilities.problemSolving}점
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600 dark:text-slate-400">평균 역량</span>
                    <span className="text-sm font-semibold">
                      {(
                        Object.values(mockEmployeeAnalysis.capabilities).reduce((a, b) => a + b, 0) /
                        Object.values(mockEmployeeAnalysis.capabilities).length
                      ).toFixed(1)}점
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600 dark:text-slate-400">개선 필요 역량</span>
                    <Badge variant="outline" className="bg-yellow-50 dark:bg-yellow-900">
                      창의성: {mockEmployeeAnalysis.capabilities.creativity}점
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Success DNA 매칭 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>Success DNA 매칭 정보</CardTitle>
          <CardDescription>고성과자 모델과의 유사도 분석</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
                <TrendingUp className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-lg font-semibold">Success DNA 일치율</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {mockEmployeeAnalysis.department} 고성과자 모델 기준
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className={`text-4xl font-bold ${getMatchColor(mockEmployeeAnalysis.successDnaMatch)}`}>
                {mockEmployeeAnalysis.successDnaMatch.toFixed(1)}%
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                {mockEmployeeAnalysis.successDnaMatch >= 90
                  ? '매우 높은 일치율'
                  : mockEmployeeAnalysis.successDnaMatch >= 80
                  ? '높은 일치율'
                  : '보통 일치율'}
              </p>
            </div>
          </div>
          <div className="mt-4">
            <div className="h-3 w-full rounded-full bg-slate-200 dark:bg-slate-800">
              <div
                className={`h-3 rounded-full ${
                  mockEmployeeAnalysis.successDnaMatch >= 90
                    ? 'bg-green-500'
                    : mockEmployeeAnalysis.successDnaMatch >= 80
                    ? 'bg-blue-500'
                    : 'bg-yellow-500'
                }`}
                style={{ width: `${mockEmployeeAnalysis.successDnaMatch}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
