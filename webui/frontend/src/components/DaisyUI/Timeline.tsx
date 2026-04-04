import React, { memo } from 'react';

export interface TimelineItem {
  title: string;
  description?: string;
  time?: string;
  icon?: React.ReactNode;
  status?: 'success' | 'error' | 'pending' | 'info' | 'warning';
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
        const dotColor = item.status ? statusColorMap[item.status] || '' : 'bg-primary';

        return (
          <li key={idx}>
            {idx > 0 && <hr className={item.status === 'success' || item.status === 'info' ? 'bg-primary' : ''} />}
            {(item.side === 'start' || (!item.side && idx % 2 === 0)) && (
              <div className="timeline-start timeline-box">
                <div className="font-semibold">{item.title}</div>
                {item.description && <div className="text-sm opacity-70">{item.description}</div>}
                {item.time && <div className="text-xs opacity-50">{item.time}</div>}
              </div>
            )}
            <div className="timeline-middle">
              {item.icon || (
                <div className={`w-3 h-3 rounded-full ${dotColor}`} />
              )}
            </div>
            {(item.side === 'end' || (!item.side && idx % 2 !== 0)) && (
              <div className="timeline-end timeline-box">
                <div className="font-semibold">{item.title}</div>
                {item.description && <div className="text-sm opacity-70">{item.description}</div>}
                {item.time && <div className="text-xs opacity-50">{item.time}</div>}
              </div>
            )}
            {!isLast && <hr className={item.status === 'success' || item.status === 'info' ? 'bg-primary' : ''} />}
          </li>
        );
      })}
    </ul>
  );
});

Timeline.displayName = 'Timeline';

export default Timeline;
