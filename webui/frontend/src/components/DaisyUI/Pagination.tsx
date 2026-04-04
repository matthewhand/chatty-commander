import React, { memo, useMemo } from 'react';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
}

function getPageNumbers(current: number, total: number): (number | 'ellipsis')[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | 'ellipsis')[] = [1];

  if (current > 3) {
    pages.push('ellipsis');
  }

  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 2) {
    pages.push('ellipsis');
  }

  pages.push(total);
  return pages;
}

export const Pagination = memo(({ currentPage, totalPages, onPageChange, size = 'md', className = '' }: PaginationProps) => {
  const sizeClass = size !== 'md' ? `btn-${size}` : '';
  const pages = useMemo(() => getPageNumbers(currentPage, totalPages), [currentPage, totalPages]);

  if (totalPages <= 1) return null;

  return (
    <div className={`join ${className}`.trim()}>
      <button
        className={`join-item btn ${sizeClass}`.trim()}
        disabled={currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
        aria-label="Previous page"
      >
        «
      </button>
      {pages.map((page, idx) =>
        page === 'ellipsis' ? (
          <button key={`ellipsis-${idx}`} className={`join-item btn btn-disabled ${sizeClass}`.trim()} disabled>
            ...
          </button>
        ) : (
          <button
            key={page}
            className={`join-item btn ${sizeClass} ${page === currentPage ? 'btn-active' : ''}`.trim()}
            onClick={() => onPageChange(page)}
            aria-current={page === currentPage ? 'page' : undefined}
          >
            {page}
          </button>
        )
      )}
      <button
        className={`join-item btn ${sizeClass}`.trim()}
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        aria-label="Next page"
      >
        »
      </button>
    </div>
  );
});

Pagination.displayName = 'Pagination';

export default Pagination;
