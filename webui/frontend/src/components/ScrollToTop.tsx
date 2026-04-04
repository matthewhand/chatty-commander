import React, { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';
import { Button } from './DaisyUI';

const ScrollToTop: React.FC = () => {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setVisible(window.scrollY > 300);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToTop = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <Button
            variant="primary"
            size="sm"
            className={`btn-circle fixed bottom-6 right-6 z-50 transition-opacity duration-300 ${
                visible ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
            onClick={scrollToTop}
            aria-label="Scroll to top"
        >
            <ArrowUp size={16} />
        </Button>
    );
};

export default ScrollToTop;
