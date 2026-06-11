import React from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export interface PerfMetric {
  time: string;
  cpu: number;
  memory: number;
}

const CustomTooltip = React.memo(({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-base-300 border border-base-content/20 p-3 rounded-lg shadow-xl text-xs">
        <p className="font-mono mb-2 text-base-content/60">{label}</p>
        {payload.map((entry: any) => (
          <div key={entry.name} className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.stroke }} />
            <span className="font-semibold" style={{ color: entry.stroke }}>
              {entry.name}: {entry.value.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
});

interface PerformanceChartProps {
  history: PerfMetric[];
}

const PerformanceChart = React.memo(({ history }: PerformanceChartProps) => {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={history}>
        <defs>
          <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3abff8" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#3abff8" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#fbbd23" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#fbbd23" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
        <XAxis dataKey="time" hide />
        <YAxis
          domain={[0, 100]}
          tickFormatter={(value) => `${value}%`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="cpu"
          stroke="#3abff8"
          fillOpacity={1}
          fill="url(#colorCpu)"
          name="CPU"
          isAnimationActive={false}
        />
        <Area
          type="monotone"
          dataKey="memory"
          stroke="#fbbd23"
          fillOpacity={1}
          fill="url(#colorMem)"
          name="Memory"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
});

export default PerformanceChart;
