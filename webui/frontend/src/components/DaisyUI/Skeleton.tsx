import React from 'react';

interface SkeletonProps {
  shape?: 'rectangle' | 'circle' | 'text';
  width?: string | number;
  height?: string | number;
  className?: string;
  lines?: number;
  animate?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({ shape = 'rectangle', width, height, className = '', lines = 1, animate = true }) => {
  const shapeClass = shape === 'circle' ? 'rounded-full' : 'rounded';
  const getSizeStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {};
    if (width) styles.width = typeof width === 'number' ? `${width}px` : width;
    if (height) styles.height = typeof height === 'number' ? `${height}px` : height;
    return styles;
  };

  const baseClasses = `skeleton ${shapeClass} ${animate ? '' : 'skeleton-static'} ${className}`;

  if (shape === 'text') {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, index) => (
          <div key={index} className={baseClasses} style={{ ...getSizeStyles(), height: height || '1rem', width: width || (index === lines - 1 && lines > 1 ? '66.67%' : '100%') }} aria-hidden="true" />
        ))}
      </div>
    );
  }

  return <div className={baseClasses} style={getSizeStyles()} aria-hidden="true" />;
};

export const SkeletonAvatar: React.FC<Omit<SkeletonProps, 'shape'>> = (props) => <Skeleton {...props} shape="circle" />;
export const SkeletonText: React.FC<Omit<SkeletonProps, 'shape'> & { lines?: number }> = (props) => <Skeleton {...props} shape="text" />;
export const SkeletonCard: React.FC<{ className?: string; animate?: boolean; showImage?: boolean; showActions?: boolean }> = ({
  className = '', animate = true, showImage = true, showActions = true,
}) => (
  <div className={`card bg-base-100 shadow-xl ${className}`}>
    {showImage && <figure className="px-4 pt-4"><Skeleton width="100%" height="8rem" animate={animate} className="rounded-xl" /></figure>}
    <div className="card-body">
      <SkeletonText lines={1} width="75%" animate={animate} className="mb-2 h-4" />
      <SkeletonText lines={3} animate={animate} className="mb-4 h-3" />
      {showActions && (
        <div className="card-actions justify-end">
          <Skeleton width="5rem" height="2.5rem" animate={animate} />
          <Skeleton width="6rem" height="2.5rem" animate={animate} />
        </div>
      )}
    </div>
  </div>
);

export const SkeletonTableLayout: React.FC<{ rows?: number; columns?: number; className?: string; animate?: boolean }> = ({
  rows = 5, columns = 4, className = '', animate = true,
}) => (
  <div className={`overflow-x-auto ${className}`}>
    <table className="table">
      <thead><tr>{Array.from({ length: columns }).map((_, i) => <th key={i}><Skeleton width="6rem" height="1rem" animate={animate} /></th>)}</tr></thead>
      <tbody>{Array.from({ length: rows }).map((_, rowIdx) => (
        <tr key={rowIdx}>{Array.from({ length: columns }).map((_, colIdx) => <td key={colIdx}><Skeleton width="8rem" height="1rem" animate={animate} /></td>)}</tr>
      ))}</tbody>
    </table>
  </div>
);

export const SkeletonStatsCards: React.FC<{ count?: number; className?: string; animate?: boolean }> = ({
  count = 4, className = '', animate = true,
}) => (
  <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 ${className}`}>
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="card bg-base-100 shadow-sm p-4">
        <Skeleton width="3rem" height="0.75rem" animate={animate} className="mb-2" />
        <Skeleton width="4rem" height="1.5rem" animate={animate} className="mb-1" />
        <Skeleton width="5rem" height="0.625rem" animate={animate} />
      </div>
    ))}
  </div>
);

export default Skeleton;
