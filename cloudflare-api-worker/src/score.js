/** Score a fetched listing. Pure: no network. */

function textOf(html, re) {
  const m = re.exec(html || "");
  return m ? m[1].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim() : "";
}

function meta(html, name) {
  const re = new RegExp(`<meta[^>]+(?:name|property)=["']${name}["'][^>]+content=["']([^"']+)["']`, "i");
  const re2 = new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+(?:name|property)=["']${name}["']`, "i");
  return textOf(html, re) || textOf(html, re2);
}

export function scoreListing({ html = "", llmsStatus = 0, llmsText = "", listed = null }) {
  const title = textOf(html, /<title[^>]*>([\s\S]*?)<\/title>/i);
  const pitch = meta(html, "description") || meta(html, "og:description");
  const og = meta(html, "og:image");
  const jsonLd = /<script[^>]+type=["']application\/ld\+json["']/i.test(html);
  const pricing = /(?:\$\s?\d|\bpricing\b|\bfree\b|\b\/mo\b|\bper month\b|\bpaid plan\b)/i.test(html.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " "));
  const llms = llmsStatus >= 200 && llmsStatus < 300 && String(llmsText || "").trim().length > 20;
  const checks = [
    { id: "title", label: "Title", ok: title.length >= 15 && title.length <= 70, points: 15, fix: title ? `Title is ${title.length} characters. Aim for about 15–70.` : "Add a <title> that says what the tool is." },
    { id: "pitch", label: "One-line pitch", ok: pitch.length >= 50 && pitch.length <= 160, points: 15, fix: pitch ? `Meta description is ${pitch.length} characters. Aim for about 50–160.` : "Add a meta description that states the one-line pitch." },
    { id: "pricing", label: "Pricing clarity", ok: pricing, points: 15, fix: "Say whether it is free, freemium, or paid, with a price or a link to pricing, in the page text." },
    { id: "og", label: "OG image", ok: /^https?:\/\//i.test(og), points: 15, fix: "Add an og:image meta tag with an absolute https URL." },
    { id: "jsonld", label: "JSON-LD schema", ok: jsonLd, points: 15, fix: "Add a JSON-LD script (SoftwareApplication or Organization) so agents can read the listing." },
    { id: "llms", label: "llms.txt", ok: llms, points: 15, fix: "Publish /llms.txt with a title and links. AgentScout's free llms.txt generator can draft one." },
    { id: "listed", label: "AgentScout listing", ok: !!(listed && listed.slug), points: 10, fix: "This site is not in the AgentScout directory yet. Submit it free, or use Fast-Track ($15) for same-day review." },
  ];
  const score = checks.reduce((n, c) => n + (c.ok ? c.points : 0), 0);
  return {
    score,
    max: 100,
    title,
    pitch,
    checks: checks.map((c) => ({ id: c.id, label: c.label, ok: c.ok, points: c.points, fix: c.ok ? "" : c.fix })),
    listed: listed && listed.slug ? { slug: listed.slug, name: listed.name, page: listed.page } : null,
  };
}
