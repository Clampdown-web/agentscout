/**
 * Limiter calls copied from the Nov 7 capture of index.js.
 * The .catch branches treat a thrown limiter as allowed. protect() has to
 * make those calls return a failed result instead of throwing.
 */

export async function capturedReviewAllowed(env) {
  if (env.REVIEW_RL) {
    const { success } = await env.REVIEW_RL.limit({ key: "rv:test" }).catch(() => ({ success: true }));
    if (!success) return 429;
  }
  return 200;
}

export async function capturedTrackAllowed(env) {
  if (env.TRACK_RL) {
    const { success } = await env.TRACK_RL.limit({ key: "track:test" }).catch(() => ({ success: true }));
    if (!success) return 429;
  }
  return 200;
}

export async function capturedReadyAllowed(env) {
  if (env.READY_LIMIT) {
    const result = await env.READY_LIMIT.get(env.READY_LIMIT.idFromName("ready")).fetch("https://limit/").then((response) => response.json()).catch((error) => ({ ok: true, err: String(error && error.message || error).slice(0, 80) }));
    if (!result.ok) return 429;
    return 200;
  }
  if (env.READY_RL) {
    const { success } = await env.READY_RL.limit({ key: "203.0.113.10" });
    if (!success) return 429;
  }
  return 200;
}
