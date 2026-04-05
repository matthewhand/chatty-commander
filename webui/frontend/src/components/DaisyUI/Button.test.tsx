import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Button } from './Button';
import { BrowserRouter } from 'react-router-dom';

describe('Button Component', () => {
  it('renders correctly with children', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Button variant="primary">Button</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-primary');

    rerender(<Button variant="secondary">Button</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-secondary');

    rerender(<Button variant="error">Button</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-error');
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<Button size="lg">Button</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-lg');

    rerender(<Button size="sm">Button</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-sm');
  });

  it('applies shape classes correctly', () => {
    const { rerender } = render(<Button shape="circle">C</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-circle');

    rerender(<Button shape="square">SQ</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-square');
  });

  it('shows loading spinner when loading is true', () => {
    render(<Button loading>Button</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('button')).toHaveClass('btn-disabled');
  });

  it('disables the button when disabled is true', () => {
    render(<Button disabled>Button</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByRole('button')).toHaveClass('btn-disabled');
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when loading or disabled', () => {
    const handleClick = vi.fn();
    const { rerender } = render(<Button loading onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();

    rerender(<Button disabled onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('renders as a Link when "to" prop is provided', () => {
    render(
      <BrowserRouter>
        <Button to="/test">Link Button</Button>
      </BrowserRouter>
    );
    const link = screen.getByRole('link', { name: /link button/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/test');
    expect(link).toHaveClass('btn');
  });

  it('applies active class when active is true', () => {
    render(<Button active>Active</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-active');
  });
});
