import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Building2, Calendar, DollarSign, Search, Plus, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';

export default function CoreHRPage() {
  // 임시 데이터 (나중에 API로 대체)
  const employees = [
    { id: 1, name: '홍길동', department: '개발팀', position: '시니어 개발자', status: '재직', joinDate: '2020-01-15' },
    { id: 2, name: '김철수', department: '마케팅팀', position: '마케팅 매니저', status: '재직', joinDate: '2019-03-20' },
    { id: 3, name: '이영희', department: '인사팀', position: 'HR 전문가', status: '재직', joinDate: '2021-06-10' },
    { id: 4, name: '박민수', department: '개발팀', position: '주니어 개발자', status: '재직', joinDate: '2023-09-01' },
    { id: 5, name: '최지은', department: '디자인팀', position: 'UI/UX 디자이너', status: '재직', joinDate: '2022-02-14' },
  ];

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Core HR
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            정형 HR 데이터 관리 및 직원 정보 시스템
          </p>
        </div>
        <Button asChild>
          <Link href="/v20/core/employees/new">
            <Plus className="mr-2 h-4 w-4" />
            신규 직원 등록
          </Link>
        </Button>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 직원 수</CardTitle>
            <Users className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              <span className="text-green-600 dark:text-green-400">+12</span> 이번 달
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">부서 수</CardTitle>
            <Building2 className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              조직 구조
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">출근률</CardTitle>
            <Calendar className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">96.5%</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              이번 달 평균
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 급여</CardTitle>
            <DollarSign className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₩4.2M</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              월 평균
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 빠른 액션 */}
      <div className="grid gap-6 md:grid-cols-4">
        <Link href="/v20/core/employees">
          <Card className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-900">
            <CardHeader>
              <CardTitle className="text-base">직원 관리</CardTitle>
              <CardDescription>직원 목록 및 정보 관리</CardDescription>
            </CardHeader>
          </Card>
        </Link>
        <Link href="/v20/core/organization">
          <Card className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-900">
            <CardHeader>
              <CardTitle className="text-base">조직도</CardTitle>
              <CardDescription>조직 구조 시각화 및 관리</CardDescription>
            </CardHeader>
          </Card>
        </Link>
        <Link href="/v20/core/payroll">
          <Card className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-900">
            <CardHeader>
              <CardTitle className="text-base">급여 관리</CardTitle>
              <CardDescription>급여 계산 및 관리</CardDescription>
            </CardHeader>
          </Card>
        </Link>
        <Link href="/v20/core/attendance">
          <Card className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-900">
            <CardHeader>
              <CardTitle className="text-base">근태 관리</CardTitle>
              <CardDescription>출퇴근 및 근태 관리</CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>

      {/* 최근 직원 목록 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>최근 직원 목록</CardTitle>
              <CardDescription>최근 등록된 직원 정보</CardDescription>
            </div>
            <Link href="/v20/core/employees">
              <Button variant="outline" size="sm">
                전체 보기
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {employees.slice(0, 5).map((employee) => (
              <div
                key={employee.id}
                className="flex items-center justify-between rounded-lg border border-slate-200 p-4 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
                    <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="font-medium">{employee.name}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {employee.department} · {employee.position}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <Badge variant="outline">{employee.status}</Badge>
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    입사일: {employee.joinDate}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
