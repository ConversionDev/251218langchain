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
import { ShieldCheck, CheckCircle2, Search, Eye, Loader2, Copy, ExternalLink } from 'lucide-react';
import Link from 'next/link';

// Mock 데이터: 발행된 VC 리스트
const mockVCs = [
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

export default function CredentialPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [verifyingId, setVerifyingId] = useState<number | null>(null);

  const filteredVCs = mockVCs.filter(
    (vc) =>
      vc.employeeName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      vc.employeeId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      vc.credentialType.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleVerify = async (id: number) => {
    setVerifyingId(id);
    // 시뮬레이션: 2초 후 완료
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setVerifyingId(null);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const truncateHash = (hash: string) => {
    return `${hash.slice(0, 10)}...${hash.slice(-8)}`;
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Verified Credentials
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            블록체인 기반 검증 가능한 증명서 관리 시스템
          </p>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 발행 VC</CardTitle>
            <ShieldCheck className="h-4 w-4 text-slate-600 dark:text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockVCs.length}</div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              발행된 증명서
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">검증 완료</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {mockVCs.filter((vc) => vc.status === 'verified').length}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              검증된 증명서
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">대기 중</CardTitle>
            <ShieldCheck className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {mockVCs.filter((vc) => vc.status === 'pending').length}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              검증 대기 중
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">블록체인 네트워크</CardTitle>
            <ShieldCheck className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              Ethereum
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              메인넷
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
              placeholder="사원명, 사번, 증명 종류로 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-10 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
        </CardContent>
      </Card>

      {/* VC 리스트 테이블 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>발행된 증명서 목록</CardTitle>
              <CardDescription>
                블록체인에 저장된 검증 가능한 증명서 목록
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>사원명</TableHead>
                <TableHead>증명 종류</TableHead>
                <TableHead>발행 기관</TableHead>
                <TableHead>발행 일시</TableHead>
                <TableHead>트랜잭션 해시</TableHead>
                <TableHead>상태</TableHead>
                <TableHead className="text-right">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredVCs.map((vc) => (
                <TableRow key={vc.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {vc.employeeName}
                      {vc.status === 'verified' && (
                        <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                      )}
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {vc.employeeId}
                    </p>
                  </TableCell>
                  <TableCell>{vc.credentialType}</TableCell>
                  <TableCell>{vc.issuer}</TableCell>
                  <TableCell>{vc.issuedDate}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <code className="text-xs font-mono text-slate-600 dark:text-slate-400">
                        {truncateHash(vc.transactionHash)}
                      </code>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => copyToClipboard(vc.transactionHash)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                  <TableCell>
                    {vc.status === 'verified' ? (
                      <Badge variant="outline" className="border-green-500 text-green-700 dark:text-green-400">
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        Verified
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="border-yellow-500 text-yellow-700 dark:text-yellow-400">
                        Pending
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleVerify(vc.id)}
                        disabled={verifyingId === vc.id}
                      >
                        {verifyingId === vc.id ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            검증 중...
                          </>
                        ) : (
                          <>
                            <ShieldCheck className="mr-2 h-4 w-4" />
                            Verify Integrity
                          </>
                        )}
                      </Button>
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/credential/${vc.id}`}>
                          <Eye className="h-4 w-4" />
                        </Link>
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 검증 중 로딩 바 (애니메이션) */}
      {verifyingId !== null && (
        <Card className="border-blue-500 bg-blue-50 dark:bg-blue-900">
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-blue-600 dark:text-blue-400" />
                <p className="font-medium text-blue-900 dark:text-blue-100">
                  데이터 무결성 검증 중...
                </p>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-blue-200 dark:bg-blue-800">
                <div className="h-full w-full animate-[loading_2s_ease-in-out_infinite] bg-blue-600 dark:bg-blue-400" />
              </div>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                블록체인에서 트랜잭션 해시를 검증하고 있습니다...
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
