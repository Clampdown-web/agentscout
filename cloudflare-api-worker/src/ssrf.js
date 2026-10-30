/** SSRF checks for the roast fetcher. http/https only, no private targets, including after DNS. */

const BLOCKED_HOST = /(^|\.)(localhost|local|internal|invalid|localdomain)$/i;

export function isBlockedIp(ip) {
  if (!ip || typeof ip !== "string") return true;
  let raw = ip.trim().toLowerCase();
  if (raw.startsWith("[") && raw.endsWith("]")) raw = raw.slice(1, -1);
  if (raw.includes("%")) raw = raw.split("%")[0];
  if (raw.startsWith("::ffff:")) {
    const mapped = raw.slice(7);
    if (mapped.includes(".")) return isBlockedIp(mapped);
    const parts = mapped.split(":").filter(Boolean);
    if (parts.length === 2) {
      const n = (parseInt(parts[0], 16) << 16) + parseInt(parts[1], 16);
      return isBlockedIp([24, 16, 8, 0].map((s) => (n >>> s) & 255).join("."));
    }
  }
  if (raw.includes(".")) return blockedV4(raw);
  return blockedV6(raw);
}

function blockedV4(raw) {
  const bits = raw.split(".");
  if (bits.length !== 4) return true;
  const nums = [];
  for (const bit of bits) {
    if (!/^\d{1,3}$/.test(bit)) return true;
    if (bit.length > 1 && bit.startsWith("0")) return true;
    const n = Number(bit);
    if (n > 255) return true;
    nums.push(n);
  }
  const [a, b] = nums;
  if (a === 0 || a === 10 || a === 127) return true;
  if (a === 169 && b === 254) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 192 && b === 168) return true;
  if (a === 100 && b >= 64 && b <= 127) return true;
  if (a === 192 && b === 0) return true;
  if (a === 198 && (b === 18 || b === 19)) return true;
  if (a === 198 && b === 51) return true;
  if (a === 203 && b === 0) return true;
  if (a >= 224) return true;
  return false;
}

function blockedV6(raw) {
  if (raw === "::" || raw === "::1") return true;
  const full = expandV6(raw);
  if (!full) return true;
  const first = parseInt(full[0], 16);
  if ((first & 0xfe00) === 0xfc00) return true;
  if ((first & 0xffc0) === 0xfe80) return true;
  if ((first & 0xff00) === 0xff00) return true;
  if (full[0] === "2001" && full[1] === "0db8") return true;
  return false;
}

function expandV6(raw) {
  const halves = raw.split("::");
  if (halves.length > 2) return null;
  const head = halves[0] ? halves[0].split(":") : [];
  const tail = halves.length === 2 && halves[1] ? halves[1].split(":") : [];
  if (halves.length === 1 && head.length !== 8) return null;
  if ([...head, ...tail].some((p) => !/^[0-9a-f]{1,4}$/i.test(p))) return null;
  const missing = 8 - head.length - tail.length;
  if (missing < 0) return null;
  const pad = Array(missing).fill("0");
  return [...head, ...pad, ...tail].map((p) => p.padStart(4, "0"));
}

export function validateUrlShape(input) {
  let raw = String(input || "").trim();
  if (!raw) return { error: "Enter a public http or https URL." };
  if (!/^https?:\/\//i.test(raw)) raw = "https://" + raw;
  let url;
  try { url = new URL(raw); } catch { return { error: "That address is not a valid URL." }; }
  if (url.protocol !== "http:" && url.protocol !== "https:") return { error: "Only http and https URLs can be checked." };
  if (url.username || url.password) return { error: "URLs with a username or password are blocked." };
  const port = url.port;
  if (port && port !== "80" && port !== "443") return { error: "Only ports 80 and 443 can be checked." };
  const host = url.hostname.replace(/^\[|\]$/g, "").toLowerCase();
  if (!host || BLOCKED_HOST.test(host) || host === "0.0.0.0" || host === "metadata.google.internal") {
    return { error: "That host is not a public website." };
  }
  if (host.includes(":") || /^\d+\.\d+\.\d+\.\d+$/.test(host)) {
    if (isBlockedIp(host)) return { error: "That address is not public." };
  } else if (!/^[a-z0-9.-]+$/.test(host) || !host.includes(".") || host.includes("..")) {
    return { error: "That host is not a public website." };
  }
  url.hostname = host;
  url.hash = "";
  return { url };
}

export function isIpLiteral(host) {
  const raw = String(host || "").trim().toLowerCase().replace(/^\[|\]$/g, "");
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(raw)) return true;
  return raw.includes(":");
}

export async function resolveAndCheck(hostname, fetchImpl = fetch) {
  const host = String(hostname || "").replace(/^\[|\]$/g, "");
  // A public name is not an IP. Checking isBlockedIp() on it treats every hostname as blocked.
  if (isIpLiteral(host)) {
    if (isBlockedIp(host)) return { error: "That address is not public." };
    return { addresses: [host] };
  }
  const addresses = [];
  for (const type of ["A", "AAAA"]) {
    const res = await fetchImpl(`https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(host)}&type=${type}`, {
      headers: { accept: "application/dns-json" },
    });
    if (!res.ok) return { error: "Could not look up that host." };
    const data = await res.json();
    for (const ans of data.Answer || []) {
      if (typeof ans.data === "string") addresses.push(ans.data.replace(/\.$/, ""));
    }
  }
  if (!addresses.length) return { error: "That host has no public address." };
  if (addresses.some((ip) => isBlockedIp(ip))) return { error: "That host resolves to a blocked address." };
  return { addresses };
}
