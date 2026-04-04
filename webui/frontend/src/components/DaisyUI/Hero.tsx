import React, { memo } from 'react';

export interface HeroProps {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
  className?: string;
  overlay?: boolean;
  backgroundImage?: string;
}

export const Hero = memo(({ title, subtitle, children, className = '', overlay = false, backgroundImage }: HeroProps) => {
  const style = backgroundImage ? { backgroundImage: `url(${backgroundImage})` } : undefined;

  return (
    <div className={`hero min-h-[20rem] ${className}`.trim()} style={style}>
      {overlay && <div className="hero-overlay bg-opacity-60" />}
      <div className="hero-content text-center">
        <div className="max-w-md">
          <h1 className="text-5xl font-bold">{title}</h1>
          {subtitle && <p className="py-6">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  );
});

Hero.displayName = 'Hero';

export default Hero;
