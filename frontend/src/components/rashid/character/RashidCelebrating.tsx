/**
 * Rashid Celebrating Component
 * Both hands raised, big smile
 * Used for: after applying to job, completing onboarding, earning badge
 */

import { motion } from 'framer-motion';
import { RASHID_COLORS } from './colors';
import { CELEBRATING_VARIANTS, CELEBRATING_ANIMATION } from './animations';

interface RashidCelebratingProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const SIZE_SCALES = {
  xs: 0.3,
  sm: 0.5,
  md: 1,
  lg: 1.5,
  xl: 2,
};

export function RashidCelebrating({ size = 'md', className = '' }: RashidCelebratingProps) {
  const scale = SIZE_SCALES[size];

  return (
    <motion.svg
      viewBox="0 0 200 400"
      width="100%"
      height="100%"
      className={className}
      style={{ width: '100%', height: '100%' }}
    >
      {/* Feet */}
      <ellipse cx="80" cy="380" rx="15" ry="8" fill={RASHID_COLORS.shoesBrown} />
      <ellipse cx="120" cy="380" rx="15" ry="8" fill={RASHID_COLORS.shoesBrown} />
      
      {/* Legs */}
      <path d="M85 320 L80 380" stroke={RASHID_COLORS.pantsNavy} strokeWidth="18" strokeLinecap="round" />
      <path d="M115 320 L120 380" stroke={RASHID_COLORS.pantsNavy} strokeWidth="18" strokeLinecap="round" />
      
      {/* Pants */}
      <path
        d="M70 280 L85 320 L115 320 L130 280 L130 300 L70 300 Z"
        fill={RASHID_COLORS.pantsNavy}
      />
      
      {/* Shirt - Lower */}
      <path
        d="M65 260 L70 280 L130 280 L135 260 L135 290 L65 290 Z"
        fill={RASHID_COLORS.shirtBlue}
      />
      
      {/* Shirt - Upper */}
      <path
        d="M60 220 L65 260 L135 260 L140 220 L140 250 L60 250 Z"
        fill={RASHID_COLORS.shirtBlue}
      />
      
      {/* Collar */}
      <path
        d="M95 220 L100 205 L105 220 L105 240 L95 240 Z"
        fill={RASHID_COLORS.shirtBlue}
      />
      
      {/* Head - Neck */}
      <rect x="85" y="180" width="30" height="40" fill={RASHID_COLORS.pantsNavy} />
      
      {/* Head - Back hair */}
      <path
        d="M75 140 Q70 180 80 190 L120 190 Q130 180 125 140 Q100 130 75 140 Z"
        fill={RASHID_COLORS.hairDark}
      />
      
      {/* Head - Face */}
      <ellipse cx="100" cy="160" rx="35" ry="40" fill={RASHID_COLORS.skinBase} />
      
      {/* Hair - Top */}
      <path
        d="M65 130 Q100 80 135 130 Q135 150 100 155 Q65 150 65 130 Z"
        fill={RASHID_COLORS.hairDark}
      />
      
      {/* Hair - Sideburns */}
      <path
        d="M65 145 Q65 170 75 180 L75 150"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M135 145 Q135 170 125 180 L125 150"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="3"
        fill="none"
      />
      
      {/* Stubble */}
      <path
        d="M85 175 Q100 185 115 175"
        stroke={RASHID_COLORS.stubble}
        strokeWidth="1"
        fill="none"
        opacity="0.6"
      />
      
      {/* Eyes - Happy */}
      <g>
        <ellipse cx="90" cy="155" rx="5" ry="3" fill={RASHID_COLORS.eyesBrown} />
        <ellipse cx="110" cy="155" rx="5" ry="3" fill={RASHID_COLORS.eyesBrown} />
      </g>
      
      {/* Eyebrows - Happy */}
      <path
        d="M85 145 Q90 140 95 145"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="1.5"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M105 145 Q110 140 115 145"
        stroke={RASHID_COLORS.hairDark}
        strokeWidth="1.5"
        fill="none"
        strokeLinecap="round"
      />
      
      {/* Nose */}
      <path
        d="M100 165 Q100 175 95 178"
        stroke={RASHID_COLORS.skinShadow}
        strokeWidth="1.5"
        fill="none"
      />
      
      {/* Mouth - Big Smile */}
      <path
        d="M85 185 Q100 205 115 185"
        stroke={RASHID_COLORS.smileColor}
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      
      {/* Ear */}
      <ellipse cx="65" cy="160" rx="4" ry="6" fill={RASHID_COLORS.skinBase} />
      <ellipse cx="135" cy="160" rx="4" ry="6" fill={RASHID_COLORS.skinBase} />
      
      {/* Left Arm - Celebrating */}
      <motion.g
        initial="idle"
        animate="celebrate"
        variants={CELEBRATING_VARIANTS}
        transition={CELEBRATING_ANIMATION.transition}
      >
        <path
          d="M60 230 L40 180"
          stroke={RASHID_COLORS.skinBase}
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Hand */}
        <circle cx="40" cy="180" r="6" fill={RASHID_COLORS.skinBase} />
      </motion.g>
      
      {/* Right Arm - Celebrating */}
      <motion.g
        initial="idle"
        animate="celebrate"
        variants={CELEBRATING_VARIANTS}
        transition={CELEBRATING_ANIMATION.transition}
      >
        <path
          d="M140 230 L160 180"
          stroke={RASHID_COLORS.skinBase}
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Hand */}
        <circle cx="160" cy="180" r="6" fill={RASHID_COLORS.skinBase} />
      </motion.g>
    </motion.svg>
  );
}