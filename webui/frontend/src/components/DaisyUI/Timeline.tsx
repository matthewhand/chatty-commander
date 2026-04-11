import React, { memo } from 'react';

export interface TimelineItem {
  id?: string | number;
  title: string;
  subtitle?: string;
  content?: React.ReactNode;
  description?: string; // Legacy support
  time?: string; // Legacy support
  icon?: React.ReactNode;
  status?: 'success' | 'error' | 'pending' | 'info' | 'warning';
  color?: 'primary' | 'secondary' | 'accent' | 'success' | 'error' | 'info' | 'warning' | 'neutral';
  side?: 'start' | 'end';
}

export interface TimelineProps {
  items: TimelineItem[];
  vertical?: boolean;
  className?: string;
}

const statusColorMap: Record<string, string> = {
  success: 'bg-success',
  error: 'bg-error',
  pending: 'bg-base-300',
  info: 'bg-info',
  warning: 'bg-warning',
};

export const Timeline = memo(({ items, vertical = true, className = '' }: TimelineProps) => {
  return (
    <ul className={`timeline ${vertical ? 'timeline-vertical' : ''} ${className}`.trim()}>
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;
        const dotColor = item.color ? `bg-${item.color}` : (item.status ? statusColorMap[item.status] || '' : 'bg-primary');

        const renderBox = (
          <>
            <div className="font-semibold">{item.title}</div>
            {(item.subtitle || item.time) && <div className="text-xs opacity-50 mb-1">{item.subtitle || item.time}</div>}
            {(item.content || item.description) && <div className="text-sm opacity-70">{item.content || item.description}</div>}
          </>
        );

        return (
          <li key={item.id || idx}>
            {idx > 0 && <hr className={item.color === 'primary' || item.status === 'success' || item.status === 'info' ? 'bg-primary' : ''} />}
            {(item.side === 'start' || (!item.side && idx % 2 === 0)) && (
              <div className="timeline-start timeline-box">
                {renderBox}
              </div>
            )}
            <div className="timeline-middle">
              {item.icon || (
                <div className={`w-3 h-3 rounded-full ${dotColor}`} />
              )}
            </div>
            {(item.side === 'end' || (!item.side && idx % 2 !== 0)) && (
              <div className="timeline-end timeline-box">
                {renderBox}
              </div>
            )}
            {!isLast && <hr className={item.color === 'primary' || item.status === 'success' || item.status === 'info' ? 'bg-primary' : ''} />}
          </li>
        );
      })}
    </ul>
  );
});

Timeline.displayName = 'Timeline';

export default Timeline;
