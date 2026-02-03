import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, BrainCircuit, ShieldCheck, BarChart3, TrendingUp, UsersRound, MessageCircle } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          대시보드
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Success DNA 플랫폼 전체 현황을 한눈에 확인하세요.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Core HR</CardTitle>
            <Users className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              총 직원 수
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Talent Intelligence</CardTitle>
            <BrainCircuit className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">89</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              AI 분석 완료
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Verified Credentials</CardTitle>
            <ShieldCheck className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">567</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              발급된 증명서
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance</CardTitle>
            <BarChart3 className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">92%</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              평균 성과 달성률
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>최근 활동</CardTitle>
            <CardDescription>플랫폼 내 최근 업데이트 내역</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
                  <UsersRound className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">신규 직원 등록</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">2시간 전</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900">
                  <BrainCircuit className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">AI 분석 완료</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">5시간 전</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                  <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">성과 평가 업데이트</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">1일 전</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>빠른 액션</CardTitle>
            <CardDescription>자주 사용하는 기능에 빠르게 접근</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              <Link
                href="/core"
                className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
              >
                <Users className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                <span className="text-sm font-medium">직원 관리</span>
              </Link>
              <Link
                href="/intelligence"
                className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
              >
                <BrainCircuit className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                <span className="text-sm font-medium">AI 분석 실행</span>
              </Link>
              <Link
                href="/credential"
                className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
              >
                <ShieldCheck className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                <span className="text-sm font-medium">증명서 발급</span>
              </Link>
              <Link
                href="/performance"
                className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
              >
                <BarChart3 className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                <span className="text-sm font-medium">성과 리포트</span>
              </Link>
              <Link
                href="/chat"
                className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
              >
                <MessageCircle className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                <span className="text-sm font-medium">직원 상담</span>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
