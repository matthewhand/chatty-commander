import React, { memo, useState, useEffect, useCallback, useRef } from 'react';

export interface CountdownProps {
  targetDate?: Date | string;
  seconds?: number;
  onComplete?: () => void;
  className?: string;
  showLabels?: boolean;
}

interface TimeLeft {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

function computeTimeLeft(targetDate?: Date | string, initialSeconds?: number, startTime?: number): TimeLeft {
  if (targetDate) {
    const target = typeof targetDate === 'string' ? new Date(targetDate) : targetDate;
    const diff = Math.max(0, Math.floor((target.getTime() - Date.now()) / 1000));
    return {
      days: Math.floor(diff / 86400),
      hours: Math.floor((diff % 86400) / 3600),
      minutes: Math.floor((diff % 3600) / 60),
      seconds: diff % 60,
    };
  }

  if (initialSeconds !== undefined && startTime !== undefined) {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const remaining = Math.max(0, initialSeconds - elapsed);
    return {
      days: Math.floor(remaining / 86400),
      hours: Math.floor((remaining % 86400) / 3600),
      minutes: Math.floor((remaining % 3600) / 60),
      seconds: remaining % 60,
    };
  }

  return { days: 0, hours: 0, minutes: 0, seconds: 0 };
}

export const Countdown = memo(({ targetDate, seconds: initialSeconds, onComplete, className = '', showLabels = true }: CountdownProps) => {
  const startTimeRef = useRef(Date.now());
  const completedRef = useRef(false);
  const [timeLeft, setTimeLeft] = useState<TimeLeft>(() =>
    computeTimeLeft(targetDate, initialSeconds, startTimeRef.current)
  );

  const tick = useCallback(() => {
    const tl = computeTimeLeft(targetDate, initialSeconds, startTimeRef.current);
    setTimeLeft(tl);
    if (tl.days === 0 && tl.hours === 0 && tl.minutes === 0 && tl.seconds === 0 && !completedRef.current) {
      completedRef.current = true;
      onComplete?.();
    }
  }, [targetDate, initialSeconds, onComplete]);

  useEffect(() => {
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [tick]);

  const segments: { value: number; label: string }[] = [];
  if (timeLeft.days > 0) segments.push({ value: timeLeft.days, label: 'days' });
  segments.push({ value: timeLeft.hours, label: 'hours' });
  segments.push({ value: timeLeft.minutes, label: 'min' });
  segments.push({ value: timeLeft.seconds, label: 'sec' });

  return (
    <div className={`flex gap-5 ${className}`.trim()}>
      {segments.map((seg) => (
        <div key={seg.label} className="flex flex-col items-center">
          <span className="countdown font-mono text-4xl">
            <span style={{ '--value': seg.value } as React.CSSProperties} aria-label={`${seg.value} ${seg.label}`} />
          </span>
          {showLabels && <span className="text-xs opacity-60">{seg.label}</span>}
        </div>
      ))}
    </div>
  );
});

Countdown.displayName = 'Countdown';

export default Countdown;
