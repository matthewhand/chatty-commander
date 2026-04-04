import React, { memo } from 'react';

export interface DiffProps {
  oldContent: React.ReactNode;
  newContent: React.ReactNode;
  oldLabel?: string;
  newLabel?: string;
  className?: string;
}

export const Diff = memo(({ oldContent, newContent, oldLabel, newLabel, className = '' }: DiffProps) => {
  return (
    <div className={`diff aspect-[16/9] ${className}`.trim()}>
      <div className="diff-item-1">
        {oldLabel && (
          <div className="absolute top-2 left-2 badge badge-neutral badge-sm z-10">{oldLabel}</div>
        )}
        <div className="bg-base-200 text-base-content grid place-content-center text-9xl font-black">
          {oldContent}
        </div>
      </div>
      <div className="diff-item-2">
        {newLabel && (
          <div className="absolute top-2 left-2 badge badge-neutral badge-sm z-10">{newLabel}</div>
        )}
        <div className="bg-base-300 text-base-content grid place-content-center text-9xl font-black">
          {newContent}
        </div>
      </div>
      <div className="diff-resizer" />
    </div>
  );
});

Diff.displayName = 'Diff';

export default Diff;
