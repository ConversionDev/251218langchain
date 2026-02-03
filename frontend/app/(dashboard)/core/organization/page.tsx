import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Users, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function OrganizationPage() {
  // 임시 조직 구조 데이터
  const organization = [
    {
      id: 1,
      name: '경영진',
      manager: 'CEO',
      employees: 3,
      children: [
        {
          id: 2,
          name: '개발팀',
          manager: '강민호',
          employees: 25,
          children: [
            { id: 3, name: '프론트엔드', manager: '홍길동', employees: 8 },
            { id: 4, name: '백엔드', manager: '박민수', employees: 12 },
            { id: 5, name: '인프라', manager: '이철수', employees: 5 },
          ],
        },
        {
          id: 6,
          name: '마케팅팀',
          manager: '김철수',
          employees: 15,
          children: [
            { id: 7, name: '디지털 마케팅', manager: '윤서연', employees: 8 },
            { id: 8, name: '콘텐츠', manager: '최지은', employees: 7 },
          ],
        },
        {
          id: 9,
          name: '인사팀',
          manager: '이영희',
          employees: 12,
        },
        {
          id: 10,
          name: '영업팀',
          manager: '정수진',
          employees: 20,
        },
      ],
    },
  ];

  const renderDepartment = (dept: any, level: number = 0) => {
    return (
      <div key={dept.id} className="ml-4">
        <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4 dark:border-slate-800">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
            <Building2 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold">{dept.name}</h3>
              <Badge variant="outline">{dept.employees}명</Badge>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              팀장: {dept.manager}
            </p>
          </div>
        </div>
        {dept.children && (
          <div className="mt-2 border-l-2 border-slate-200 pl-4 dark:border-slate-800">
            {dept.children.map((child: any) => renderDepartment(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          조직도
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          조직 구조 시각화 및 관리
        </p>
      </div>

      {/* 조직 통계 */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 부서 수</CardTitle>
            <Building2 className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              전체 조직 단위
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 직원 수</CardTitle>
            <Users className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              전체 직원
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 부서 인원</CardTitle>
            <Users className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">51</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              부서당 평균
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 조직도 트리 */}
      <Card>
        <CardHeader>
          <CardTitle>조직 구조</CardTitle>
          <CardDescription>계층형 조직 구조 트리</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {organization.map((dept) => renderDepartment(dept))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
