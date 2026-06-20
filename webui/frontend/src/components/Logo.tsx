import React from 'react';

export interface LogoProps {
    /** Hide the "ChattyCommander" wordmark, leaving only the SVG mark. */
    iconOnly?: boolean;
    /** Pixel size of the square SVG mark. */
    size?: number;
    /** Classes for the outer lockup (layout, font-size for the wordmark). */
    className?: string;
    /**
     * Color class for the SVG mark. Defaults to `text-primary`; override (e.g.
     * `text-primary-content`) when placing the mark on a colored surface.
     */
    iconClassName?: string;
    /**
     * Mark the lockup as decorative (aria-hidden, no role/label). Use when the
     * brand name is already announced by adjacent text.
     */
    decorative?: boolean;
}

/**
 * ChattyCommander brand lockup: an inline SVG mark (a stylized voice/sound-wave
 * speech bubble) plus the unified "ChattyCommander" wordmark.
 *
 * The mark strokes with `currentColor`, so its color comes from a DaisyUI text
 * token (`iconClassName`) rather than a hard-coded value — keeping it themeable
 * across the light/dark/cyberpunk/synthwave themes.
 */
const Logo: React.FC<LogoProps> = ({
    iconOnly = false,
    size = 28,
    className,
    iconClassName = 'text-primary',
    decorative = false,
}) => {
    return (
        <span
            className={`inline-flex items-center gap-2 ${className ?? ''}`.trim()}
            role={decorative ? undefined : 'img'}
            aria-label={decorative ? undefined : 'ChattyCommander'}
            aria-hidden={decorative ? true : undefined}
        >
            <svg
                width={size}
                height={size}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                className={`shrink-0 ${iconClassName}`.trim()}
                aria-hidden="true"
                focusable="false"
            >
                {/* Speech bubble — the "chat" half of the brand. */}
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
                {/* Voice waveform — the "command" half. */}
                <path d="M9 12.5v-1" />
                <path d="M12 14v-4" />
                <path d="M15 12.5v-1" />
            </svg>
            {!iconOnly && (
                <span className="font-bold tracking-tight whitespace-nowrap">
                    <span className="text-primary">Chatty</span>
                    <span className="text-base-content">Commander</span>
                </span>
            )}
        </span>
    );
};

export default Logo;
