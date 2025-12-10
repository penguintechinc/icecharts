interface AvatarProps {
  src?: string;
  alt?: string;
  initials?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  onClick?: () => void;
}

export default function Avatar({
  src,
  alt,
  initials,
  size = 'md',
  className = '',
  onClick,
}: AvatarProps) {
  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
    xl: 'h-16 w-16 text-lg',
  };

  const baseClasses = `${sizeClasses[size]} rounded-full flex items-center justify-center font-semibold overflow-hidden flex-shrink-0`;

  if (src) {
    return (
      <img
        src={src}
        alt={alt || 'Avatar'}
        className={`${baseClasses} object-cover ${onClick ? 'cursor-pointer' : ''} ${className}`}
        onClick={onClick}
      />
    );
  }

  return (
    <div
      className={`${baseClasses} bg-gradient-to-br from-ice-gold-400 to-ice-gold-500 text-slate-900 ${
        onClick ? 'cursor-pointer' : ''
      } ${className}`}
      onClick={onClick}
    >
      {initials || '?'}
    </div>
  );
}
