import { Suspense, lazy, useEffect, useState } from "react";
import { RasheedScene } from "./RasheedScene";
import { RASHEED_GLB_URL } from "./glb-url";

/**
 * Rasheed3DOrFallback — the single drop-in point for the Rasheed character.
 *
 * Behavior:
 *   1. Probe for the GLB asset at RASHEED_GLB_URL (HEAD request).
 *   2. If present  -> lazy-load + render the real 3D <RasheedAvatar3D/> (the
 *      R3F bundle is code-split so it never bloats the initial payload).
 *   3. If absent / errors -> render the existing animated vector <RasheedScene/>
 *      (the app keeps working today, with a real character, not a placeholder).
 *
 * The moment `frontend/public/models/rasheed.glb` exists, every mount of this
 * component upgrades to 3D automatically — no other frontend change required.
 */

// Code-split: the entire three/R3F layer loads only when the GLB is present.
const RasheedAvatar3D = lazy(() =>
  import("./RasheedAvatar3D").then((m) => ({ default: m.RasheedAvatar3D })),
);

type Probe = "checking" | "present" | "absent";

// Module-level cache so we probe once per session, not per mount.
let cachedProbe: Probe = "checking";
let probePromise: Promise<Probe> | null = null;

function probeAsset(): Promise<Probe> {
  if (cachedProbe !== "checking") return Promise.resolve(cachedProbe);
  if (probePromise) return probePromise;
  probePromise = fetch(RASHEED_GLB_URL, { method: "HEAD" })
    .then((res) => {
      const ct = res.headers.get("content-type") ?? "";
      // A present GLB responds 200 and is NOT an HTML SPA fallback.
      const ok = res.ok && !ct.includes("text/html");
      cachedProbe = ok ? "present" : "absent";
      return cachedProbe;
    })
    .catch(() => {
      cachedProbe = "absent";
      return cachedProbe;
    });
  return probePromise;
}

interface Props {
  className?: string;
  frame?: "bust" | "full";
  /** Rendered while probing (defaults to the vector scene, so no flash of empty). */
  fallback?: React.ReactNode;
}

export function Rasheed3DOrFallback({ className = "", frame = "bust", fallback }: Props) {
  const [probe, setProbe] = useState<Probe>(cachedProbe);

  useEffect(() => {
    let alive = true;
    probeAsset().then((p) => alive && setProbe(p));
    return () => {
      alive = false;
    };
  }, []);

  const vector = fallback ?? <RasheedScene className={className} />;

  if (probe === "present") {
    return (
      <div className={`relative aspect-[3/4] w-full max-w-[440px] mx-auto ${className}`}>
        <Suspense fallback={vector}>
          <RasheedAvatar3D frame={frame} />
        </Suspense>
      </div>
    );
  }

  // checking or absent -> vector fallback (real working character).
  return <>{vector}</>;
}

export default Rasheed3DOrFallback;
