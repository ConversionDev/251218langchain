'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend } from 'recharts';
import { ArrowLeft, Users, X, Trophy, Target } from 'lucide-react';
import Link from 'next/link';
import { mockPerformanceRankings } from '@/lib/mock-data';

export default function ComparePage() {
  const [selectedEmployees, setSelectedEmployees] = useState<number[]>([]);

  const toggleEmployee = (id: number) => {
    if (selectedEmployees.includes(id)) {
      setSelectedEmployees(selectedEmployees.filter((empId) => empId !== id));
    } else {
      if (selectedEmployees.length < 5) {
        setSelectedEmployees([...selectedEmployees, id]);
      }
    }
  };

  const removeEmployee = (id: number) => {
    setSelectedEmployees(selectedEmployees.filter((empId) => empId !== id));
  };

  const selectedEmployeesData = mockPerformanceRankings.filter((emp) =>
    selectedEmployees.includes(emp.id)
  );

  // Radar Chart 데이터 생성
  const radarData = [
    '리더십',
    '협업 능력',
    '창의성',
    '문제 해결',
    '커뮤니케이션',
  ].map((subject) => {
    const dataPoint: any = { subject };
    selectedEmployeesData.forEach((emp, index) => {
      const capabilityKey = subject === '리더십' ? 'leadership' :
        subject === '협업 능력' ? 'collaboration' :
        subject === '창의성' ? 'creativity' :
        subject === '문제 해결' ? 'problemSolving' : 'communication';
      dataPoint[`employee${index + 1}`] = emp.capabilities[capabilityKey as keyof typeof emp.capabilities];
    });
    return dataPoint;
  });

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" asChild>
            <Link href="/performance">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              비교 분석
            </h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              두 명 이상의 직원을 선택하여 역량을 비교하세요 (최대 5명)
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* 직원 선택 */}
        <Card className="md:col-span-1">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <div>
                <CardTitle>직원 선택</CardTitle>
                <CardDescription>
                  비교할 직원을 선택하세요 ({selectedEmployees.length}/5)
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {mockPerformanceRankings.map((emp) => (
                <button
                  key={emp.id}
                  onClick={() => toggleEmployee(emp.id)}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    selectedEmployees.includes(emp.id)
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900'
                      : 'border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{emp.name}</p>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        {emp.department} · 종합: {emp.totalScore}점
                      </p>
                    </div>
                    {selectedEmployees.includes(emp.id) && (
                      <Badge variant="outline" className="border-blue-500 text-blue-700 dark:text-blue-300">
                        선택됨
                      </Badge>
                    )}
                    {emp.rank <= 3 && (
                      <Trophy className={`h-4 w-4 ${
                        emp.rank === 1 ? 'text-yellow-600' :
                        emp.rank === 2 ? 'text-slate-600' :
                        'text-orange-600'
                      }`} />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 비교 결과 */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                <div>
                  <CardTitle>역량 비교</CardTitle>
                  <CardDescription>선택된 직원들의 역량 Radar Chart</CardDescription>
                </div>
              </div>
              {selectedEmployees.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedEmployees([])}
                >
                  모두 해제
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {selectedEmployees.length === 0 ? (
              <div className="flex h-96 items-center justify-center rounded-lg border border-dashed border-slate-300 dark:border-slate-700">
                <div className="text-center">
                  <Users className="mx-auto h-12 w-12 text-slate-400" />
                  <p className="mt-4 text-sm font-medium text-slate-600 dark:text-slate-400">
                    비교할 직원을 선택하세요
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    {selectedEmployeesData.map((emp, index) => (
                      <Radar
                        key={emp.id}
                        name={emp.name}
                        dataKey={`employee${index + 1}`}
                        stroke={colors[index]}
                        fill={colors[index]}
                        fillOpacity={0.3}
                      />
                    ))}
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>

                {/* 선택된 직원 정보 */}
                <div className="space-y-4">
                  <p className="font-semibold">선택된 직원 정보</p>
                  <div className="grid gap-4 md:grid-cols-2">
                    {selectedEmployeesData.map((emp, index) => (
                      <Card key={emp.id} className="border-2" style={{ borderColor: colors[index] }}>
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <CardTitle className="text-base">{emp.name}</CardTitle>
                                {emp.rank <= 3 && (
                                  <Trophy className={`h-4 w-4 ${
                                    emp.rank === 1 ? 'text-yellow-600' :
                                    emp.rank === 2 ? 'text-slate-600' :
                                    'text-orange-600'
                                  }`} />
                                )}
                              </div>
                              <CardDescription>{emp.department}</CardDescription>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => removeEmployee(emp.id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-slate-600 dark:text-slate-400">Core Score</span>
                              <span className="font-semibold text-blue-600 dark:text-blue-400">
                                {emp.coreScore}점
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-slate-600 dark:text-slate-400">AI DNA Score</span>
                              <span className="font-semibold text-purple-600 dark:text-purple-400">
                                {emp.aiDnaScore}점
                              </span>
                            </div>
                            <div className="flex items-center justify-between border-t pt-2">
                              <span className="font-medium">종합 점수</span>
                              <span className="text-lg font-bold">{emp.totalScore}점</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-slate-600 dark:text-slate-400">랭킹</span>
                              <Badge variant="outline">
                                {emp.rank}위
                              </Badge>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
