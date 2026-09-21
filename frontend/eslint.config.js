import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "@typescript-eslint/no-unused-vars": "off",
      // `any` is pervasive in API-response plumbing across ~40 pages. Treat it as a
      // warning (tracked debt) rather than a hard error so the lint gate stays green
      // while we incrementally introduce typed domain models.
      "@typescript-eslint/no-explicit-any": "warn",
      "react-hooks/exhaustive-deps": "warn",
      // ── Design-system guard ──────────────────────────────────────────────
      // Block raw Tailwind palette classes (bg-gray-100, text-blue-600,
      // dark:border-red-500, …). They only define one/two shades and DON'T theme
      // across light/dark/night. Use semantic tokens instead — see DESIGN_SYSTEM.md
      // §2 cheatsheet (muted-foreground, destructive, success, warning, info,
      // signal, primary, border, surface-*). Warn-level: tracked debt, not a gate.
      "no-restricted-syntax": [
        "warn",
        {
          selector:
            "Literal[value=/(^|[\\s\"'`:])(bg|text|border|from|via|to|ring|fill|stroke|divide|placeholder|shadow|outline|decoration|accent|caret)-(gray|slate|zinc|neutral|stone|blue|indigo|violet|purple|fuchsia|pink|rose|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky)-(50|[1-9]00|950)\\b/]",
          message:
            "Raw Tailwind palette class detected — it won't theme across light/dark/night. Use a semantic token (see DESIGN_SYSTEM.md §2: muted-foreground, destructive, success, warning, info, signal, primary, border, surface-*).",
        },
        {
          selector:
            "TemplateElement[value.raw=/(^|[\\s\"'`:])(bg|text|border|from|via|to|ring|fill|stroke|divide|placeholder)-(gray|slate|zinc|neutral|stone|blue|indigo|violet|purple|fuchsia|pink|rose|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky)-(50|[1-9]00|950)\\b/]",
          message:
            "Raw Tailwind palette class in a template string — use a semantic token instead (see DESIGN_SYSTEM.md §2).",
        },
      ],
    },
  },
  {
    // Config/tooling files may use require() and Node globals.
    files: ["**/*.config.{ts,js}", "**/tailwind.config.ts"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
    },
  },
);
