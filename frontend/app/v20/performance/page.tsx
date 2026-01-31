'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Trophy, BarChart3, Target, TrendingUp, Award, GitCompare } from 'lucide-react';
import Link from 'next/link';
import { mockPerformanceRankings, mockPerformanceTrend } from '@/lib/mock-data';

export default function PerformancePage() {
  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    if (rank === 2) return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200';
    if (rank === 3) return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    return '';
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Performance Analytics
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            종합 성과 분석 대시보드 (Core Score 40% + AI DNA Score 60%)
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/v20/performance/compare">
            <GitCompare className="mr-2 h-4 w-4" />
            비교 분석
          </Link>
        </Button>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 종합 점수</CardTitle>
            <BarChart3 className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(
                mockPerformanceRankings.reduce((sum, emp) => sum + emp.totalScore, 0) /
                mockPerformanceRankings.length
              ).toFixed(1)}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              전체 직원 평균
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 Core Score</CardTitle>
            <Target className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {(
                mockPerformanceRankings.reduce((sum, emp) => sum + emp.coreScore, 0) /
                mockPerformanceRankings.length
              ).toFixed(1)}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              정량 지표 (40%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 AI DNA Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {(
                mockPerformanceRankings.reduce((sum, emp) => sum + emp.aiDnaScore, 0) /
                mockPerformanceRankings.length
              ).toFixed(1)}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              AI 분석 (60%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">차세대 리더</CardTitle>
            <Trophy className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {mockPerformanceRankings.filter((emp) => emp.totalScore >= 90).length}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              90점 이상
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 종합 랭킹 테이블 */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              <div>
                <CardTitle>차세대 리더 랭킹</CardTitle>
                <CardDescription>정량 지표 + AI DNA 점수 종합 랭킹</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">순위</TableHead>
                  <TableHead>이름</TableHead>
                  <TableHead className="text-right">Core (40%)</TableHead>
                  <TableHead className="text-right">AI DNA (60%)</TableHead>
                  <TableHead className="text-right">종합 점수</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockPerformanceRankings.map((employee) => (
                  <TableRow key={employee.id}>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`${
                          employee.rank <= 3 ? getRankBadgeColor(employee.rank) : ''
                        }`}
                      >
                        {employee.rank}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{employee.name}</p>
                        <p className="text-xs text-slate-600 dark:text-slate-400">
                          {employee.department}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                        {employee.coreScore}점
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="text-sm font-semibold text-purple-600 dark:text-purple-400">
                        {employee.aiDnaScore}점
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <span className="text-lg font-bold">
                          {employee.totalScore}점
                        </span>
                        {employee.rank <= 3 && (
                          <Award className={`h-4 w-4 ${
                            employee.rank === 1 ? 'text-yellow-600' :
                            employee.rank === 2 ? 'text-slate-600' :
                            'text-orange-600'
                          }`} />
                        )}
                      </div>
                      <div className="h-1 w-16 ml-auto mt-1 rounded-full bg-slate-200 dark:bg-slate-800">
                        <div
                          className="h-1 rounded-full bg-blue-500"
                          style={{ width: `${employee.totalScore}%` }}
                        />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* 성과 추이 차트 */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              <div>
                <CardTitle>성과 추이</CardTitle>
                <CardDescription>월별 성과 변화</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockPerformanceTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                />
                <YAxis domain={[70, 100]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="coreScore"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Core Score (40%)"
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="aiDnaScore"
                  stroke="#a855f7"
                  strokeWidth={2}
                  name="AI DNA Score (60%)"
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="totalScore"
                  stroke="#10b981"
                  strokeWidth={3}
                  name="종합 점수"
                  dot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600 dark:text-slate-400">가중치 적용</span>
                <span className="font-semibold">
                  Core Score × 0.4 + AI DNA Score × 0.6 = 종합 점수
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 가중치 설명 */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <div>
              <CardTitle>점수 계산 방식</CardTitle>
              <CardDescription>종합 점수 산정 방법</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <span className="font-semibold text-blue-900 dark:text-blue-100">
                    Core Score
                  </span>
                </div>
                <Badge variant="outline" className="border-blue-500 text-blue-700 dark:text-blue-300">
                  40%
                </Badge>
              </div>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                정형 HR 데이터 기반 정량 지표 (근태, 급여, 평가 등)
              </p>
            </div>
            <div className="rounded-lg border border-purple-200 bg-purple-50 p-4 dark:border-purple-800 dark:bg-purple-900">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  <span className="font-semibold text-purple-900 dark:text-purple-100">
                    AI DNA Score
                  </span>
                </div>
                <Badge variant="outline" className="border-purple-500 text-purple-700 dark:text-purple-300">
                  60%
                </Badge>
              </div>
              <p className="text-sm text-purple-700 dark:text-purple-300">
                AI(EXAONE) 기반 비정형 데이터 분석 점수 (Success DNA 일치율)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
