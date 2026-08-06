/**
 * Rashid Avatar Component
 * A friendly Egyptian HR mentor character with animated states
 */

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

interface RashidAvatarProps {
  state?: 'idle' | 'talking' | 'thinking';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

const RASHID_COLORS = {
  skin: '#f5d0b0',
  skinShadow: '#e6c09a',
  hair: '#2d2d2d',
  shirt: '#3b82f6',
  shirtLight: '#60a5fa',
  shirtDark: '#2563eb',
  eyes: '#1e3a8a',
  smile: '#dc2626',
};

export function RashidAvatar({ 
  state = 'idle', 
  size = 'md',
  onClick 
}: RashidAvatarProps) {
  const [currentState, setCurrentState] = useState<'idle' | 'talking' | 'thinking'>(state);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    setCurrentState(state);
  }, [state]);

  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-16 h-16',
    lg: 'w-20 h-20',
  };

  const animationVariants = {
    idle: {
      y: [0, -2, 0],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut' as const,
      },
    },
    talking: {
      y: [0, -3, 0, -3, 0],
      transition: {
        duration: 0.5,
        repeat: Infinity,
        ease: 'easeInOut' as const,
      },
    },
    thinking: {
      rotate: [0, 5, 0, -5, 0],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut' as const,
      },
    },
  };

  return (
    <motion.div
      className={`${sizeClasses[size]} relative cursor-pointer select-none`}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      animate={currentState}
      variants={animationVariants}
      initial={false}
    >
      {/* Speech bubble indicator when talking */}
      {currentState === 'talking' && (
        <motion.div
          className="absolute -top-2 -right-2 w-3 h-3 bg-blue-500 rounded-full"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 0.3, repeat: Infinity }}
        />
      )}

      {/* Thinking dots */}
      {currentState === 'thinking' && (
        <div className="absolute -top-4 -right-4 flex gap-1">
          {[1, 2, 3].map((i) => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 bg-gray-600 rounded-full"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ 
                duration: 1, 
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      )}

      {/* Rashid Character SVG */}
      <svg viewBox="0 0 100 120" className="w-full h-full drop-shadow-lg">
        {/* Body - Shirt */}
        <path
          d="M25,100 L25,70 Q25,55 40,55 L60,55 Q75,55 75,70 L75,100 Z"
          fill={RASHID_COLORS.shirt}
        />
        <path
          d="M25,100 L25,115 L75,115 L75,100 Z"
          fill={RASHID_COLORS.shirtDark}
        />
        
        {/* Collar */}
        <path
          d="M40,55 L50,65 L60,55"
          fill="none"
          stroke={RASHID_COLORS.shirtLight}
          strokeWidth="3"
        />

        {/* Head */}
        <ellipse
          cx="50"
          cy="40"
          rx="22"
          ry="26"
          fill={RASHID_COLORS.skin}
        />

        {/* Hair - Short dark hair */}
        <path
          d="M28,35 Q28,15 50,15 Q72,15 72,35 Q72,25 68,25 Q65,25 65,30 Q65,35 50,35 Q35,35 35,30 Q35,25 32,25 Q28,25 28,35 Z"
          fill={RASHID_COLORS.hair}
        />

        {/* Beard - Light stubble */}
        <path
          d="M35,50 Q35,45 40,45 Q45,45 45,50 Q45,55 50,55 Q55,55 55,50 Q55,45 60,45 Q65,45 65,50"
          fill="none"
          stroke="#5d5d5d"
          strokeWidth="1.5"
          strokeLinecap="round"
        />

        {/* Eyes */}
        <g fill={RASHID_COLORS.eyes}>
          <ellipse cx="42" cy="38" rx="3" ry="4" />
          <ellipse cx="58" cy="38" rx="3" ry="4" />
        </g>

        {/* Eyebrows */}
        <path
          d="M39,34 Q42,32 45,34"
          fill="none"
          stroke={RASHID_COLORS.hair}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <path
          d="M55,34 Q58,32 61,34"
          fill="none"
          stroke={RASHID_COLORS.hair}
          strokeWidth="1.5"
          strokeLinecap="round"
        />

        {/* Smile */}
        <path
          d="M45,50 Q50,55 55,50"
          fill="none"
          stroke={RASHID_COLORS.smile}
          strokeWidth="2"
          strokeLinecap="round"
        />

        {/* Hand gesture - Right hand raised */}
        <g transform="translate(65, 75)">
          <motion.ellipse
            cx="0"
            cy="0"
            rx="6"
            ry="8"
            fill={RASHID_COLORS.skin}
            animate={currentState === 'talking' ? { y: [0, -2, 0] } : {}}
            transition={{ duration: 0.3, repeat: Infinity }}
          />
          <motion.path
            d="M-3,-8 Q0,-12 3,-8"
            fill="none"
            stroke={RASHID_COLORS.skin}
            strokeWidth="2"
            animate={currentState === 'talking' ? { d: ["M-3,-8 Q0,-12 3,-8", "M-4,-10 Q0,-14 4,-10"] } : {}}
            transition={{ duration: 0.3, repeat: Infinity }}
          />
        </g>
      </svg>
    </motion.div>
  );
}