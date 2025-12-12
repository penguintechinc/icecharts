import React, { useEffect, useState } from 'react';
import './AttentionClickAnimation.css';

interface AttentionClickAnimationProps {
  x: number;
  y: number;
  onAnimationComplete?: () => void;
}

export const AttentionClickAnimation: React.FC<AttentionClickAnimationProps> = ({
  x,
  y,
  onAnimationComplete,
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      onAnimationComplete?.();
    }, 2000);

    return () => clearTimeout(timer);
  }, [onAnimationComplete]);

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className="attention-click-animation"
      style={{
        position: 'absolute',
        left: x,
        top: y,
        pointerEvents: 'none',
      }}
    >
      {/* Animated ripple rings */}
      <div className="ripple-ring ring-1" />
      <div className="ripple-ring ring-2" />
      <div className="ripple-ring ring-3" />
    </div>
  );
};
