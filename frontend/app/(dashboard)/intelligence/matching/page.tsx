'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { BrainCircuit, Search, TrendingUp, Users, Target } from 'lucide-react';
import { RadarChartComponent } from '@/components/v20/intelligence/RadarChart';

// Mock 데이터: 부서별 고성과자 모델
const mockHighPerformerModels = {
  '개발팀': {
    department: '개발팀',
    modelName: '개발팀 고성과자 모델',
    capabilities: {
      leadership: 75,
      collaboration: 95,
      creativity: 85,
      problemSolving: 98,
      communication: 80,
    },
    description: '개발팀 고성과자들은 문제 해결 능력과 협업 능력이 매우 뛰어나며, 기술적 도전 과제를 즐깁니다.',
  },
  '마케팅팀': {
    department: '마케팅팀',
    modelName: '마케팅팀 고성과자 모델',
    capabilities: {
      leadership: 90,
      collaboration: 88,
      creativity: 95,
      problemSolving: 85,
      communication: 92,
    },
    description: '마케팅팀 고성과자들은 창의성과 커뮤니케이션 능력이 뛰어나며, 리더십도 강합니다.',
  },
  '인사팀': {
    department: '인사팀',
    modelName: '인사팀 고성과자 모델',
    capabilities: {
      leadership: 85,
      collaboration: 92,
      creativity: 70,
      problemSolving: 88,
      communication: 95,
    },
    description: '인사팀 고성과자들은 커뮤니케이션과 협업 능력이 매우 뛰어나며, 사람 중심의 문제 해결을 잘합니다.',
  },
};

// Mock 데이터: 직원 리스트
const mockEmployees = [
  {
    id: 1,
    name: '홍길동',
    employeeId: 'EMP001',
    department: '개발팀',
    capabilities: {
      leadership: 85,
      collaboration: 90,
      creativity: 78,
      problemSolving: 92,
      communication: 88,
    },
    vectorSimilarity: 0.875,
  },
  {
    id: 2,
    name: '김철수',
    employeeId: 'EMP002',
    department: '마케팅팀',
    capabilities: {
      leadership: 88,
      collaboration: 85,
      creativity: 92,
      problemSolving: 82,
      communication: 90,
    },
    vectorSimilarity: 0.923,
  },
  {
    id: 3,
    name: '이영희',
    employeeId: 'EMP003',
    department: '인사팀',
    capabilities: {
      leadership: 82,
      collaboration: 90,
      creativity: 68,
      problemSolving: 85,
      communication: 93,
    },
    vectorSimilarity: 0.789,
  },
];

export default function MatchingPage() {
  const [selectedDepartment, setSelectedDepartment] = useState<string>('개발팀');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>('EMP001');
  const [searchQuery, setSearchQuery] = useState('');

  const selectedModel = mockHighPerformerModels[selectedDepartment as keyof typeof mockHighPerformerModels];
  const selectedEmployee = mockEmployees.find(emp => emp.employeeId === selectedEmployeeId);

  // Radar Chart 데이터 생성 (직원 + 모델 비교)
  const radarData = selectedEmployee
    ? [
        {
          subject: '리더십',
          value: selectedEmployee.capabilities.leadership,
          modelValue: selectedModel.capabilities.leadership,
        },
        {
          subject: '협업 능력',
          value: selectedEmployee.capabilities.collaboration,
          modelValue: selectedModel.capabilities.collaboration,
        },
        {
          subject: '창의성',
          value: selectedEmployee.capabilities.creativity,
          modelValue: selectedModel.capabilities.creativity,
        },
        {
          subject: '문제 해결',
          value: selectedEmployee.capabilities.problemSolving,
          modelValue: selectedModel.capabilities.problemSolving,
        },
        {
          subject: '커뮤니케이션',
          value: selectedEmployee.capabilities.communication,
          modelValue: selectedModel.capabilities.communication,
        },
      ]
    : [];

  const filteredEmployees = mockEmployees.filter(
    (emp) =>
      emp.department === selectedDepartment &&
      (emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        emp.employeeId.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.9) return 'text-green-600 dark:text-green-400';
    if (similarity >= 0.8) return 'text-blue-600 dark:text-blue-400';
    return 'text-yellow-600 dark:text-yellow-400';
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          매칭 툴
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          부서별 고성과자 모델과 직원의 벡터 유사도 비교 및 시각화
        </p>
      </div>

      {/* 부서 선택 및 직원 검색 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>부서 선택</CardTitle>
            <CardDescription>고성과자 모델을 선택하세요</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.keys(mockHighPerformerModels).map((dept) => (
                <Button
                  key={dept}
                  variant={selectedDepartment === dept ? 'default' : 'outline'}
                  className="w-full justify-start"
                  onClick={() => {
                    setSelectedDepartment(dept);
                    // 부서 변경 시 해당 부서의 첫 번째 직원 선택
                    const firstEmployee = mockEmployees.find(emp => emp.department === dept);
                    if (firstEmployee) {
                      setSelectedEmployeeId(firstEmployee.employeeId);
                    }
                  }}
                >
                  <Target className="mr-2 h-4 w-4" />
                  {dept} 고성과자 모델
                </Button>
              ))}
            </div>
            {selectedModel && (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-sm font-medium mb-2">{selectedModel.modelName}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {selectedModel.description}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>직원 검색</CardTitle>
            <CardDescription>비교할 직원을 선택하세요</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  placeholder="이름, 사번으로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {filteredEmployees.map((emp) => (
                  <button
                    key={emp.id}
                    onClick={() => setSelectedEmployeeId(emp.employeeId)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      selectedEmployeeId === emp.employeeId
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900'
                        : 'border-slate-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{emp.name}</p>
                        <p className="text-xs text-slate-600 dark:text-slate-400">
                          {emp.employeeId}
                        </p>
                      </div>
                      <Badge variant="outline">
                        유사도: {(emp.vectorSimilarity * 100).toFixed(1)}%
                      </Badge>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 벡터 유사도 비교 시각화 */}
      {selectedEmployee && selectedModel && (
        <>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>벡터 유사도 비교</CardTitle>
                  <CardDescription>
                    {selectedEmployee.name} vs {selectedModel.modelName}
                  </CardDescription>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-600 dark:text-slate-400">벡터 유사도</p>
                  <p className={`text-3xl font-bold ${getSimilarityColor(selectedEmployee.vectorSimilarity)}`}>
                    {(selectedEmployee.vectorSimilarity * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <RadarChartComponent
                data={radarData}
                employeeName={selectedEmployee.name}
                modelName={selectedModel.modelName}
              />
            </CardContent>
          </Card>

          {/* 상세 비교 */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>직원 역량</CardTitle>
                <CardDescription>{selectedEmployee.name} ({selectedEmployee.employeeId})</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {radarData.map((item) => (
                    <div key={item.subject} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{item.subject}</span>
                        <span className="text-sm font-semibold">{item.value}점</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-800">
                        <div
                          className="h-2 rounded-full bg-blue-500"
                          style={{ width: `${item.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>고성과자 모델 역량</CardTitle>
                <CardDescription>{selectedModel.modelName}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {radarData.map((item) => (
                    <div key={item.subject} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{item.subject}</span>
                        <span className="text-sm font-semibold">{item.modelValue}점</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-800">
                        <div
                          className="h-2 rounded-full bg-green-500"
                          style={{ width: `${item.modelValue}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 차이 분석 */}
          <Card>
            <CardHeader>
              <CardTitle>차이 분석</CardTitle>
              <CardDescription>직원과 고성과자 모델 간 역량 차이</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {radarData.map((item) => {
                  const diff = item.value - item.modelValue;
                  const absDiff = Math.abs(diff);
                  return (
                    <div key={item.subject} className="flex items-center justify-between rounded-lg border border-slate-200 p-3 dark:border-slate-800">
                      <span className="text-sm font-medium">{item.subject}</span>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-xs text-slate-600 dark:text-slate-400">차이</p>
                          <p className={`text-sm font-semibold ${diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                            {diff > 0 ? '+' : ''}{diff.toFixed(1)}점
                          </p>
                        </div>
                        <div className="h-2 w-24 rounded-full bg-slate-200 dark:bg-slate-800">
                          <div
                            className={`h-2 rounded-full ${diff > 0 ? 'bg-green-500' : diff < 0 ? 'bg-red-500' : 'bg-slate-400'}`}
                            style={{ width: `${(absDiff / 100) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
