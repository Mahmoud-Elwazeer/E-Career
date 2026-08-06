/**
 * Rashid Character Color Constants
 * Shared color palette for all Rashid character components
 */

export const RASHID_COLORS = {
  // Skin tones
  skinLight: '#f5d0b0',
  skinBase: '#D4956A',
  skinShadow: '#C6855A',
  
  // Hair and beard
  hairDark: '#2d2d2d',
  hairBrown: '#3B2417',
  stubble: '#5C4033',
  
  // Clothing
  shirtBlue: '#3b82f6',
  shirtLight: '#60a5fa',
  shirtDark: '#2563eb',
  pantsNavy: '#1e293b',
  pantsDark: '#0f172a',
  shoesBrown: '#6B4C3B',
  shoesDark: '#4A352A',
  
  // Face features
  eyesBrown: '#5D4037',
  eyesShadow: '#3E2723',
  smileColor: '#E57373',
  
  // Accessories
  glasses: 'rgba(0,0,0,0.1)',
  
  // Animation colors
  blinkLine: '#3E2723',
} as const;

export type RashidColorKey = keyof typeof RASHID_COLORS;