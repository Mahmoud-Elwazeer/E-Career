/**
 * Rashid Bust Component
 * Upper body only (head + shoulders + partial torso)
 * Used for: chat header, floating widget, small UI spaces
 */

import { motion } from 'framer-motion';
import { RASHID_COLORS } from './colors';
import { BUST_BREATHING_VARIANTS, BUST_BREATHING_ANIMATION } from './animations';

interface RashidBustProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const SIZE_SCALES = {
  xs: 0.4,
  sm: 0.6,
  md: 1,
  lg: 1.5,
  xl: 2,
};

export function RashidBust({ size = 'md', className = '' }: RashidBustProps) {
  const scale = SIZE_SCALES[size];

  return (
    <motion.svg
      viewBox="0 0 200 200"
      width="100%"
      height="100%"
      initial="exhale"
      animate="exhale"
      variants={BUST_BREATHING_VARIANTS}
      transition={BUST_BREATHING_ANIMATION.transition}
      className={className}
      style={{ width: '100%', height: '100%' }}
    >
      {/* Neck */}
      <rect x="85" y="120" width="30" height="40" fill={RASHID_COLORS.pantsNavy} />
      
      {/* Shoulders */}
      <path
        d="M60 120 Q100 140 140 120 L140 130 Q100 150 60 130 Z"
        fill={RASHID_COLORS.pantsNavy}
      />
      
      {/* Shirt - Collar */}
      <path
        d="M85 120 L100 105 L115 120 L115 130 L85 130 Z"
        fill={RASHID_COLORS.shirtBlue}
      />
      
      {/* Shirt - Shoulders */}
      <path
        d="M60 130 Q100 150 140 130 L140 160 Q100 180 60 160 Z"
        fill={RASHID_COLORS.shirtBlue}
      />
      
      {/* Head - Neck connection */}
      <ellipse cx="100" cy="80" rx="25" ry="20" fill={RASHID_COLORS.skinBase} />
      
      {/* Head - Back hair */}
      <path
        d="M75 60 Q70 100 80 110 L120 110 Q130 100 125 60 Q100 50 75 60 Z"
        fill={RASHID_COLORS.hairDark}
      />
      
      {/* Head - Face */}
      <ellipse cx="100" cy="80" rx="30" ry="35" fill={RASHID_COLORS.skinBase} />
      
      {/* Hair - Top */}
      <path
        d="M70 55 Q100 30 130 55 Q130 70 100 75 Q70 70 70 55 Z"
        fill={RASHID_COLORS.hairDark}
      />
      
      {/* Hair - Sideburns */}
      <path
        d="M70 65 Q70 80 75 85 L75 70"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M130 65 Q130 80 125 85 L125 70"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="3"
        fill="none"
      />
      
      {/* Stubble */}
      <path
        d="M85 95 Q100 105 115 95"
        stroke={RASHID_COLORS.stubble}
        strokeWidth="1"
        fill="none"
        opacity="0.6"
      />
      
      {/* Eyes */}
      <g>
        <ellipse cx="90" cy="75" rx="4" ry="3" fill={RASHID_COLORS.eyesBrown} />
        <ellipse cx="110" cy="75" rx="4" ry="3" fill={RASHID_COLORS.eyesBrown} />
      </g>
      
      {/* Eyebrows */}
      <path
        d="M86 68 Q90 65 94 68"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="1.5"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M106 68 Q110 65 114 68"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="1.5"
        fill="none"
        strokeLinecap="round"
      />
      
      {/* Nose */}
      <path
        d="M100 82 Q100 88 95 90"
        stroke={RASHID_COLORS.skinShadow}
        strokeWidth="1.5"
        fill="none"
      />
      
      {/* Mouth - Smile */}
      <path
        d="M90 100 Q100 110 110 100"
        stroke={RASHID_COLORS.smileColor}
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
      />
      
      {/* Ear */}
      <ellipse cx="65" cy="80" rx="3" ry="5" fill={RASHID_COLORS.skinBase} />
      <ellipse cx="135" cy="80" rx="3" ry="5" fill={RASHID_COLORS.skinBase} />
    </motion.svg>
  );
}