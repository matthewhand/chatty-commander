import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { Badge } from './Badge';

describe('Badge Component', () => {
  it('renders correctly with children', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText(/test badge/i)).toBeInTheDocument();
  });

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Badge variant="primary">Badge</Badge>);
    expect(screen.getByText('Badge')).toHaveClass('badge-primary');

    rerender(<Badge variant="secondary">Badge</Badge>);
    expect(screen.getByText('Badge')).toHaveClass('badge-secondary');

    rerender(<Badge variant="success">Badge</Badge>);
    expect(screen.getByText('Badge')).toHaveClass('badge-success');
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<Badge size="small">Badge</Badge>);
    expect(screen.getByText('Badge')).toHaveClass('badge-xs');

    rerender(<Badge size="lg">Badge</Badge>);
    expect(screen.getByText('Badge')).toHaveClass('badge-lg');
  });

  it('applies outline style correctly', () => {
    render(<Badge badgeStyle="outline">Outline</Badge>);
    expect(screen.getByText('Outline')).toHaveClass('badge-outline');
  });

  it('renders icon when provided', () => {
    render(<Badge icon={<span data-testid="test-icon" />}>With Icon</Badge>);
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });
});
