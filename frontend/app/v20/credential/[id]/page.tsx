'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, ArrowLeft, CheckCircle2, Copy, ExternalLink } from 'lucide-react';
import Link from 'next/link';

// Mock 데이터: VC 상세 정보 및 DID 문서
const mockVCDetail = {
  id: 1,
  employeeName: '홍길동',
  employeeId: 'EMP001',
  credentialType: '학위 증명서',
  issuedDate: '2024-01-15',
  transactionHash: '0x12a3f4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3',
  status: 'verified',
  issuer: '서울대학교',
  // DID 문서
  didDocument: {
    '@context': ['https://www.w3.org/ns/did/v1'],
    id: 'did:example:123456789abcdefghi',
    verificationMethod: [
      {
        id: 'did:example:123456789abcdefghi#keys-1',
        type: 'EcdsaSecp256k1VerificationKey2019',
        controller: 'did:example:123456789abcdefghi',
        publicKeyHex: '02b97c30de767f084ce3080168ee293053ba33b235d7116a3263d29f1450936b71',
      },
    ],
    authentication: ['did:example:123456789abcdefghi#keys-1'],
    service: [
      {
        id: 'did:example:123456789abcdefghi#vcs',
        type: 'VerifiableCredentialService',
        serviceEndpoint: 'https://vc.example.com/credentials',
      },
    ],
  },
  // VC 내용
  credential: {
    '@context': ['https://www.w3.org/2018/credentials/v1'],
    type: ['VerifiableCredential', 'DegreeCredential'],
    issuer: {
      id: 'did:example:issuer',
      name: '서울대학교',
    },
    issuanceDate: '2024-01-15T00:00:00Z',
    credentialSubject: {
      id: 'did:example:123456789abcdefghi',
      name: '홍길동',
      degree: {
        type: 'Bachelor',
        name: '컴퓨터공학',
        institution: '서울대학교',
      },
    },
    proof: {
      type: 'EcdsaSecp256k1Signature2019',
      created: '2024-01-15T00:00:00Z',
      proofPurpose: 'assertionMethod',
      verificationMethod: 'did:example:123456789abcdefghi#keys-1',
      jws: 'eyJhbGciOiJFUzI1NkstUiIsInI2NCI6IkEyNTZHS0EiLCJraWQiOiJkaWQ6ZXhhbXBsZToxMjM0NTY3ODlhYmNkZWZnaGkja2V5cy0xIn0...',
    },
  },
};

export default function CredentialDetailPage({ params }: { params: { id: string } }) {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" asChild>
            <Link href="/v20/credential">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              VC 상세 정보
            </h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              {mockVCDetail.employeeName} ({mockVCDetail.employeeId}) - {mockVCDetail.credentialType}
            </p>
          </div>
        </div>
        {mockVCDetail.status === 'verified' && (
          <Badge variant="outline" className="border-green-500 text-green-700 dark:text-green-400 text-lg px-4 py-2">
            <CheckCircle2 className="mr-2 h-4 w-4" />
            Verified
          </Badge>
        )}
      </div>

      {/* 기본 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>증명서 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">사원명</p>
              <p className="text-base font-semibold">{mockVCDetail.employeeName}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">사번</p>
              <p className="text-base font-semibold">{mockVCDetail.employeeId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">증명 종류</p>
              <p className="text-base font-semibold">{mockVCDetail.credentialType}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">발행 기관</p>
              <p className="text-base font-semibold">{mockVCDetail.issuer}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">발행 일시</p>
              <p className="text-base font-semibold">{mockVCDetail.issuedDate}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">트랜잭션 해시</p>
              <div className="flex items-center gap-2">
                <code className="text-xs font-mono text-slate-600 dark:text-slate-400">
                  {mockVCDetail.transactionHash}
                </code>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => copyToClipboard(mockVCDetail.transactionHash)}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* DID 문서 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>DID 문서</CardTitle>
              <CardDescription>탈중앙화 식별자(DID) 정보</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(JSON.stringify(mockVCDetail.didDocument, null, 2))}
            >
              <Copy className="mr-2 h-4 w-4" />
              복사
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
            <pre className="overflow-x-auto text-xs font-mono text-slate-700 dark:text-slate-300">
              {JSON.stringify(mockVCDetail.didDocument, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* Verifiable Credential */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Verifiable Credential</CardTitle>
              <CardDescription>검증 가능한 증명서 전체 내용</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(JSON.stringify(mockVCDetail.credential, null, 2))}
            >
              <Copy className="mr-2 h-4 w-4" />
              복사
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
            <pre className="overflow-x-auto text-xs font-mono text-slate-700 dark:text-slate-300">
              {JSON.stringify(mockVCDetail.credential, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* 블록체인 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>블록체인 정보</CardTitle>
          <CardDescription>트랜잭션 상세 정보</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-slate-200 p-4 dark:border-slate-800">
              <div>
                <p className="text-sm font-medium">네트워크</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">Ethereum Mainnet</p>
              </div>
              <Badge variant="outline">활성</Badge>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-slate-200 p-4 dark:border-slate-800">
              <div>
                <p className="text-sm font-medium">블록 번호</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">18,234,567</p>
              </div>
              <Button variant="outline" size="sm" asChild>
                <a
                  href={`https://etherscan.io/tx/${mockVCDetail.transactionHash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Etherscan에서 보기
                </a>
              </Button>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-slate-200 p-4 dark:border-slate-800">
              <div>
                <p className="text-sm font-medium">확인 수</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">12 confirmations</p>
              </div>
              <Badge variant="outline" className="border-green-500 text-green-700 dark:text-green-400">
                <CheckCircle2 className="mr-1 h-3 w-3" />
                검증 완료
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
