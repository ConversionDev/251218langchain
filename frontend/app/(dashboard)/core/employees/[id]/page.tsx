import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Users, Mail, Phone, Calendar, MapPin, Edit } from 'lucide-react';
import Link from 'next/link';

// 임시 직원 상세 데이터 (나중에 API로 대체)
const mockEmployee = {
  id: 1,
  employeeId: 'EMP001',
  name: '홍길동',
  department: '개발팀',
  position: '시니어 개발자',
  status: '재직',
  email: 'hong@example.com',
  phone: '010-1234-5678',
  address: '서울시 강남구',
  joinDate: '2020-01-15',
  birthDate: '1990-05-20',
};

export default async function EmployeeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            직원 상세 정보
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            직원 정보 조회 및 수정
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/core/employees">목록으로</Link>
          </Button>
          <Button asChild>
            <Link href={`/core/employees/${id}/edit`}>
              <Edit className="mr-2 h-4 w-4" />
              수정
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* 기본 정보 */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>기본 정보</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
                  <Users className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold">{mockEmployee.name}</h2>
                  <p className="text-slate-600 dark:text-slate-400">
                    {mockEmployee.employeeId} · {mockEmployee.position}
                  </p>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    부서
                  </label>
                  <p className="mt-1 text-base">{mockEmployee.department}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    직급
                  </label>
                  <p className="mt-1 text-base">{mockEmployee.position}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    상태
                  </label>
                  <p className="mt-1">
                    <Badge variant="outline">{mockEmployee.status}</Badge>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    입사일
                  </label>
                  <p className="mt-1 text-base">{mockEmployee.joinDate}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 연락처 정보 */}
        <Card>
          <CardHeader>
            <CardTitle>연락처 정보</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm font-medium">이메일</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {mockEmployee.email}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm font-medium">연락처</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {mockEmployee.phone}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm font-medium">주소</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {mockEmployee.address}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm font-medium">생년월일</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {mockEmployee.birthDate}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 추가 정보 섹션들 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>급여 정보</CardTitle>
            <CardDescription>최근 급여 내역</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">기본급</span>
                <span className="font-medium">₩5,000,000</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">보너스</span>
                <span className="font-medium">₩500,000</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="text-sm font-medium">실지급액</span>
                <span className="font-semibold">₩4,950,000</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>근태 정보</CardTitle>
            <CardDescription>이번 달 근태 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">출근일수</span>
                <span className="font-medium">22일</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">지각</span>
                <span className="font-medium">0회</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">출근률</span>
                <span className="font-semibold text-green-600 dark:text-green-400">100%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
