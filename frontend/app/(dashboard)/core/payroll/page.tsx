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
import { DollarSign, Calendar, Download, Search } from 'lucide-react';

// 임시 급여 데이터
const mockPayroll = [
  { id: 1, employeeId: 'EMP001', name: '홍길동', department: '개발팀', baseSalary: 5000000, bonus: 500000, tax: 550000, netSalary: 4950000, month: '2024-01' },
  { id: 2, employeeId: 'EMP002', name: '김철수', department: '마케팅팀', baseSalary: 4500000, bonus: 300000, tax: 480000, netSalary: 4320000, month: '2024-01' },
  { id: 3, employeeId: 'EMP003', name: '이영희', department: '인사팀', baseSalary: 4200000, bonus: 200000, tax: 440000, netSalary: 3960000, month: '2024-01' },
  { id: 4, employeeId: 'EMP004', name: '박민수', department: '개발팀', baseSalary: 3500000, bonus: 150000, tax: 365000, netSalary: 3285000, month: '2024-01' },
  { id: 5, employeeId: 'EMP005', name: '최지은', department: '디자인팀', baseSalary: 3800000, bonus: 250000, tax: 405000, netSalary: 3645000, month: '2024-01' },
];

export default function PayrollPage() {
  const [selectedMonth, setSelectedMonth] = useState('2024-01');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredPayroll = mockPayroll.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.employeeId.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalBaseSalary = filteredPayroll.reduce((sum, item) => sum + item.baseSalary, 0);
  const totalBonus = filteredPayroll.reduce((sum, item) => sum + item.bonus, 0);
  const totalTax = filteredPayroll.reduce((sum, item) => sum + item.tax, 0);
  const totalNetSalary = filteredPayroll.reduce((sum, item) => sum + item.netSalary, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          급여 관리
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          급여 계산, 조회 및 관리
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 기본급</CardTitle>
            <DollarSign className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₩{(totalBaseSalary / 1000000).toFixed(1)}M
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {filteredPayroll.length}명 기준
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 보너스</CardTitle>
            <DollarSign className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₩{(totalBonus / 1000000).toFixed(1)}M
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              성과 보너스
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 세금</CardTitle>
            <DollarSign className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₩{(totalTax / 1000000).toFixed(1)}M
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              공제액
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 지급액</CardTitle>
            <DollarSign className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₩{(totalNetSalary / 1000000).toFixed(1)}M
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              실지급액
            </p>
          </CardContent>
        </Card>
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
                placeholder="이름, 사번으로 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-slate-400" />
              <Input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="w-40"
              />
            </div>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              엑셀 다운로드
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 급여 목록 테이블 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>급여 명세</CardTitle>
              <CardDescription>
                {selectedMonth} 급여 내역 ({filteredPayroll.length}명)
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
                <TableHead className="text-right">기본급</TableHead>
                <TableHead className="text-right">보너스</TableHead>
                <TableHead className="text-right">세금</TableHead>
                <TableHead className="text-right">실지급액</TableHead>
                <TableHead>상태</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPayroll.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.employeeId}</TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.department}</TableCell>
                  <TableCell className="text-right">
                    ₩{(item.baseSalary / 10000).toFixed(0)}만
                  </TableCell>
                  <TableCell className="text-right">
                    ₩{(item.bonus / 10000).toFixed(0)}만
                  </TableCell>
                  <TableCell className="text-right">
                    ₩{(item.tax / 10000).toFixed(0)}만
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    ₩{(item.netSalary / 10000).toFixed(0)}만
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">지급 완료</Badge>
                  </TableCell>
                </TableRow>
              ))}
              <TableRow className="bg-slate-50 dark:bg-slate-900">
                <TableCell colSpan={3} className="font-semibold">
                  합계
                </TableCell>
                <TableCell className="text-right font-semibold">
                  ₩{(totalBaseSalary / 1000000).toFixed(1)}M
                </TableCell>
                <TableCell className="text-right font-semibold">
                  ₩{(totalBonus / 1000000).toFixed(1)}M
                </TableCell>
                <TableCell className="text-right font-semibold">
                  ₩{(totalTax / 1000000).toFixed(1)}M
                </TableCell>
                <TableCell className="text-right font-semibold">
                  ₩{(totalNetSalary / 1000000).toFixed(1)}M
                </TableCell>
                <TableCell></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
