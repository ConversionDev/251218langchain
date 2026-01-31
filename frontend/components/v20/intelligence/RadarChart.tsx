'use client';

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';

interface RadarChartData {
  subject: string;
  value: number;
  fullMark?: number;
}

interface RadarChartProps {
  data: RadarChartData[];
  employeeName?: string;
  modelName?: string;
}

export function RadarChartComponent({ data, employeeName, modelName }: RadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" />
        <PolarRadiusAxis angle={90} domain={[0, 100]} />
        {employeeName && (
          <Radar
            name={employeeName}
            dataKey="value"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
          />
        )}
        {modelName && (
          <Radar
            name={modelName}
            dataKey="modelValue"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.3}
          />
        )}
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );
}
