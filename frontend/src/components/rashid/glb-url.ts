/**
 * Fixed drop-in path for the Rasheed 3D asset. Kept in its own module so the
 * fallback/probe path can import it without pulling in the three.js/R3F bundle
 * (which lives in RasheedAvatar3D and is code-split).
 *
 * See frontend/RASHEED_3D_ASSET_SPEC.md for the asset requirements.
 */
export const RASHEED_GLB_URL = "/models/rasheed.glb";
