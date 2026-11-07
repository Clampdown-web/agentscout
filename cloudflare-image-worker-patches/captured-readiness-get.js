/**
 * Fetch loop copied from the Nov 7 capture of agentscout-image index.js
 * (sha256 cf43a7a555662357f7aa7cde5474194213d749add2a7e264705f4f907b056f15).
 * This is the handler behavior, not the fix. protect() has to make global fetch
 * fail closed for this User-Agent, including on later hops.
 */
const CAP = 3e5;
const TMO = 6e3;

export function capturedBadHost(hostname) {
  const h = String(hostname || "").toLowerCase();
  if (!h.includes(".") || h.endsWith(".local") || h.endsWith(".internal") || h.endsWith(".invalid") || h === "localhost" || h.endsWith(".localhost")) return true;
  if (/^[0-9.]+$/.test(h) || h.includes(":") || h.startsWith("[")) return true;
  return false;
}

export async function capturedReadinessGet(url) {
  let cur = url;
  for (let i = 0; i < 4; i++) {
    const p = new URL(cur);
    if (!/^https?:$/.test(p.protocol) || p.port || p.username || capturedBadHost(p.hostname)) return { status: 0, err: "blocked" };
    let response;
    try {
      response = await fetch(cur, {
        method: "GET",
        redirect: "manual",
        headers: {
          "User-Agent": "AgentScoutReadinessChecker/1.0 (+https://agentscouthq.com/free-tools/ai-agent-readiness-checker.html)",
          Accept: "*/*",
        },
        signal: AbortSignal.timeout(TMO),
      });
    } catch {
      return { status: 0, err: "unreachable" };
    }
    if (response.status >= 300 && response.status < 400 && response.headers.get("Location")) {
      cur = new URL(response.headers.get("Location"), cur).toString();
      if (response.body && response.body.cancel) response.body.cancel().catch(() => {});
      continue;
    }
    let text = "";
    if (response.body && response.body.getReader) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let size = 0;
      while (size < CAP) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.length;
        text += decoder.decode(value, { stream: true });
      }
      reader.cancel().catch(() => {});
    } else {
      text = await response.text();
    }
    return {
      status: response.status,
      final: cur,
      type: (response.headers.get("Content-Type") || "").toLowerCase(),
      text: text.slice(0, CAP),
    };
  }
  return { status: 0, err: "too many redirects" };
}
