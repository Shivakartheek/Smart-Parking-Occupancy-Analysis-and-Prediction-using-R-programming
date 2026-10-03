// FILE: static/js/script.js
// Small shared helper functions used by more than one page.
// Page-specific logic (dashboard, parking form, analytics charts,
// prediction form) lives in a <script> block at the bottom of each
// template, right next to the HTML it controls - this keeps things
// easy to follow for a beginner reading the code top to bottom.

/**
 * Returns an HTML string for a colored status badge (LOW / MEDIUM / HIGH).
 */
function statusBadgeHtml(status) {
  return `<span class="status-badge status-${status}">${status}</span>`;
}

/**
 * Simple fetch wrapper that always sends/receives JSON and
 * throws a readable error if the request fails.
 */
async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    const message = (data.errors && data.errors.join(" ")) || data.error || "Request failed.";
    throw new Error(message);
  }
  return data;
}
