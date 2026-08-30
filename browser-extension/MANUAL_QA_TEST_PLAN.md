# E-Career Autofill Extension — Manual QA Test Plan

## Prerequisites

1. Chrome (or Chromium-based browser) with Developer Mode enabled
2. Load the extension: `chrome://extensions` > "Load unpacked" > select `browser-extension/`
3. An E-Career account with an extension token (`eck_...` prefix)
4. Open the extension popup and connect using your token

## Test Matrix

### T1 — Greenhouse (boards.greenhouse.io)

| Step | Action | Expected |
|------|--------|----------|
| T1.1 | Navigate to any Greenhouse application page (e.g. `https://boards.greenhouse.io/*/jobs/*/`) | Content script loads after ~500ms |
| T1.2 | Observe form fields | First Name, Last Name, Email, Location, Portfolio URL pre-filled from profile |
| T1.3 | Check blue banner | "E-Career: N fields pre-filled. Review & submit manually." appears top-right |
| T1.4 | Wait 8 seconds | Banner auto-dismisses |
| T1.5 | Check pre-filled values | Match your E-Career profile data exactly |
| T1.6 | Confirm no submit button was clicked | Form remains unsubmitted; submit button is untouched |
| T1.7 | If some fields were already filled | Those fields should NOT be overwritten |

### T2 — Lever (jobs.lever.co)

| Step | Action | Expected |
|------|--------|----------|
| T2.1 | Navigate to a Lever "Apply" page (e.g. `https://jobs.lever.co/{company}/{posting}/apply`) | Content script loads |
| T2.2 | Observe form fields | Full Name, Email, Current Company, Location, Portfolio URL pre-filled |
| T2.3 | Check blue banner | Banner appears with count of filled fields |
| T2.4 | Verify no auto-submit | Submit/Apply button not clicked; form is in editable state |
| T2.5 | If Lever page has no standard form (different layout) | Extension does nothing, no errors in console |

### T3 — Ashby (jobs.ashbyhq.com)

| Step | Action | Expected |
|------|--------|----------|
| T3.1 | Navigate to an Ashby application page (e.g. `https://jobs.ashbyhq.com/{company}/application?jobId=...`) | Content script loads |
| T3.2 | Observe form fields | First Name, Last Name, Email, Location, Portfolio URL, Current Company pre-filled |
| T3.3 | Check blue banner | Banner appears |
| T3.4 | Verify no auto-submit | Form remains in editable state |
| T3.5 | If Ashby uses non-standard field names | Some fields may not be detected — document which ones missed |

### T4 — Cross-cutting

| Step | Action | Expected |
|------|--------|----------|
| T4.1 | Disconnect token in popup, reload an ATS page | No autofill occurs, no banner, no errors |
| T4.2 | Reconnect token, reload | Autofill resumes |
| T4.3 | Visit a non-ATS page (e.g. google.com) | No content script runs, no console errors |
| T4.4 | Open DevTools console on each ATS page | No JavaScript errors from E-Career scripts |
| T4.5 | Check that fields already filled by the user are NOT overwritten | Extension skips non-empty fields |

## Known Limitations

- **Phone**: Not stored in E-Career profile; phone fields will not be autofilled
- **LinkedIn URL**: Not stored in CareerProfile model; LinkedIn fields will not be autofilled
- **Resume upload**: Not handled by autofill (file inputs require user interaction)
- **Custom questions**: ATS-specific custom fields are not detected
- **Lever full name**: Lever uses a single "Full Name" field; extension concatenates first + last name
- **Ashby field names vary**: Some Ashby employers customize field names; fallback selectors cover common patterns but may miss custom configurations
