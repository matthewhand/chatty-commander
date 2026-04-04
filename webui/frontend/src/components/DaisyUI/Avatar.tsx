import React from 'react';

interface AvatarProps {
  src?: string;
  alt?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  shape?: 'circle' | 'square';
  online?: boolean;
  placeholder?: boolean;
  children?: React.ReactNode;
  className?: string;
  innerClassName?: string;
}

const sizeClasses = { xs: 'w-6 h-6', sm: 'w-8 h-8', md: 'w-12 h-12', lg: 'w-16 h-16', xl: 'w-24 h-24' };
const shapeClasses = { circle: 'rounded-full', square: 'rounded' };

const Avatar: React.FC<AvatarProps> = ({
  src, alt = 'avatar', size = 'md', shape = 'circle', online, placeholder, children, className = '', innerClassName = '',
}) => (
  <div className={`avatar ${online ? 'online' : ''} ${placeholder ? 'placeholder' : ''} ${className}`.trim()}>
    <div className={`${sizeClasses[size]} ${shapeClasses[shape]} ${innerClassName || (placeholder ? 'bg-neutral-focus text-neutral-content' : '')}`.trim()}>
      {placeholder ? <span>{children}</span> : <img src={src} alt={alt} />}
    </div>
  </div>
);

export default Avatar;
