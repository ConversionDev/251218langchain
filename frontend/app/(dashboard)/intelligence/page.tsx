'use client';

import { useState } from 'react';
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
import { BrainCircuit, TrendingUp, Search, Eye, ArrowRight } from 'lucide-react';
import Link from 'next/link';

// Mock 데이터: AI 분석 완료된 직원 리스트
const mockAnalyzedEmployees = [
  {
    id: 1,
    name: '홍길동',
    employeeId: 'EMP001',
    department: '개발팀',
    position: '시니어 개발자',
    analyzedDate: '2024-01-15',
    successDnaMatch: 87.5,
    status: '완료',
  },
  {
    id: 2,
    name: '김철수',
    employeeId: 'EMP002',
    department: '마케팅팀',
    position: '마케팅 매니저',
    analyzedDate: '2024-01-14',
    successDnaMatch: 92.3,
    status: '완료',
  },
  {
    id: 3,
    name: '이영희',
    employeeId: 'EMP003',
    department: '인사팀',
    position: 'HR 전문가',
    analyzedDate: '2024-01-13',
    successDnaMatch: 78.9,
    status: '완료',
  },
  {
    id: 4,
    name: '박민수',
    employeeId: 'EMP004',
    department: '개발팀',
    position: '주니어 개발자',
    analyzedDate: '2024-01-12',
    successDnaMatch: 85.2,
    status: '완료',
  },
  {
    id: 5,
    name: '최지은',
    employeeId: 'EMP005',
    department: '디자인팀',
    position: 'UI/UX 디자이너',
    analyzedDate: '2024-01-11',
    successDnaMatch: 91.7,
    status: '완료',
  },
  {
    id: 6,
    name: '정수진',
    employeeId: 'EMP006',
    department: '영업팀',
    position: '영업 대표',
    analyzedDate: '2024-01-10',
    successDnaMatch: 88.4,
    status: '완료',
  },
];

export default function IntelligencePage() {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredEmployees = mockAnalyzedEmployees.filter(
    (employee) =>
      employee.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      employee.employeeId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      employee.department.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Success DNA 일치율 통계
  const avgMatch = mockAnalyzedEmployees.reduce((sum, emp) => sum + emp.successDnaMatch, 0) / mockAnalyzedEmployees.length;
  const highMatch = mockAnalyzedEmployees.filter(emp => emp.successDnaMatch >= 90).length;
  const mediumMatch = mockAnalyzedEmployees.filter(emp => emp.successDnaMatch >= 80 && emp.successDnaMatch < 90).length;
  const lowMatch = mockAnalyzedEmployees.filter(emp => emp.successDnaMatch < 80).length;

  const getMatchColor = (match: number) => {
    if (match >= 90) return 'text-green-600 dark:text-green-400';
    if (match >= 80) return 'text-blue-600 dark:text-blue-400';
    return 'text-yellow-600 dark:text-yellow-400';
  };

  const getMatchBadgeVariant = (
    match: number
  ): 'default' | 'outline' | 'destructive' | 'secondary' => {
    if (match >= 90) return 'default';
    if (match >= 80) return 'secondary';
    return 'outline';
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Talent Intelligence
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            AI(EXAONE) 기반 비정형 데이터 분석 및 Success DNA 매칭
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/intelligence/matching">
            <BrainCircuit className="mr-2 h-4 w-4" />
            매칭 툴
          </Link>
        </Button>
      </div>

      {/* Success DNA 일치율 통계 카드 */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 일치율</CardTitle>
            <TrendingUp className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getMatchColor(avgMatch)}`}>
              {avgMatch.toFixed(1)}%
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              전체 직원 평균
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">높은 일치율</CardTitle>
            <BrainCircuit className="h-4 w-4 text-green-600 dark:text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {highMatch}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              90% 이상 ({((highMatch / mockAnalyzedEmployees.length) * 100).toFixed(0)}%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">보통 일치율</CardTitle>
            <BrainCircuit className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {mediumMatch}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              80-90% ({((mediumMatch / mockAnalyzedEmployees.length) * 100).toFixed(0)}%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">낮은 일치율</CardTitle>
            <BrainCircuit className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {lowMatch}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              80% 미만 ({((lowMatch / mockAnalyzedEmployees.length) * 100).toFixed(0)}%)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 검색 */}
      <Card>
        <CardHeader>
          <CardTitle>검색</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="이름, 사번, 부서로 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-10 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
        </CardContent>
      </Card>

      {/* AI 분석 완료된 직원 리스트 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>최근 AI 분석 완료 직원</CardTitle>
              <CardDescription>
                EXAONE AI가 분석한 직원 리스트 및 Success DNA 일치율
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>사번</TableHead>
                <TableHead>이름</TableHead>
                <TableHead>부서</TableHead>
                <TableHead>직급</TableHead>
                <TableHead>분석 완료일</TableHead>
                <TableHead className="text-center">Success DNA 일치율</TableHead>
                <TableHead>상태</TableHead>
                <TableHead className="text-right">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEmployees.map((employee) => (
                <TableRow key={employee.id}>
                  <TableCell className="font-medium">{employee.employeeId}</TableCell>
                  <TableCell>{employee.name}</TableCell>
                  <TableCell>{employee.department}</TableCell>
                  <TableCell>{employee.position}</TableCell>
                  <TableCell>{employee.analyzedDate}</TableCell>
                  <TableCell className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className={`text-lg font-bold ${getMatchColor(employee.successDnaMatch)}`}>
                        {employee.successDnaMatch.toFixed(1)}%
                      </span>
                      <div className="h-2 w-20 rounded-full bg-slate-200 dark:bg-slate-800">
                        <div
                          className={`h-2 rounded-full ${
                            employee.successDnaMatch >= 90
                              ? 'bg-green-500'
                              : employee.successDnaMatch >= 80
                              ? 'bg-blue-500'
                              : 'bg-yellow-500'
                          }`}
                          style={{ width: `${employee.successDnaMatch}%` }}
                        />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getMatchBadgeVariant(employee.successDnaMatch)}>
                      {employee.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/intelligence/${employee.id}`}>
                        <Eye className="mr-2 h-4 w-4" />
                        상세 보기
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
