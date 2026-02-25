"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("system");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">설정</h1>
        <p className="mt-1 text-muted-foreground">
          시스템 설정 및 환경설정을 관리합니다.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="system">시스템 설정</TabsTrigger>
          <TabsTrigger value="env">환경설정</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="mt-6">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold leading-none tracking-tight">시스템 설정</h2>
              <p className="text-sm text-muted-foreground">
                애플리케이션 동작, API 연결, 알림 등 시스템 전반 설정
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="api-base">API 기본 URL</Label>
                <Input
                  id="api-base"
                  placeholder="https://api.example.com"
                  className="max-w-md"
                />
                <p className="text-xs text-muted-foreground">
                  백엔드 API 서버 주소 (환경 변수로 override 가능)
                </p>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <div>
                  <Label htmlFor="rag-default">RAG 검색 기본 사용</Label>
                  <p className="text-xs text-muted-foreground">
                    AI 질의 시 RAG 검색을 기본으로 사용합니다
                  </p>
                </div>
                <input type="checkbox" id="rag-default" defaultChecked className="h-4 w-4 rounded border-input" />
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <div>
                  <Label htmlFor="stream-default">스트리밍 응답</Label>
                  <p className="text-xs text-muted-foreground">
                    AI 응답을 스트리밍으로 표시합니다
                  </p>
                </div>
                <input type="checkbox" id="stream-default" defaultChecked className="h-4 w-4 rounded border-input" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="env" className="mt-6">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold leading-none tracking-tight">환경설정</h2>
              <p className="text-sm text-muted-foreground">
                테마, 로케일, 표시 옵션 등 사용 환경 설정
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>테마</Label>
                <p className="text-xs text-muted-foreground">
                  상단 헤더의 다크 모드 토글로 전환할 수 있습니다.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="date-format">날짜 표시 형식</Label>
                <Input
                  id="date-format"
                  placeholder="YYYY-MM-DD"
                  className="max-w-xs"
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <div>
                  <Label htmlFor="compact-view">간편 보기</Label>
                  <p className="text-xs text-muted-foreground">
                    목록·테이블을 더 조밀하게 표시합니다
                  </p>
                </div>
                <input type="checkbox" id="compact-view" className="h-4 w-4 rounded border-input" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
