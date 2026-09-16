import { useEffect, useState } from "react";
import { RASHEED_GLB_URL } from "./glb-url";
import { type RasheedGlbReport } from "./validateRasheedGlb";

/**
 * RasheedGlbCheck — a dev-only overlay that loads /models/rasheed.glb and prints
 * a PASS/FAIL validation report against the integration contract. Mounted only
 * when the URL contains `?rasheedCheck=1`, so it never affects normal users.
 *
 * Use it to verify a supplied asset before shipping: open
 *   https://jobs.usamif.com/?rasheedCheck=1
 * and read the checklist. Only a green PASS means the Rasheed 3D task is done.
 */
export function RasheedGlbCheck() {
  const [report, setReport] = useState<RasheedGlbReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "done" | "absent">("loading");

  useEffect(() => {
    let alive = true;
    (async () => {
      // Probe first.
      try {
        const head = await fetch(RASHEED_GLB_URL, { method: "HEAD" });
        const ct = head.headers.get("content-type") ?? "";
        if (!head.ok || ct.includes("text/html")) {
          if (alive) setState("absent");
          return;
        }
      } catch {
        if (alive) setState("absent");
        return;
      }
      // Dynamically import the heavy loader + validator only for this check.
      try {
        const [{ GLTFLoader }, { validateRasheedGlb }] = await Promise.all([
          import("three-stdlib"),
          import("./validateRasheedGlb"),
        ]);
        const loader = new GLTFLoader();
        loader.load(
          RASHEED_GLB_URL,
          (gltf) => {
            if (!alive) return;
            setReport(validateRasheedGlb(gltf));
            setState("done");
          },
          undefined,
          (err) => {
            if (!alive) return;
            setError(String(err));
            setState("done");
          },
        );
      } catch (e) {
        if (alive) {
          setError(String(e));
          setState("done");
        }
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const box: React.CSSProperties = {
    position: "fixed",
    right: 12,
    bottom: 12,
    zIndex: 99999,
    maxWidth: 420,
    maxHeight: "70vh",
    overflow: "auto",
    background: "rgba(6,32,30,0.96)",
    color: "#EAF6F4",
    font: "12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace",
    padding: "14px 16px",
    borderRadius: 12,
    border: "1px solid #16403C",
    boxShadow: "0 10px 40px rgba(0,0,0,0.4)",
  };

  const Row = ({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) => (
    <div style={{ display: "flex", gap: 8, alignItems: "flex-start", padding: "2px 0" }}>
      <span style={{ color: ok ? "#4ADE80" : "#F87171", fontWeight: 700 }}>{ok ? "PASS" : "FAIL"}</span>
      <span>
        {label}
        {detail ? <span style={{ opacity: 0.7 }}> — {detail}</span> : null}
      </span>
    </div>
  );

  return (
    <div style={box} role="status" aria-live="polite">
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Rasheed GLB validation</div>
      {state === "loading" && <div>Loading {RASHEED_GLB_URL} …</div>}
      {state === "absent" && (
        <div>
          No asset at <code>{RASHEED_GLB_URL}</code>. App is on the vector fallback (expected until a
          valid Rasheed GLB is supplied). See <code>frontend/RASHEED_3D_ASSET_SPEC.md</code>.
        </div>
      )}
      {state === "done" && error && <div style={{ color: "#F87171" }}>Load error: {error}</div>}
      {state === "done" && report && (
        <>
          <div style={{ fontWeight: 700, color: report.pass ? "#4ADE80" : "#F87171", marginBottom: 6 }}>
            {report.pass ? "PASS ✅ — asset satisfies the contract" : "FAIL ❌ — asset not ready"}
          </div>
          <div style={{ opacity: 0.8, marginTop: 6, marginBottom: 2 }}>Required</div>
          {report.required.map((r) => (
            <Row key={r.label} {...r} />
          ))}
          <div style={{ opacity: 0.8, marginTop: 6, marginBottom: 2 }}>Recommended</div>
          {report.recommended.map((r) => (
            <Row key={r.label} {...r} />
          ))}
          <div style={{ opacity: 0.7, marginTop: 8, borderTop: "1px solid #16403C", paddingTop: 6 }}>
            {report.summary.bones} bones · {report.summary.skinnedMeshes} skinned ·{" "}
            {report.summary.morphNames.length} morphs · {report.summary.clipNames.length} clips ·{" "}
            {report.summary.triangles.toLocaleString()} tris
          </div>
        </>
      )}
    </div>
  );
}

export default RasheedGlbCheck;
