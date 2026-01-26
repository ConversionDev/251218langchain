"use client";

import { Card, CardContent } from "@/components/ui/card";

interface DashboardCardProps {
  title: string;
  value: string | number;
  icon: string;
  loading?: boolean;
}

export default function DashboardCard({
  title,
  value,
  icon,
  loading = false,
}: DashboardCardProps) {
  return (
    <Card className="bg-white border border-gray-200 rounded-xl p-5 flex flex-col gap-3 transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5">
      <div className="text-3xl leading-none">{icon}</div>
      <CardContent className="flex flex-col gap-1 p-0">
        <h3 className="text-sm text-gray-500 font-medium">{title}</h3>
        <p className="text-2xl font-bold text-gray-800 leading-[1.2]">
          {loading ? (
            <span className="inline-block bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 bg-[length:200%_100%] animate-loading rounded min-w-[60px] h-6"></span>
          ) : (
            value
          )}
        </p>
      </CardContent>
    </Card>
  );
}
