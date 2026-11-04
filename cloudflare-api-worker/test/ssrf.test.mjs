import test from "node:test";
import assert from "node:assert/strict";
import { isBlockedIp, validateUrlShape, resolveAndCheck } from "../src/ssrf.js";
import { scoreListing } from "../src/score.js";

test("blocks private, loopback, link-local, and metadata addresses", () => {
  for (const ip of [
    "127.0.0.1", "10.1.2.3", "192.168.1.1", "172.16.0.1", "169.254.169.254", "0.0.0.0", "100.64.0.1", "::1", "fc00::1", "fe80::1", "::ffff:127.0.0.1",
    "0:0:0:0:0:ffff:a9fe:a9fe", "::0:ffff:7f00:1", "0:0:0:0:0:ffff:a00:1",
    "64:ff9b::a00:1", "64:ff9b:1:a00:0:100::", "2002:a9fe:a9fe::",
  ]) {
    assert.equal(isBlockedIp(ip), true, ip);
  }
  assert.equal(isBlockedIp("1.1.1.1"), false);
  assert.equal(isBlockedIp("8.8.8.8"), false);
  assert.equal(isBlockedIp("64:ff9b::808:808"), false);
  assert.equal(isBlockedIp("64:ff9b:1:808:8:800::"), false);
  assert.equal(isBlockedIp("2002:808:808::"), false);
  assert.equal(isBlockedIp("0:0:0:0:0:ffff:808:808"), false);
});

test("url shape allows only public http(s)", () => {
  assert.equal(validateUrlShape("https://example.com/pricing").error, undefined);
  assert.ok(validateUrlShape("http://127.0.0.1/").error);
  assert.ok(validateUrlShape("http://169.254.169.254/").error);
  assert.ok(validateUrlShape("file:///etc/passwd").error);
  assert.ok(validateUrlShape("https://user:pass@example.com/").error);
  assert.ok(validateUrlShape("https://example.com:22/").error);
  assert.ok(validateUrlShape("http://localhost/").error);
  assert.ok(validateUrlShape("https://metadata.google.internal/").error);
  assert.ok(validateUrlShape("http://[0:0:0:0:0:ffff:a9fe:a9fe]/").error);
  assert.ok(validateUrlShape("http://[::0:ffff:7f00:1]/").error);
  assert.ok(validateUrlShape("http://[0:0:0:0:0:ffff:a00:1]/").error);
  assert.ok(validateUrlShape("http://[64:ff9b::a00:1]/").error);
  assert.ok(validateUrlShape("http://[2002:a9fe:a9fe::]/").error);
  assert.equal(validateUrlShape("http://[64:ff9b::808:808]/").error, undefined);
  assert.equal(validateUrlShape("http://[2002:808:808::]/").error, undefined);
});

test("public hostnames are looked up and bare private IPs are blocked", async () => {
  const dns = async () => new Response(JSON.stringify({ Answer: [{ data: "1.1.1.1" }] }), { status: 200, headers: { "content-type": "application/json" } });
  for (const host of ["example.com", "cursor.com"]) {
    const result = await resolveAndCheck(host, dns);
    assert.equal(result.error, undefined, host);
    assert.ok(result.addresses.includes("1.1.1.1"), host);
  }
  for (const host of ["127.0.0.1", "169.254.169.254", "10.0.0.1", "::1", "[::1]"]) {
    const result = await resolveAndCheck(host, dns);
    assert.equal(result.error, "That address is not public.", host);
  }
  const privateAnswer = await resolveAndCheck("example.com", async () => new Response(JSON.stringify({ Answer: [{ data: "10.0.0.1" }] }), { status: 200 }));
  assert.equal(privateAnswer.error, "That host resolves to a blocked address.");
});

test("score names concrete fixes and does not invent a listing", () => {
  const result = scoreListing({
    html: "<title>Hi</title><meta name=\"description\" content=\"Short\"><p>Free plan $10/mo</p>",
    llmsStatus: 404,
    llmsText: "",
    listed: null,
  });
  assert.ok(result.score < 100);
  assert.ok(result.checks.find((c) => c.id === "title" && !c.ok).fix.includes("Title"));
  assert.equal(result.listed, null);
  assert.equal(result.checks.find((c) => c.id === "pricing").ok, true);
});
