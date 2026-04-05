import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Input } from './Input';

describe('Input Component', () => {
  it('renders correctly with placeholder', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText(/enter text/i)).toBeInTheDocument();
  });

  it('renders label correctly', () => {
    render(<Input label="My Label" id="test-input" />);
    expect(screen.getByText('My Label')).toBeInTheDocument();
    expect(screen.getByLabelText('My Label')).toBeInTheDocument();
  });

  it('renders error message correctly', () => {
    render(<Input error="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveClass('input-error');
  });

  it('renders helper text correctly', () => {
    render(<Input helperText="Hint text" />);
    expect(screen.getByText('Hint text')).toBeInTheDocument();
  });

  it('calls onChange handler when typing', () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'hello' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('shows password toggle when type is password', () => {
    render(<Input type="password" label="Password" />);
    const toggleButton = screen.getByLabelText(/show password/i);
    expect(toggleButton).toBeInTheDocument();
    
    const input = screen.getByLabelText('Password');
    expect(input).toHaveAttribute('type', 'password');
    
    fireEvent.click(toggleButton);
    expect(input).toHaveAttribute('type', 'text');
    expect(screen.getByLabelText(/hide password/i)).toBeInTheDocument();
  });

  it('renders prefix and suffix correctly', () => {
    render(<Input prefix="pre" suffix="post" />);
    expect(screen.getByText('pre')).toBeInTheDocument();
    expect(screen.getByText('post')).toBeInTheDocument();
  });
});
