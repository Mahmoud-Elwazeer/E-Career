/**
 * Rashid Character Animation Variants
 * Shared framer-motion animation configurations
 */

import { Variants, easeInOut } from 'framer-motion';

export const BLINK_VARIANTS: Variants = {
  open: { scaleY: 1 },
  closed: { scaleY: 0.1, transition: { duration: 0.08 } },
};

export const BLINK_ANIMATION = {
  initial: 'open',
  animate: 'closed',
  transition: {
    repeat: Infinity,
    repeatDelay: Math.random() * 2000 + 3000, // 3-5 seconds random
    type: 'tween',
    ease: easeInOut,
  },
};

export const WAVE_VARIANTS: Variants = {
  idle: { rotate: 0 },
  wave: { rotate: 15 },
};

export const WAVE_ANIMATION = {
  initial: 'idle',
  animate: ['idle', 'wave', 'idle'],
  transition: {
    repeat: Infinity,
    duration: 1.5,
    ease: easeInOut,
  },
};

export const THINKING_VARIANTS: Variants = {
  idle: { rotate: 0 },
  think: { rotate: 5 },
};

export const THINKING_ANIMATION = {
  initial: 'idle',
  animate: ['idle', 'think', 'idle'],
  transition: {
    repeat: Infinity,
    duration: 2,
    ease: easeInOut,
  },
};

export const PRESENTING_VARIANTS: Variants = {
  idle: { y: 0 },
  present: { y: -5 },
};

export const PRESENTING_ANIMATION = {
  initial: 'idle',
  animate: ['idle', 'present', 'idle'],
  transition: {
    repeat: Infinity,
    duration: 1.2,
    ease: easeInOut,
  },
};

export const CELEBRATING_VARIANTS: Variants = {
  idle: { y: 0 },
  celebrate: { y: -8 },
};

export const CELEBRATING_ANIMATION = {
  initial: 'idle',
  animate: ['idle', 'celebrate', 'idle'],
  transition: {
    repeat: Infinity,
    duration: 0.8,
    ease: easeInOut,
  },
};

export const LISTENING_VARIANTS: Variants = {
  idle: { rotate: 0 },
  lean: { rotate: 3 },
};

export const LISTENING_ANIMATION = {
  initial: 'idle',
  animate: ['idle', 'lean', 'idle'],
  transition: {
    repeat: Infinity,
    duration: 2.5,
    ease: easeInOut,
  },
};

export const BUST_BREATHING_VARIANTS: Variants = {
  inhale: { scaleY: 1.01 },
  exhale: { scaleY: 1 },
};

export const BUST_BREATHING_ANIMATION = {
  initial: 'exhale',
  animate: ['exhale', 'inhale', 'exhale'],
  transition: {
    repeat: Infinity,
    duration: 3,
    ease: easeInOut,
  },
};

// Size configurations
export const SIZE_CONFIG = {
  xs: { width: 32, height: 64 },
  sm: { width: 48, height: 96 },
  md: { width: 128, height: 256 },
  lg: { width: 256, height: 512 },
  xl: { width: 400, height: 800 },
};

export const BUST_SIZE_CONFIG = {
  xs: { width: 32, height: 32 },
  sm: { width: 48, height: 48 },
  md: { width: 128, height: 128 },
  lg: { width: 256, height: 256 },
  xl: { width: 400, height: 400 },
};