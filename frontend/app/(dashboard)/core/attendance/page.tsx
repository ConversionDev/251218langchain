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
import { Calendar, Clock, Search, Download, CheckCircle2, XCircle } from 'lucide-react';

// 임시 근태 데이터
const mockAttendance = [
  { id: 1, employeeId: 'EMP001', name: '홍길동', department: '개발팀', date: '2024-01-15', checkIn: '09:00', checkOut: '18:00', workHours: 9, status: '정상' },
  { id: 2, employeeId: 'EMP002', name: '김철수', department: '마케팅팀', date: '2024-01-15', checkIn: '09:15', checkOut: '18:30', workHours: 9.25, status: '정상' },
  { id: 3, employeeId: 'EMP003', name: '이영희', department: '인사팀', date: '2024-01-15', checkIn: '08:45', checkOut: '17:45', workHours: 9, status: '정상' },
  { id: 4, employeeId: 'EMP004', name: '박민수', department: '개발팀', date: '2024-01-15', checkIn: '09:30', checkOut: '18:00', workHours: 8.5, status: '지각' },
  { id: 5, employeeId: 'EMP005', name: '최지은', department: '디자인팀', date: '2024-01-15', checkIn: '09:00', checkOut: null, workHours: 0, status: '미퇴근' },
];

export default function AttendancePage() {
  const [selectedDate, setSelectedDate] = useState('2024-01-15');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAttendance = mockAttendance.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.employeeId.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const normalCount = filteredAttendance.filter(item => item.status === '정상').length;
  const lateCount = filteredAttendance.filter(item => item.status === '지각').length;
  const absentCount = filteredAttendance.filter(item => item.status === '결근').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          근태 관리
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          출퇴근 기록 및 근태 현황 관리
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">정상 출근</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{normalCount}</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              명
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">지각</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{lateCount}</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              명
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">결근</CardTitle>
            <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{absentCount}</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              명
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">출근률</CardTitle>
            <Calendar className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filteredAttendance.length > 0 
                ? ((normalCount / filteredAttendance.length) * 100).toFixed(1)
                : 0}%
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              정상 출근률
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
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
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

      {/* 근태 목록 테이블 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>출퇴근 기록</CardTitle>
              <CardDescription>
                {selectedDate} 근태 현황 ({filteredAttendance.length}명)
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
                <TableHead>날짜</TableHead>
                <TableHead>출근 시간</TableHead>
                <TableHead>퇴근 시간</TableHead>
                <TableHead className="text-right">근무 시간</TableHead>
                <TableHead>상태</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAttendance.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.employeeId}</TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.department}</TableCell>
                  <TableCell>{item.date}</TableCell>
                  <TableCell>{item.checkIn}</TableCell>
                  <TableCell>{item.checkOut || '-'}</TableCell>
                  <TableCell className="text-right">
                    {item.workHours > 0 ? `${item.workHours}시간` : '-'}
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={item.status === '정상' ? 'outline' : 'outline'}
                      className={
                        item.status === '정상' 
                          ? 'border-green-500 text-green-700 dark:text-green-400'
                          : item.status === '지각'
                          ? 'border-yellow-500 text-yellow-700 dark:text-yellow-400'
                          : 'border-red-500 text-red-700 dark:text-red-400'
                      }
                    >
                      {item.status}
                    </Badge>
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
