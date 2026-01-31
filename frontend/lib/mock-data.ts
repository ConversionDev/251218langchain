/**
 * Mock Data 통합 관리
 * 백엔드 API 연동 시 이 파일의 데이터를 실제 API 호출로 교체
 */

// ==================== Core HR Mock Data ====================
export const mockEmployees = [
  {
    id: 1,
    name: '홍길동',
    employeeId: 'EMP001',
    department: '개발팀',
    position: '시니어 개발자',
    status: '재직',
    email: 'hong@example.com',
    phone: '010-1234-5678',
    joinDate: '2020-01-15',
  },
  {
    id: 2,
    name: '김철수',
    employeeId: 'EMP002',
    department: '마케팅팀',
    position: '마케팅 매니저',
    status: '재직',
    email: 'kim@example.com',
    phone: '010-2345-6789',
    joinDate: '2019-03-20',
  },
  {
    id: 3,
    name: '이영희',
    employeeId: 'EMP003',
    department: '인사팀',
    position: 'HR 전문가',
    status: '재직',
    email: 'lee@example.com',
    phone: '010-3456-7890',
    joinDate: '2021-06-10',
  },
  {
    id: 4,
    name: '박민수',
    employeeId: 'EMP004',
    department: '개발팀',
    position: '주니어 개발자',
    status: '재직',
    email: 'park@example.com',
    phone: '010-4567-8901',
    joinDate: '2023-09-01',
  },
  {
    id: 5,
    name: '최지은',
    employeeId: 'EMP005',
    department: '디자인팀',
    position: 'UI/UX 디자이너',
    status: '재직',
    email: 'choi@example.com',
    phone: '010-5678-9012',
    joinDate: '2022-02-14',
  },
];

// ==================== Intelligence Mock Data ====================
export const mockAnalyzedEmployees = [
  {
    id: 1,
    name: '홍길동',
    employeeId: 'EMP001',
    department: '개발팀',
    position: '시니어 개발자',
    analyzedDate: '2024-01-15',
    successDnaMatch: 87.5,
    status: '완료',
    capabilities: {
      leadership: 85,
      collaboration: 90,
      creativity: 78,
      problemSolving: 92,
      communication: 88,
    },
    behaviorSummary: `홍길동 직원은 강한 기술적 역량과 협업 능력을 보유하고 있습니다. 특히 문제 해결 능력이 뛰어나며, 복잡한 기술적 도전 과제를 체계적으로 접근합니다.

리더십 측면에서는 팀 내 기술적 의사결정을 주도하며, 주니어 개발자들을 멘토링하는 데 적극적입니다. 협업 능력은 매우 높아서 크로스 펑셔널 팀과의 소통이 원활하며, 프로젝트 진행 시 다른 팀원들의 의견을 적극 수렴합니다.

창의성은 보통 수준이지만, 실용적인 솔루션을 찾는 데 강점이 있습니다. 커뮤니케이션 능력도 우수하여 기술적 내용을 비기술자에게도 명확하게 전달할 수 있습니다.`,
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
    capabilities: {
      leadership: 88,
      collaboration: 85,
      creativity: 92,
      problemSolving: 82,
      communication: 90,
    },
    behaviorSummary: `김철수 직원은 창의적인 마케팅 전략 수립 능력이 뛰어나며, 리더십과 커뮤니케이션 능력이 매우 우수합니다.`,
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
    capabilities: {
      leadership: 82,
      collaboration: 90,
      creativity: 68,
      problemSolving: 85,
      communication: 93,
    },
    behaviorSummary: `이영희 직원은 커뮤니케이션과 협업 능력이 매우 뛰어나며, 사람 중심의 문제 해결을 잘합니다.`,
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
    capabilities: {
      leadership: 70,
      collaboration: 88,
      creativity: 75,
      problemSolving: 90,
      communication: 82,
    },
    behaviorSummary: `박민수 직원은 문제 해결 능력이 뛰어나며, 협업 능력도 우수합니다.`,
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
    capabilities: {
      leadership: 92,
      collaboration: 88,
      creativity: 95,
      problemSolving: 85,
      communication: 90,
    },
    behaviorSummary: `최지은 직원은 창의성과 리더십이 매우 뛰어나며, 디자인 분야에서 탁월한 역량을 보여줍니다.`,
  },
];

export const mockHighPerformerModels = {
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

// ==================== Credential Mock Data ====================
export const mockVCs = [
  {
    id: 1,
    employeeName: '홍길동',
    employeeId: 'EMP001',
    credentialType: '학위 증명서',
    issuedDate: '2024-01-15',
    transactionHash: '0x12a3f4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3',
    status: 'verified',
    issuer: '서울대학교',
  },
  {
    id: 2,
    employeeName: '김철수',
    employeeId: 'EMP002',
    credentialType: '자격증',
    issuedDate: '2024-01-14',
    transactionHash: '0x23b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3',
    status: 'verified',
    issuer: '한국정보통신자격협회',
  },
  {
    id: 3,
    employeeName: '이영희',
    employeeId: 'EMP003',
    credentialType: '경력 증명서',
    issuedDate: '2024-01-13',
    transactionHash: '0x34c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4',
    status: 'pending',
    issuer: '이전 회사',
  },
  {
    id: 4,
    employeeName: '박민수',
    employeeId: 'EMP004',
    credentialType: '학위 증명서',
    issuedDate: '2024-01-12',
    transactionHash: '0x45d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5',
    status: 'verified',
    issuer: 'KAIST',
  },
  {
    id: 5,
    employeeName: '최지은',
    employeeId: 'EMP005',
    credentialType: '자격증',
    issuedDate: '2024-01-11',
    transactionHash: '0x56e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
    status: 'verified',
    issuer: 'Adobe',
  },
];

// ==================== Performance Mock Data ====================
export const mockPerformanceRankings = [
  {
    id: 1,
    name: '홍길동',
    employeeId: 'EMP001',
    department: '개발팀',
    coreScore: 85, // 정량 지표 (40%)
    aiDnaScore: 87.5, // AI DNA 점수 (60%)
    totalScore: 86.5, // 가중 평균
    rank: 1,
    capabilities: {
      leadership: 85,
      collaboration: 90,
      creativity: 78,
      problemSolving: 92,
      communication: 88,
    },
  },
  {
    id: 2,
    name: '김철수',
    employeeId: 'EMP002',
    department: '마케팅팀',
    coreScore: 88,
    aiDnaScore: 92.3,
    totalScore: 90.6,
    rank: 2,
    capabilities: {
      leadership: 88,
      collaboration: 85,
      creativity: 92,
      problemSolving: 82,
      communication: 90,
    },
  },
  {
    id: 3,
    name: '이영희',
    employeeId: 'EMP003',
    department: '인사팀',
    coreScore: 82,
    aiDnaScore: 78.9,
    totalScore: 80.1,
    rank: 3,
    capabilities: {
      leadership: 82,
      collaboration: 90,
      creativity: 68,
      problemSolving: 85,
      communication: 93,
    },
  },
  {
    id: 4,
    name: '박민수',
    employeeId: 'EMP004',
    department: '개발팀',
    coreScore: 75,
    aiDnaScore: 85.2,
    totalScore: 81.1,
    rank: 4,
    capabilities: {
      leadership: 70,
      collaboration: 88,
      creativity: 75,
      problemSolving: 90,
      communication: 82,
    },
  },
  {
    id: 5,
    name: '최지은',
    employeeId: 'EMP005',
    department: '디자인팀',
    coreScore: 90,
    aiDnaScore: 91.7,
    totalScore: 91.0,
    rank: 5,
    capabilities: {
      leadership: 92,
      collaboration: 88,
      creativity: 95,
      problemSolving: 85,
      communication: 90,
    },
  },
].sort((a, b) => b.totalScore - a.totalScore)
  .map((item, index) => ({ ...item, rank: index + 1 }));

export const mockPerformanceTrend = [
  { month: '2023-07', coreScore: 80, aiDnaScore: 82, totalScore: 81.2 },
  { month: '2023-08', coreScore: 82, aiDnaScore: 84, totalScore: 83.2 },
  { month: '2023-09', coreScore: 84, aiDnaScore: 85, totalScore: 84.6 },
  { month: '2023-10', coreScore: 83, aiDnaScore: 86, totalScore: 84.8 },
  { month: '2023-11', coreScore: 85, aiDnaScore: 87, totalScore: 86.2 },
  { month: '2023-12', coreScore: 86, aiDnaScore: 87.5, totalScore: 86.9 },
  { month: '2024-01', coreScore: 85, aiDnaScore: 87.5, totalScore: 86.5 },
];

// ==================== Status Badge Types ====================
export type StatusType = 'pending' | 'success' | 'failed' | 'analyzing' | 'verified';

export const statusBadgeConfig: Record<StatusType, { label: string; variant: 'outline' | 'default'; className: string }> = {
  pending: {
    label: '대기 중',
    variant: 'outline',
    className: 'border-yellow-500 text-yellow-700 dark:text-yellow-400',
  },
  success: {
    label: '성공',
    variant: 'outline',
    className: 'border-green-500 text-green-700 dark:text-green-400',
  },
  failed: {
    label: '실패',
    variant: 'outline',
    className: 'border-red-500 text-red-700 dark:text-red-400',
  },
  analyzing: {
    label: '분석 중',
    variant: 'outline',
    className: 'border-blue-500 text-blue-700 dark:text-blue-400',
  },
  verified: {
    label: '검증 완료',
    variant: 'outline',
    className: 'border-green-500 text-green-700 dark:text-green-400',
  },
};
