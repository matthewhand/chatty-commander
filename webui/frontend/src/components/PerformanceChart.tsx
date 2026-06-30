import React from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

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

// Telemetry arrives roughly every 5s and the chart retains the last ~20 points,
// so the visible window is approximately the last couple of minutes.
const WINDOW_SECONDS = 20 * 5;

function formatWindowCaption(seconds: number): string {
  if (seconds < 60) return `last ${seconds}s`;
  const minutes = Math.round(seconds / 60);
  return `last ${minutes} min`;
}

const PerformanceChart = React.memo(({ history }: PerformanceChartProps) => {
  // Show a sparse set of X-axis time ticks: only the first, middle and last
  // sample so the axis stays legible instead of crammed with every timestamp.
  const ticks = React.useMemo(() => {
    if (history.length === 0) return [] as string[];
    const idxs = [0, Math.floor((history.length - 1) / 2), history.length - 1];
    return Array.from(new Set(idxs.map((i) => history[i]?.time))).filter(
      (t): t is string => Boolean(t),
    );
  }, [history]);

  return (
    <div className="flex h-full w-full flex-col">
      <ResponsiveContainer width="100%" height="100%" minHeight={0} minWidth={0}>
        <AreaChart data={history} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
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
          <XAxis
            dataKey="time"
            ticks={ticks}
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
            minTickGap={20}
          />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend verticalAlign="top" height={24} iconType="plainline" />
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
      <p className="mt-1 text-center text-[10px] text-base-content/50">
        {formatWindowCaption(WINDOW_SECONDS)}
      </p>
    </div>
  );
});

export default PerformanceChart;
