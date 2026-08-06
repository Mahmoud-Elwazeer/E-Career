/**
 * Rashid Character Component
 * Unified component for displaying Rashid with different poses
 */

import { motion, AnimatePresence } from 'framer-motion';
import { RASHID_COLORS } from './colors';
import { SIZE_CONFIG, BUST_SIZE_CONFIG } from './animations';
import { RashidBust } from './RashidBust';
import { RashidWave } from './RashidWave';
import { RashidThinking } from './RashidThinking';
import { RashidPresenting } from './RashidPresenting';
import { RashidCelebrating } from './RashidCelebrating';
import { RashidListening } from './RashidListening';

export type RashidPose = 'wave' | 'thinking' | 'presenting' | 'celebrating' | 'listening' | 'bust';
export type RashidSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface RashidCharacterProps {
  pose: RashidPose;
  size?: RashidSize;
  animated?: boolean;
  className?: string;
}

const POSE_COMPONENTS = {
  wave: RashidWave,
  thinking: RashidThinking,
  presenting: RashidPresenting,
  celebrating: RashidCelebrating,
  listening: RashidListening,
  bust: RashidBust,
};

export function RashidCharacter({ 
  pose = 'bust', 
  size = 'md', 
  animated = true,
  className = '' 
}: RashidCharacterProps) {
  const Component = POSE_COMPONENTS[pose];
  const isBust = pose === 'bust';
  
  const sizeConfig = isBust ? BUST_SIZE_CONFIG : SIZE_CONFIG;
  const sizeScale = sizeConfig[size] || SIZE_CONFIG.md;
  
  // Calculate dimensions based on size
  const width = sizeConfig[size]?.width || 128;
  const height = sizeConfig[size]?.height || 256;

  return (
    <motion.div
      className={className}
      style={{ width, height }}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Component size={size} />
    </motion.div>
  );
}