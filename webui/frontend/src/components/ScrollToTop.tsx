import React, { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

interface ScrollToTopProps {
    /**
     * The scrolling element to observe. May be a ref to an element or a CSS
     * selector resolved against the document. The app's scroll container is the
     * `<main class="overflow-y-auto">` element, NOT the window, so observing
     * `window.scroll` never fires. Defaults to `#main-content`.
     */
    target?: React.RefObject<HTMLElement> | string;
}

function resolveTarget(target?: ScrollToTopProps['target']): HTMLElement | null {
    if (!target) {
        return document.getElementById('main-content');
    }
    if (typeof target === 'string') {
        return document.querySelector<HTMLElement>(target);
    }
    return target.current;
}

const ScrollToTop: React.FC<ScrollToTopProps> = ({ target = '#main-content' }) => {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const el = resolveTarget(target);
        if (!el) {
            return;
        }

        const handleScroll = () => {
            setVisible(el.scrollTop > 300);
        };

        // Sync initial state in case the container is already scrolled.
        handleScroll();

        el.addEventListener('scroll', handleScroll, { passive: true });
        return () => el.removeEventListener('scroll', handleScroll);
    }, [target]);

    const scrollToTop = () => {
        const el = resolveTarget(target);
        el?.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <button
            onClick={scrollToTop}
            className={`btn btn-circle btn-primary btn-sm fixed bottom-6 right-6 z-50 transition-opacity duration-300 ${
                visible ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
            aria-label="Scroll to top"
        >
            <ArrowUp size={16} />
        </button>
    );
};

export default ScrollToTop;
