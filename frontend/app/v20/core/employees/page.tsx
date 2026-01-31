'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, Plus, Edit, MoreVertical, Filter } from 'lucide-react';
import Link from 'next/link';

// 임시 데이터 (나중에 API로 대체)
const mockEmployees = [
  { id: 1, name: '홍길동', employeeId: 'EMP001', department: '개발팀', position: '시니어 개발자', status: '재직', email: 'hong@example.com', phone: '010-1234-5678', joinDate: '2020-01-15' },
  { id: 2, name: '김철수', employeeId: 'EMP002', department: '마케팅팀', position: '마케팅 매니저', status: '재직', email: 'kim@example.com', phone: '010-2345-6789', joinDate: '2019-03-20' },
  { id: 3, name: '이영희', employeeId: 'EMP003', department: '인사팀', position: 'HR 전문가', status: '재직', email: 'lee@example.com', phone: '010-3456-7890', joinDate: '2021-06-10' },
  { id: 4, name: '박민수', employeeId: 'EMP004', department: '개발팀', position: '주니어 개발자', status: '재직', email: 'park@example.com', phone: '010-4567-8901', joinDate: '2023-09-01' },
  { id: 5, name: '최지은', employeeId: 'EMP005', department: '디자인팀', position: 'UI/UX 디자이너', status: '재직', email: 'choi@example.com', phone: '010-5678-9012', joinDate: '2022-02-14' },
  { id: 6, name: '정수진', employeeId: 'EMP006', department: '영업팀', position: '영업 대표', status: '재직', email: 'jung@example.com', phone: '010-6789-0123', joinDate: '2021-11-05' },
  { id: 7, name: '강민호', employeeId: 'EMP007', department: '개발팀', position: '테크리드', status: '재직', email: 'kang@example.com', phone: '010-7890-1234', joinDate: '2018-07-20' },
  { id: 8, name: '윤서연', employeeId: 'EMP008', department: '마케팅팀', position: '콘텐츠 매니저', status: '재직', email: 'yoon@example.com', phone: '010-8901-2345', joinDate: '2022-05-12' },
];

export default function EmployeesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState<string>('all');

  const filteredEmployees = mockEmployees.filter((employee) => {
    const matchesSearch = 
      employee.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      employee.employeeId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      employee.email.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesDepartment = selectedDepartment === 'all' || employee.department === selectedDepartment;
    
    return matchesSearch && matchesDepartment;
  });

  const departments = Array.from(new Set(mockEmployees.map(emp => emp.department)));

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            직원 관리
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            직원 정보 조회, 등록, 수정 및 관리
          </p>
        </div>
        <Button asChild>
          <Link href="/v20/core/employees/new">
            <Plus className="mr-2 h-4 w-4" />
            신규 등록
          </Link>
        </Button>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <CardHeader>
          <CardTitle>검색 및 필터</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="이름, 사번, 이메일로 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
              >
                <option value="all">전체 부서</option>
                {departments.map((dept) => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 직원 목록 테이블 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>직원 목록</CardTitle>
              <CardDescription>
                총 {filteredEmployees.length}명의 직원이 검색되었습니다.
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
                <TableHead>이메일</TableHead>
                <TableHead>연락처</TableHead>
                <TableHead>입사일</TableHead>
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
                  <TableCell>{employee.email}</TableCell>
                  <TableCell>{employee.phone}</TableCell>
                  <TableCell>{employee.joinDate}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{employee.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="icon" asChild>
                        <Link href={`/v20/core/employees/${employee.id}`}>
                          <Edit className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </div>
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
