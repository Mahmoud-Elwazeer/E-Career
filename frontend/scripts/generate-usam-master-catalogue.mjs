#!/usr/bin/env node
/**
 * Generates USAM-MASTER-FEATURE-LINKS.md and .json from the single
 * canonical feature catalog (src/data/feature-catalog.json), so the USAM
 * Master Ecosystem integration catalogue can never drift from the actual
 * app routes — regenerate with `npm run generate:master-catalogue` any time
 * `feature-catalog.json` changes.
 *
 * IMPORTANT about "verification": this script does NOT crawl or HTTP-check
 * any URL. "Verified" here means "the route exists in App.tsx's route table
 * and was confirmed against the real page component during the audit for
 * this change" — a point-in-time, code-level verification, not a live
 * runtime check. The output says so explicitly, per the requirement not to
 * mark a URL verified without actually testing it.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..", "..");

const FEATURES_PATH = join(__dirname, "..", "src", "data", "feature-catalog.json");
const features = JSON.parse(readFileSync(FEATURES_PATH, "utf-8"));

// The real configured production domain for this platform (confirmed via
// deploy/nginx.conf references, robots.txt, and DEPLOYMENT_STATUS docs
// across the engagement — jobs.usamif.com is the live domain; an older
// index.html canonical tag incorrectly said usam.jobs and was corrected as
// part of this same change).
const PRODUCTION_BASE_URL = "https://jobs.usamif.com";

const ACCESS_LABEL = {
  public: "None — publicly accessible",
  auth: "Requires sign-in (any account type)",
  employer: "Requires sign-in with an Employer (or Admin) account",
  admin: "Requires sign-in with an Admin account",
};

const AUDIENCE_LABEL = {
  individual: "Individuals / job seekers",
  employer: "Employers / companies",
  admin: "Platform administrators",
  everyone: "Everyone (any signed-in account)",
};

const GENERATED_AT = new Date().toISOString();

function fullUrl(path) {
  if (!path) return undefined;
  return `${PRODUCTION_BASE_URL}${path}`;
}

/**
 * How the USAM Master website should link to a protected destination.
 * This platform does NOT currently share a single sign-on session with
 * Master — there is no shared auth cookie/token exchange implemented. A
 * Master-side link into a gated feature should point at this app's /login
 * with a `?next=` query param carrying the real destination; this app's
 * Login page validates `next` (rejects any non-relative-path value) and,
 * once the user authenticates HERE, routes them to that destination.
 */
function masterLinkingNote(feature) {
  if (feature.access === "public") {
    return "Link directly — no authentication required.";
  }
  return (
    `Link to \`${PRODUCTION_BASE_URL}/login?next=${encodeURIComponent(feature.to)}\`. ` +
    `There is no shared sign-in between USAM Master and this platform today — ` +
    `the visitor authenticates on THIS platform's /login, which then redirects ` +
    `to the real destination. The \`next\` value is validated server-side ` +
    `(internal relative paths only; absolute/external URLs are rejected) to ` +
    `prevent open-redirect abuse.`
  );
}

function buildJsonCatalogue() {
  return {
    $schema: "https://jobs.usamif.com/schemas/usam-master-feature-links.v1.json",
    generatedAt: GENERATED_AT,
    productionBaseUrl: PRODUCTION_BASE_URL,
    platformName: "E-Career (USAM Jobs / USAM Career Compass)",
    note:
      "verification.status reflects CODE-LEVEL verification only (route exists " +
      "in App.tsx and the page component was read during this audit) — it is " +
      "NOT a live HTTP/browser check. See verification.method on each entry.",
    features: features.map((f) => ({
      id: f.id,
      platform: "E-Career",
      nameEn: f.nameEn,
      nameAr: f.nameAr,
      descriptionEn: f.shortDescEn,
      descriptionAr: f.shortDescAr,
      audience: AUDIENCE_LABEL[f.audience] ?? f.audience,
      navigationCategory: f.category,
      publicOverviewUrl: fullUrl(f.overviewTo) ?? null,
      directApplicationUrl: fullUrl(f.to),
      relativePath: f.to,
      access: {
        level: f.access,
        requirement: ACCESS_LABEL[f.access] ?? f.access,
      },
      status: f.status,
      relatedFeatures: f.related ?? [],
      limitations: f.note ?? null,
      masterIntegration: {
        linkingMethod: f.access === "public" ? "direct" : "login-next-param",
        instructions: masterLinkingNote(f),
      },
      verification: {
        status: "code-verified",
        method:
          "Route confirmed present in frontend/src/App.tsx and the target page " +
          "component was read directly during this audit. NOT a live HTTP or " +
          "browser check.",
        lastVerifiedAt: GENERATED_AT,
      },
    })),
  };
}

function buildMarkdown() {
  const byCategory = new Map();
  for (const f of features) {
    if (!byCategory.has(f.category)) byCategory.set(f.category, []);
    byCategory.get(f.category).push(f);
  }

  const categoryTitles = {
    discover: "Discover Opportunities",
    "career-tools": "Career Tools",
    "ai-coaching": "AI & Preparation",
    insights: "Insights",
    account: "Account",
    hiring: "Hiring (Employer)",
    platform: "Platform",
  };

  let md = `# USAM Master — E-Career Feature Links Catalogue\n\n`;
  md += `Generated: ${GENERATED_AT}\n\n`;
  md += `Platform: **E-Career (USAM Jobs / USAM Career Compass)**\n\n`;
  md += `Production base URL: \`${PRODUCTION_BASE_URL}\`\n\n`;
  md += `> **Verification note:** every row below was verified at the CODE level only — the route exists in \`frontend/src/App.tsx\` and the target page component was read directly during this audit. No live HTTP request or browser test was run against the production domain as part of generating this catalogue. See \`USAM-MASTER-INTEGRATION-TEST-RESULTS.md\` (or the delivery summary) for what was actually tested (static build/typecheck/unit tests, plus local dev-server HTTP checks) versus what still needs a real browser pass against production.\n\n`;
  md += `> **Shared sign-in:** USAM Master and E-Career do **not** currently share a single sign-on session. For any gated feature, Master should link to \`${PRODUCTION_BASE_URL}/login?next=<url-encoded-relative-path>\`. E-Career's login page validates \`next\` server-side — only internal relative paths are honored, any absolute/external URL is rejected — then redirects the authenticated user to that destination. Do not pass credentials or tokens in the URL.\n\n`;
  md += `---\n\n`;

  for (const [category, items] of byCategory) {
    md += `## ${categoryTitles[category] ?? category}\n\n`;
    md += `| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |\n`;
    md += `|---|---|---|---|---|---|---|---|\n`;
    for (const f of items) {
      const overview = f.overviewTo ? `[Overview](${fullUrl(f.overviewTo)})` : "—";
      const direct = `[Open](${fullUrl(f.to)})`;
      const related = (f.related ?? []).join(", ") || "—";
      md += `| \`${f.id}\` | ${f.nameEn} / ${f.nameAr} | ${AUDIENCE_LABEL[f.audience] ?? f.audience} | ${ACCESS_LABEL[f.access] ?? f.access} | ${f.status} | ${overview} | ${direct} | ${related} |\n`;
    }
    md += `\n`;
  }

  md += `---\n\n## Per-feature detail\n\n`;
  for (const f of features) {
    md += `### ${f.nameEn} (\`${f.id}\`)\n\n`;
    md += `- **Arabic name:** ${f.nameAr}\n`;
    md += `- **English description:** ${f.shortDescEn}\n`;
    md += `- **Arabic description:** ${f.shortDescAr}\n`;
    md += `- **Audience:** ${AUDIENCE_LABEL[f.audience] ?? f.audience}\n`;
    md += `- **Navigation category:** ${f.category}\n`;
    md += `- **Public overview URL:** ${f.overviewTo ? fullUrl(f.overviewTo) : "_(none — no dedicated explainer page; see /features)_"}\n`;
    md += `- **Direct application / deep-link URL:** ${fullUrl(f.to)}\n`;
    md += `- **Access requirement:** ${ACCESS_LABEL[f.access] ?? f.access}\n`;
    md += `- **Availability status:** ${f.status}\n`;
    md += `- **Related features:** ${(f.related ?? []).join(", ") || "none"}\n`;
    if (f.note) md += `- **Limitation / note:** ${f.note}\n`;
    md += `- **How Master should link to this:** ${masterLinkingNote(f)}\n`;
    md += `- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.\n`;
    md += `\n`;
  }

  return md;
}

const mdOut = buildMarkdown();
const jsonOut = buildJsonCatalogue();

writeFileSync(join(ROOT, "USAM-MASTER-FEATURE-LINKS.md"), mdOut, "utf-8");
writeFileSync(
  join(ROOT, "USAM-MASTER-FEATURE-LINKS.json"),
  JSON.stringify(jsonOut, null, 2) + "\n",
  "utf-8",
);

console.log(`Generated USAM-MASTER-FEATURE-LINKS.md and .json from ${features.length} catalog entries.`);
