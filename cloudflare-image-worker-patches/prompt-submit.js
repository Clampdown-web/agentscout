/**
 * Prompt submissions for the agentscout-image worker (api.agentscouthq.com).
 *
 * The worker source is not in this repo (see cloudflare-image-worker-patches
 * README.md), so this module is a drop-in: copy it into the agentscout-image
 * project next to its entry file and call handlePromptSubmit() from
 * handleSubmit() BEFORE the tool-only validation. It does not change
 * Turnstile verification, CORS/Origin checks, rate limits, or CSP — protect()
 * in security.js already gates POST /submit before the inner handler runs,
 * and this module runs inside that handler, after those gates.
 *
 * The prompt form (submit.html?type=prompt, from PR #160) posts:
 *   { type: "prompt", name, website: "", github: "", category,
 *     pricing: "Free", desc, prompt, works_with, email, x,
 *     newsletter_optin, company, tool: "", how_found, found,
 *     found_other, turnstileToken }
 * where name is the prompt title (maxlength 80), prompt is the prompt text
 * (maxlength 2000), category is one of the prompt categories below, and
 * works_with names the agents it works with (maxlength 120).
 *
 * A valid prompt submission is stored under a `prompt:` key prefix in the
 * SAME KV namespace the worker uses for tool submissions (`sub:` keys), so
 * it is never a new tool listing and the existing capture/export flow can
 * list prompt submissions separately. The stored record carries
 * type "prompt" and subject "Prompt submission"; the worker's email send
 * (and the form's mailto fallback) must use that subject line.
 *
 * Tool ("new") and update submissions are NOT handled here: handlePromptSubmit
 * returns { handled: false } for them and handleSubmit must continue with
 * its existing validation, unchanged. A tool submission without a website
 * is still rejected by that path, exactly as before.
 */

export const PROMPT_CATEGORIES = ["coding-agents", "mcp", "browser-agents"];
export const PROMPT_SUBJECT = "Prompt submission";
export const PROMPT_KEY_PREFIX = "prompt:";
/** 90 days, matching the submissions retention the recovery capture expects. */
export const PROMPT_TTL_SECONDS = 90 * 24 * 60 * 60;

const MAX_TITLE = 80;
const MAX_PROMPT = 2000;
const MAX_DESC = 500;
const MAX_WORKS_WITH = 120;
const MAX_WEBSITE = 300;
const MAX_EMAIL = 120;

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

function tooLong(value, max) {
  return value.length > max;
}

/** True only for a prompt submission; tool and update submissions fall through. */
export function isPromptSubmission(body) {
  return !!body && typeof body === "object" && !Array.isArray(body) && body.type === "prompt";
}

function bad(error) {
  return { ok: false, status: 400, error };
}

/**
 * Validate a prompt submission body. Returns { ok: true, record } with the
 * normalized record to store, or { ok: false, status: 400, error }.
 *
 * Required: a title (name), the prompt text, and a prompt category.
 * Website is optional; when given it must be http/https.
 */
export function validatePromptSubmission(body, now = Date.now()) {
  if (!isPromptSubmission(body)) return bad("Not a prompt submission.");
  const title = text(body.name);
  if (!title) return bad("Please add a title for your prompt.");
  if (tooLong(title, MAX_TITLE)) return bad("The prompt title is too long.");
  const prompt = text(body.prompt);
  if (!prompt) return bad("Please paste your prompt.");
  if (tooLong(prompt, MAX_PROMPT)) return bad("The prompt is too long.");
  const category = text(body.category);
  if (!PROMPT_CATEGORIES.includes(category)) return bad("Please pick a prompt category.");
  const website = text(body.website);
  if (website) {
    if (tooLong(website, MAX_WEBSITE)) return bad("The website link is too long.");
    let url = null;
    try { url = new URL(website); } catch { url = null; }
    if (!url || (url.protocol !== "http:" && url.protocol !== "https:")) {
      return bad("The website link must start with http:// or https://.");
    }
  }
  const worksWith = text(body.works_with);
  if (tooLong(worksWith, MAX_WORKS_WITH)) return bad("The works-with list is too long.");
  const desc = text(body.desc);
  if (tooLong(desc, MAX_DESC)) return bad("The description is too long.");
  const email = text(body.email);
  if (email && (tooLong(email, MAX_EMAIL) || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) {
    return bad("Please add a valid email.");
  }
  const record = {
    type: "prompt",
    subject: PROMPT_SUBJECT,
    ts: Math.floor(now / 1000),
    title,
    category,
    prompt,
    works_with: worksWith,
    desc,
    website,
    github: text(body.github),
    email,
    x: text(body.x),
    newsletter_optin: text(body.newsletter_optin),
    how_found: text(body.how_found),
    found: text(body.found),
    found_other: text(body.found_other),
  };
  return { ok: true, record };
}

export function promptStorageKey(id) {
  return `${PROMPT_KEY_PREFIX}${id}`;
}

function newId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `p-${Date.now().toString(36)}-${Math.floor(Math.random() * 0xffffffffffff).toString(36)}`;
}

/**
 * Store a validated prompt record in the submissions KV. `kv` is the same
 * Workers KV binding handleSubmit uses for tool submissions (`sub:` keys).
 * The key is `prompt:<uuid>`; the value is the record as JSON.
 */
export async function storePromptSubmission(kv, record, id = newId()) {
  if (!kv || typeof kv.put !== "function") throw new Error("prompt KV binding missing");
  const key = promptStorageKey(id);
  await kv.put(key, JSON.stringify(record), { expirationTtl: PROMPT_TTL_SECONDS });
  return key;
}

/**
 * The integration point. Call at the top of handleSubmit, before any
 * tool-only validation, passing the parsed JSON body and the worker's
 * submissions KV binding:
 *
 *   const prompt = await handlePromptSubmit(body, env.SUBMISSIONS);
 *   if (prompt.handled) return Response.json(prompt.body, { status: prompt.status });
 *
 * Returns { handled: false } for tool and update submissions so the
 * existing paths run unchanged, { handled: true, status: 200, body } for a
 * stored prompt, and { handled: true, status: 400, body: { error } } for
 * an invalid prompt submission. A missing KV binding fails closed (503)
 * rather than dropping the submission or treating it as a tool listing.
 */
export async function handlePromptSubmit(body, kv, now = Date.now()) {
  if (!isPromptSubmission(body)) return { handled: false };
  const validated = validatePromptSubmission(body, now);
  if (!validated.ok) {
    return { handled: true, status: validated.status, body: { error: validated.error } };
  }
  let key;
  try {
    key = await storePromptSubmission(kv, validated.record);
  } catch {
    return { handled: true, status: 503, body: { error: "Prompt storage is not configured." } };
  }
  return {
    handled: true,
    status: 200,
    body: { ok: true, type: "prompt", key, title: validated.record.title },
  };
}
