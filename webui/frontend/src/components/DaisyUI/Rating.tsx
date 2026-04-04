import React, { memo, useId } from 'react';

export interface RatingProps {
  value: number;
  onChange?: (value: number) => void;
  max?: number;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  half?: boolean;
  readOnly?: boolean;
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export const Rating = memo(({
  value,
  onChange,
  max = 5,
  size = 'md',
  half = false,
  readOnly = false,
  variant,
  className = '',
}: RatingProps) => {
  const id = useId();
  const sizeClass = size !== 'md' ? `rating-${size}` : '';
  const halfClass = half ? 'rating-half' : '';
  const variantClass = variant ? `bg-${variant}` : 'bg-warning';

  if (half) {
    return (
      <div className={`rating ${sizeClass} ${halfClass} ${className}`.trim()}>
        <input type="radio" className="rating-hidden" checked={value === 0} readOnly />
        {Array.from({ length: max }, (_, i) => (
          <React.Fragment key={i}>
            <input
              type="radio"
              name={`rating-half-${id}`}
              className={`mask mask-star-2 mask-half-1 ${variantClass}`}
              checked={value === i + 0.5}
              onChange={() => !readOnly && onChange?.(i + 0.5)}
              readOnly={readOnly}
              aria-label={`${i + 0.5} stars`}
            />
            <input
              type="radio"
              name={`rating-half-${id}`}
              className={`mask mask-star-2 mask-half-2 ${variantClass}`}
              checked={value === i + 1}
              onChange={() => !readOnly && onChange?.(i + 1)}
              readOnly={readOnly}
              aria-label={`${i + 1} stars`}
            />
          </React.Fragment>
        ))}
      </div>
    );
  }

  return (
    <div className={`rating ${sizeClass} ${className}`.trim()}>
      {Array.from({ length: max }, (_, i) => (
        <input
          key={i}
          type="radio"
          className={`mask mask-star-2 ${variantClass}`}
          checked={value === i + 1}
          onChange={() => !readOnly && onChange?.(i + 1)}
          readOnly={readOnly}
          aria-label={`${i + 1} star${i + 1 !== 1 ? 's' : ''}`}
        />
      ))}
    </div>
  );
});

Rating.displayName = 'Rating';

export default Rating;
