import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DynamicDropdown } from './DynamicDropdown';

describe('DynamicDropdown', () => {
  it('opens when clicked and closes when Escape is pressed', () => {
    render(
      <DynamicDropdown buttonContent="Menu">
        <div>Dropdown Content</div>
      </DynamicDropdown>
    );

    const button = screen.getByRole('button', { name: /open menu/i });

    // Initially closed
    expect(screen.queryByText('Dropdown Content')).not.toBeInTheDocument();

    // Click to open
    fireEvent.click(button);
    expect(screen.getByText('Dropdown Content')).toBeInTheDocument();

    // Press Escape
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });

    // Should be closed
    expect(screen.queryByText('Dropdown Content')).not.toBeInTheDocument();
  });
});
