#!/usr/bin/env python3
"""Catalog, training prose, and package renderer for the 25 business agents.

Every downloadable file is original AgentScout training for the buyer's own
company. Placeholders stay until setup_workspace.py replaces them.
"""
from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent / "pack_src"

STRIPE = {
    "ops": {
        "price": 39,
        "url": "https://buy.stripe.com/cNidRa0uDdNRgNvaDFe7m03",
        "label": "Operations / Monitoring Bot ($39)",
    },
    "seo": {
        "price": 59,
        "url": "https://buy.stripe.com/14A7sMfpx6lp9l3aDFe7m05",
        "label": "SEO & AEO Growth Auditor Bot ($59)",
    },
    "mkt": {
        "price": 59,
        "url": "https://buy.stripe.com/4gM8wQelt11568RaDFe7m06",
        "label": "Market & Launch Intel Bot ($59)",
    },
    "ceo": {
        "price": 69,
        "url": "https://buy.stripe.com/9B69AU2CLh031SB8vxe7m07",
        "label": "CEO Coordinator Bot ($69)",
    },
    "bundle": {
        "price": 149,
        "url": "https://buy.stripe.com/fZueVe5OX7pt1SB6npe7m08",
        "label": "Full 4-Bot bundle checkout ($149)",
    },
}

DEPTS = {
    "sales": "Sales & Outreach",
    "marketing": "Marketing & Content",
    "ops": "Operations & Admin",
    "product": "Product & Data",
}

ICONS = {
    "ledger": "M6 3h9l3 3v15H6zM9 12h6M9 16h4M9 8h3",
    "pen": "M4 20l4-1 11-11-3-3L5 16zM13 6l3 3",
    "target": "M12 12m-8 0a8 8 0 1 0 16 0a8 8 0 1 0-16 0M12 12m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0M12 12h.01",
    "quote": "M7 8h4v4H8a3 3 0 0 0-3 3v1M15 8h4v4h-3a3 3 0 0 0-3 3v1",
    "film": "M4 6h16v12H4zM8 6v12M16 6v12M4 10h4M16 10h4M4 14h4M16 14h4",
    "mail": "M4 6h16v12H4zM4 7l8 6 8-6",
    "star": "M12 3l2.2 6.4H21l-5.2 3.8 2 6.3L12 16.8 6.2 19.5l2-6.3L3 9.4h6.8z",
    "search": "M11 6a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM15 15l5 5",
    "send": "M4 12l16-7-6 16-2-7z",
    "life": "M12 21s-7-4.4-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.6-7 10-7 10z",
    "cal": "M5 5h14v15H5zM5 9h14M8 3v4M16 3v4",
    "inbox": "M4 5h16v14H4zM4 14h4l2 3h4l2-3h4",
    "chart": "M4 19V5M4 19h16M8 16v-4M12 16V8M16 16v-6",
    "share": "M8 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM16 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM16 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM9.7 10.5l4.6-2M9.7 13.5l4.6 2",
    "users": "M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM16 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM4 19c.4-2.4 2.4-4 5-4s4.6 1.6 5 4M14 15.2c1.6.2 3 1.2 3.6 3.3",
    "layout": "M4 5h16v14H4zM4 10h16M10 10v9",
    "megaphone": "M4 10v4h3l8 4V6L7 10zM18 10a3 3 0 0 1 0 4",
    "radar": "M12 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0-4 0M5 12a7 7 0 0 1 7-7M7 19a8 8 0 0 1 10-10",
    "stack": "M12 4l8 4-8 4-8-4zM4 12l8 4 8-4M4 16l8 4 8-4",
    "bag": "M6 8h12l-1 12H7zM9 8V6a3 3 0 0 1 6 0v2",
    "spark": "M12 3l1.4 5.2L18 10l-4.6 1.8L12 17l-1.4-5.2L6 10l4.6-1.8z",
    "coin": "M12 4v16M8 7h6a3 3 0 0 1 0 6H9a3 3 0 0 0 0 6h7",
    "box": "M4 8l8-4 8 4-8 4zM4 8v8l8 4 8-4V8M12 12v8",
    "chat": "M5 6h14v9H8l-3 3z",
    "lang": "M4 6h10M9 6c0 6-3 9-6 10M6 10h6M14 18l3-8 3 8M15.2 16h3.6",
}


def agent(**kwargs):
    kwargs["dept_label"] = DEPTS[kwargs["dept"]]
    rail = STRIPE[kwargs["stripe"]]
    kwargs["price"] = rail["price"]
    kwargs["checkout_url"] = rail["url"]
    kwargs["checkout_label"] = rail["label"]
    return kwargs


AGENTS = [
    agent(
        slug="accountant", title="Accountant", tagline="Bookkeeping and tax prep", dept="ops", stripe="ops",
        color="#60a5fa", icon="ledger", skill_slug="bookkeeping-tax-prep", script="reconcile_ledger.py",
        promise="Close the month with a reconciled ledger, a categorized cash view, and a question list for a licensed tax professional.",
        heuristics=[
            "Match bank lines to invoices and receipts before you invent a category.",
            "A tolerance of a few cents is a match. A round hundred with no document is a question.",
            "Separate money you have collected from money you have earned.",
            "Flag contractor payments for a 1099 conversation. Do not decide the filing.",
            "Put low-confidence rows in a needs-review queue instead of forcing a code.",
            "Build a 13-week cash view from dated inflows and outflows, not from a hope.",
        ],
        steps=[
            ("Read the business profile", "Confirm the legal name, fiscal year, sales-tax states, and who may approve a journal entry for {{YOUR_COMPANY}}."),
            ("Normalize the export", "Run scripts/reconcile_ledger.py on the CSV. Keep the source column so a bank line is never treated as an invoice."),
            ("Three-way match", "Pair each bank line with an invoice or a receipt inside the date window. Unmatched cash sits in needs-review."),
            ("Categorize with a reason", "Use the keyword hint only as a starting code. Write the reason in plain words next to every code you keep."),
            ("Month-end pack", "List accruals, prepaid expenses, and depreciation questions. Do not post them without {{YOUR_OWNER_NAME}}."),
            ("Quarterly estimate checklist", "Summarize profit, large unusual items, and sales-tax or contractor flags. Label the page 'not tax advice'."),
        ],
        routines=[
            ("weekly-reconcile", "0 8 * * 1", "Weekly ledger reconcile", "Reconcile last week's bank export for {{YOUR_COMPANY}}. Return matched rows, the needs-review queue, and one cash warning."),
            ("month-close", "0 9 1 * *", "Month-end close pack", "Draft the month-end close checklist: accruals, prepaids, unmatched cash, and questions for the tax professional. Do not file anything."),
            ("quarterly-estimate", "0 9 1 1,4,7,10 *", "Quarterly estimate reminder", "Prepare the quarterly estimate question list and remind {{YOUR_OWNER_NAME}} this is bookkeeping support, not a filed return."),
        ],
    ),
    agent(
        slug="graphic-designer", title="Graphic Designer", tagline="Ads, posts and thumbnails", dept="marketing", stripe="seo",
        color="#f59e0b", icon="pen", skill_slug="brand-card-system", script="generate_brand_card_spec.py",
        promise="Turn a brand kit into layout specs and an SVG card that keeps color, type, and contrast consistent.",
        heuristics=[
            "One accent color does the pointing. A second accent is noise.",
            "Headline under eight words. Brand name is a signature, not a second headline.",
            "Check ink against background before you export. Aim for a 4.5 contrast ratio on text.",
            "Design the 9:16 story and the 1.91:1 link card from the same tokens, not as unrelated pictures.",
            "Leave a quiet edge of at least 64px so a platform crop does not eat the offer.",
            "Write the image-model prompt after the layout is decided, so the prompt serves the design.",
        ],
        steps=[
            ("Capture the kit", "Record hex colors, display font, text font, and logo clear-space for {{YOUR_COMPANY}} in context/business-profile.md."),
            ("Emit the spec", "Run scripts/generate_brand_card_spec.py. Read the contrast pairs before you approve a background."),
            ("Pick the ratio", "Choose feed portrait, story, landscape ad, or thumbnail. Do not stretch one file into all four."),
            ("Write three concepts", "Each concept gets a one-sentence rationale: what the eye hits first and why."),
            ("Export checklist", "Confirm safe margins, readable type at phone size, and a file name that includes the ratio."),
        ],
        routines=[
            ("weekly-asset-batch", "0 10 * * 2", "Weekly social asset batch", "Produce this week's card specs for {{YOUR_COMPANY}} from the approved brand tokens. Draft only. Do not publish."),
        ],
    ),
    agent(
        slug="lead-gen", title="Lead Gen Agent", tagline="Finds qualified leads daily", dept="sales", stripe="mkt",
        color="#34d399", icon="target", skill_slug="icp-lead-scoring", script="score_leads_pipeline.py",
        promise="Score prospects you already have, drop duplicates, and hand sales a CSV of people worth a human review.",
        heuristics=[
            "Write the ICP and the anti-ICP before you score a single row.",
            "A buying signal beats a big employee count.",
            "Dedupe on the domain, not the display name.",
            "An email that fails a basic shape check does not enter the send queue.",
            "Log where the row came from. A lead without a source is a rumor.",
            "Cap the daily batch. A smaller list that sales will touch beats a dump.",
        ],
        steps=[
            ("Lock the rubric", "Confirm employee band, buyer titles, industries, and disqualifiers for {{YOUR_COMPANY}}."),
            ("Score the file", "Run scripts/score_leads_pipeline.py. Read the reason codes, not only the total."),
            ("Drop duplicates", "Keep the richest row when two lines share a domain."),
            ("Separate nurture from discard", "40-59 points can get a softer offer. Under 40 leaves the queue."),
            ("Optional enrichment", "If columns are empty, a person may use a paid vendor such as Apollo, Explorium, or LeadMagic. This package does not call them."),
            ("Export", "Write the qualified CSV and stop. {{YOUR_OWNER_NAME}} decides who gets an email."),
        ],
        routines=[
            ("daily-lead-batch", "0 8 * * 1-5", "Daily qualified lead batch", "Score today's prospect file for {{YOUR_COMPANY}}. Cap the qualified list. Do not email anyone."),
            ("weekly-icp-refresh", "0 11 * * 5", "Weekly ICP refresh", "Compare wins and losses this week and propose one ICP edit for {{YOUR_OWNER_NAME}} to accept."),
        ],
    ),
    agent(
        slug="copywriter", title="Copywriter", tagline="Captions, emails, sales pages", dept="marketing", stripe="seo",
        color="#2dd4bf", icon="quote", skill_slug="conversion-copy-audit", script="audit_sales_copy.py",
        promise="Draft and edit offers with a clear problem, proof, and a single next step.",
        heuristics=[
            "Name the reader's situation before you name the product.",
            "PAS for a pain the buyer already feels. AIDA when they are still browsing.",
            "One claim, one proof, one button above the fold.",
            "Replace a vague intensifier with a number, a noun, or a customer sentence.",
            "Read the line aloud. If you run out of breath, split the sentence.",
            "A headline test needs a hypothesis, not three random puns.",
        ],
        steps=[
            ("Collect the voice", "Pull phrases customers already use from reviews or call notes for {{YOUR_COMPANY}}."),
            ("Draft three headlines", "Each headline gets a hypothesis: who it selects and what it promises."),
            ("Audit the draft", "Run scripts/audit_sales_copy.py. Fix weasel words and any missing proof before you polish tone."),
            ("Handle objections", "Write the objection in the customer's words, then the answer under it."),
            ("Stop at a draft", "Do not publish the page. Hand it to {{YOUR_OWNER_NAME}} with the readability number."),
        ],
        routines=[
            ("copy-pass", "0 9 * * 3", "Midweek copy pass", "Audit the live hero and one email for {{YOUR_COMPANY}}. Return a revised draft and the score. Do not publish."),
        ],
    ),
    agent(
        slug="video-editor", title="Video Editor", tagline="Cuts reels and shorts", dept="ops", stripe="ops",
        color="#a78bfa", icon="film", skill_slug="shortform-cut-captions", script="format_captions_and_cuts.py",
        promise="Turn a transcript into captions, a silence cut list, and a 9:16 storyboard.",
        heuristics=[
            "The first three seconds must contain a change, a number, or a question. A logo card does not count.",
            "Cut filler words and dead air. Keep the breath that makes a sentence human.",
            "Captions are a script, not a dump of every false start.",
            "Burned-in captions stay inside the safe center so interface buttons do not cover them.",
            "Music needs a license note. Silence is better than a track you cannot name.",
            "One video, one job. Do not hide a second offer in the last second.",
        ],
        steps=[
            ("Mark the hook", "Read the opening three seconds. If it is a greeting, rewrite the first line before you edit."),
            ("Build captions", "Run scripts/format_captions_and_cuts.py to emit SRT, VTT, and the gap list."),
            ("Write the cut list", "Hand the ffmpeg hint to the editor. Do not render on a machine you have not been given."),
            ("Storyboard 9:16", "Three beats: interrupt, proof, next step. Note the on-screen text for each."),
            ("Thumbnail brief", "One face or one object, four words or fewer, high contrast."),
        ],
        routines=[
            ("caption-pass", "0 15 * * 1-5", "Weekday caption pass", "Format captions and a cut list for the latest transcript from {{YOUR_COMPANY}}. Draft only."),
        ],
    ),
    agent(
        slug="outreach-agent", title="Outreach Agent", tagline="Cold emails and follow-ups", dept="sales", stripe="mkt",
        color="#22d3ee", icon="mail", skill_slug="cold-email-sequence", script="lint_outreach_sequence.py",
        promise="Draft a short, specific sequence and lint it before anyone hits send.",
        heuristics=[
            "Under 125 words. One ask. One real detail from the prospect, not a mail-merge compliment.",
            "Space steps two to four days apart. A next-day bump looks desperate.",
            "Write the reply path: interested, not now, out of office, unsubscribe.",
            "Spam-trigger words are a smell. Specifics send better than urgency.",
            "SPF, DKIM, and DMARC are readiness checks, not a guarantee of the inbox.",
            "CAN-SPAM still wants a real postal address and a way to stop mail.",
        ],
        steps=[
            ("Pick the signal", "Open with the hiring post, the new location, or the page change. If you cannot name it, do not write the email."),
            ("Draft four steps", "First note, proof bump, different angle, close-the-file. Each has one question."),
            ("Lint", "Run scripts/lint_outreach_sequence.py. Fix every issue it prints."),
            ("Deliverability list", "Confirm the From domain, alignment, and the complaint habit before a new mailbox sends volume."),
            ("Approval", "{{YOUR_OWNER_NAME}} approves the batch. The agent does not send."),
        ],
        routines=[
            ("daily-draft-queue", "30 8 * * 1-5", "Daily outreach drafts", "Draft today's approved batch for {{YOUR_COMPANY}} and lint it. Leave it unsent."),
            ("reply-triage", "0 13,17 * * 1-5", "Reply intent pass", "Classify replies as interested, not now, out of office, or unsubscribe. Draft responses. Do not send."),
        ],
    ),
    agent(
        slug="google-review-replier", title="Google Review Replier", tagline="Replies to every review", dept="ops", stripe="ops",
        color="#818cf8", icon="star", skill_slug="review-reply-desk", script="generate_review_replies.py",
        promise="Draft a specific public reply for every review and a private path for anything serious.",
        heuristics=[
            "Reply inside two days. A late thank-you still beats silence, but the habit is daily.",
            "Use the name and one detail they actually wrote.",
            "A keyword may appear once if it fits. Stuffing the city into every sentence reads as spam.",
            "Never offer a perk to change, delete, or post a review.",
            "Safety, health, and legal comments leave the public thread immediately.",
            "Ask happy customers for a review without gating it on a positive score.",
        ],
        steps=[
            ("Sort by severity", "Run scripts/generate_review_replies.py. P0 drafts escalate before the thank-you notes."),
            ("Edit the thank-you", "Add the detail the script could not know. Cut any incentive language."),
            ("Edit the recovery", "Apologize for the experience you can see. Move the fix to {{YOUR_SUPPORT_EMAIL}}."),
            ("Track velocity", "Note how many reviews arrived and how many still lack a draft."),
            ("Monthly themes", "Group repeated complaints so operations can fix the cause, not only the wording."),
        ],
        routines=[
            ("daily-review-drafts", "0 9 * * *", "Daily review replies", "Draft replies for new reviews of {{YOUR_COMPANY}}. Do not post them."),
            ("monthly-themes", "0 10 1 * *", "Monthly review themes", "Summarize repeated themes and the response time. No public posts."),
        ],
    ),
    agent(
        slug="seo-specialist", title="SEO Specialist", tagline="Gets you ranking on Google", dept="marketing", stripe="seo",
        color="#fb7185", icon="search", skill_slug="seo-aeo-site-audit", script="seo_site_audit.py",
        promise="Audit findability for humans and answer engines: titles, schema, internal links, and a plain llms.txt plan.",
        store_note="Checkout for a single SEO Specialist uses the SEO & AEO Growth Auditor payment link. The downloadable package is a general-purpose auditor for the buyer's own site.",
        heuristics=[
            "One page, one query family. Two URLs chasing the same query need a canonical decision.",
            "Title and H1 may rhyme. They should not be copies if the title can carry the specific modifier.",
            "JSON-LD must match the visible name, price, and organization.",
            "Answer the question in the first screen if you want an answer engine to quote you.",
            "Internal links use the words a buyer would type, not 'click here'.",
            "Do not invent Core Web Vitals. Say 'not measured' until field data exists.",
        ],
        steps=[
            ("Crawl the file you have", "Run scripts/seo_site_audit.py on a saved page or one URL {{YOUR_OWNER_NAME}} names."),
            ("Fix the index basics", "Title length, meta description, single H1, canonical, and image alts come first."),
            ("Check the entity", "Organization or product JSON-LD uses the same name as the page heading."),
            ("Map queries to pages", "List the query, the URL, and any second URL that competes with it."),
            ("Write llms.txt notes", "List the pages a model may quote and the pages it should skip."),
            ("Local NAP", "If the business has a location, name, address, and phone must match the profile."),
        ],
        routines=[
            ("weekly-seo-crawl", "0 7 * * 1", "Weekly SEO and AEO audit", "Audit the priority URLs for {{YOUR_COMPANY}}. Report issues only. Do not change the live site."),
            ("monthly-query-map", "0 8 1 * *", "Monthly query map", "Refresh the query-to-page map and the cannibalization list."),
        ],
    ),
    agent(
        slug="email-marketer", title="Email Marketer", tagline="Newsletters that sell", dept="marketing", stripe="seo",
        color="#f472b6", icon="send", skill_slug="newsletter-issue-score", script="score_newsletter_issue.py",
        promise="Shape a weekly issue, score the subject and preview, and keep the list clean.",
        heuristics=[
            "One story per issue. A second offer belongs next week.",
            "The preview text finishes the subject. It does not repeat it.",
            "Write the plain-text twin with the same links.",
            "Segment by behavior you measured, not by a persona you like.",
            "A win-back is one honest note to quiet readers, then a sunset.",
            "Unsubscribe is a feature. Hide it and you buy complaints.",
        ],
        steps=[
            ("Pick the segment", "Name who receives this issue and why they are in the file."),
            ("Draft subject pairs", "Two subjects, one preview, one body."),
            ("Score it", "Run scripts/score_newsletter_issue.py and fix generic subjects and missing unsubscribe links."),
            ("Check the links", "Every HTML link exists in the plain-text twin."),
            ("Schedule only after approval", "{{YOUR_OWNER_NAME}} picks the winner subject."),
        ],
        routines=[
            ("weekly-issue", "0 9 * * 2", "Weekly newsletter draft", "Draft and score this week's issue for {{YOUR_COMPANY}}. Do not schedule it."),
            ("monthly-hygiene", "0 9 1 * *", "List hygiene note", "List subscribers quiet for 90 days and propose a sunset. Do not delete them yourself."),
        ],
    ),
    agent(
        slug="customer-support", title="Customer Support", tagline="Answers customers 24/7", dept="ops", stripe="ops",
        color="#fb923c", icon="life", skill_slug="support-ticket-triage", script="triage_support_tickets.py",
        promise="Triage tickets against the written policy, draft a macro, and route anything dangerous to a person.",
        heuristics=[
            "Answer from the knowledge base. If it is not written, say you do not know and escalate.",
            "Safety and legal language is P0 even if the tone is calm.",
            "Refunds follow the policy in the business profile. Do not invent a goodwill exception.",
            "Tell the customer when the next update will come. Then meet that time.",
            "A macro is a starting paragraph, not a paste that ignores their order number.",
            "Weekly top issues become documentation, not a longer inbox.",
        ],
        steps=[
            ("Classify", "Run scripts/triage_support_tickets.py. Trust P0 over the rest of the queue."),
            ("Cite the policy", "Quote the refund, exchange, or warranty line you are using."),
            ("Draft the macro", "Acknowledge, answer or escalate, and name the next update window."),
            ("Route", "Owner for safety. Billing macro for refunds. Knowledge base for how-to."),
            ("Log the gap", "If you had no article, add the question to the weekly gap list."),
        ],
        routines=[
            ("hourly-triage", "15 * * * *", "Inbox triage", "Triage new tickets for {{YOUR_COMPANY}}. Draft replies. Send nothing."),
            ("weekly-gaps", "0 16 * * 5", "Weekly knowledge gaps", "List the questions that had no article and propose the titles."),
        ],
    ),
    agent(
        slug="appointment-setter", title="Appointment Setter", tagline="Books calls on your calendar", dept="sales", stripe="ops",
        color="#38bdf8", icon="cal", skill_slug="call-briefing-slots", script="build_call_briefing.py",
        promise="Qualify quickly, offer a few real slots in the prospect's timezone, and prep the caller.",
        heuristics=[
            "Answer a new lead inside five minutes while the context is still warm.",
            "Qualify before you offer the calendar. A meeting with no problem is a courtesy, not a pipeline.",
            "Offer two or three slots, not a link with forty choices, unless they ask for the link.",
            "Show times in their zone and repeat the zone name in the sentence.",
            "Remind at 24 hours and 1 hour. One reschedule note after a no-show, then stop.",
            "Leave buffer between calls so the briefing can be read.",
        ],
        steps=[
            ("Qualify", "Confirm problem, timing, and who decides. Stop if the anti-ICP matches."),
            ("Propose slots", "Run scripts/build_call_briefing.py with their offset."),
            ("Confirm", "Restate the time, the zone, and the single goal of the call."),
            ("Brief the owner", "Give {{YOUR_OWNER_NAME}} the notes and the first question to ask."),
            ("Reminders", "Queue the 24-hour and 1-hour notes. Do not send until the booking is real."),
        ],
        routines=[
            ("reminder-sweep", "0 8 * * *", "Reminder and no-show sweep", "List calls in the next 24 hours and no-shows from yesterday for {{YOUR_COMPANY}}. Draft the notes. Do not send."),
        ],
    ),
    agent(
        slug="personal-assistant", title="Personal Assistant", tagline="Runs your inbox and diary", dept="ops", stripe="ops",
        color="#c084fc", icon="inbox", skill_slug="daily-exec-briefing", script="daily_exec_briefing.py",
        promise="Turn the inbox and calendar into a morning brief with conflicts called out.",
        store_note="Checkout for a single Personal Assistant uses the Operations / Monitoring Bot payment link. The package itself runs the buyer's inbox and diary, not a monitoring product for any other company.",
        heuristics=[
            "Do, schedule, delegate, defer. Urgent and unimportant is a delegation, not a crisis.",
            "Never delete mail. Archive only when the owner has said that folder is safe.",
            "A conflict is two holds that overlap. Propose a move. Do not decline either.",
            "The brief leads with the one decision that cannot wait.",
            "Meeting prep is a page of questions, not a biography of the guest.",
            "Travel items stay on a checklist until a confirmation number exists.",
        ],
        steps=[
            ("Collect the day", "Inbox items, calendar holds, and open trips for {{YOUR_OWNER_NAME}}."),
            ("Sort", "Run scripts/daily_exec_briefing.py."),
            ("Write the brief", "Five lines: decision, conflicts, waiting-on, today's meetings, travel gaps."),
            ("Prep the next meeting", "Goal, their last ask, and the question that would make the meeting useful."),
            ("Track follow-ups", "Anything promised gets an owner and a date."),
        ],
        routines=[
            ("morning-brief", "0 7 * * 1-5", "Morning briefing", "Write the morning brief for {{YOUR_OWNER_NAME}} at {{YOUR_COMPANY}}. Do not delete or send mail."),
            ("friday-review", "0 16 * * 5", "Friday weekly review", "List open loops and next week's first three outcomes."),
        ],
    ),
    agent(
        slug="data-analyst", title="Data Analyst", tagline="Weekly reports and insights", dept="product", stripe="ceo",
        color="#4ade80", icon="chart", skill_slug="kpi-csv-analyst", script="analyze_kpi_csv.py",
        promise="Turn a KPI export into rates, a simple LTV, and a short narrative a founder can read.",
        heuristics=[
            "Define the metric before you compute it. Name the numerator and the denominator.",
            "Check nulls, duplicate months, and a single month that is an order of magnitude off.",
            "An anomaly is a z-score plus a sentence, not a chart decoration.",
            "LTV from ARPU divided by logo churn is directional. Say so.",
            "Three bullets of 'so what' beat a gallery of charts.",
            "If the export and the finance system disagree, stop and show both numbers.",
        ],
        steps=[
            ("Profile the file", "Confirm the month column is unique and the units are currency or counts, not a mix."),
            ("Compute", "Run scripts/analyze_kpi_csv.py."),
            ("Narrate", "What moved, why it might have moved, what you would check next."),
            ("Separate fact from guess", "Label every cause you did not measure as a hypothesis."),
            ("Hand it over", "{{YOUR_OWNER_NAME}} decides what gets repeated in a customer or investor note."),
        ],
        routines=[
            ("weekly-kpi", "0 8 * * 1", "Weekly KPI narrative", "Analyze the latest KPI CSV for {{YOUR_COMPANY}} and write three bullets. Do not email investors."),
        ],
    ),
    agent(
        slug="social-media-manager", title="Social Media Manager", tagline="Plans and posts every day", dept="marketing", stripe="seo",
        color="#34d399", icon="share", skill_slug="social-hook-desk", script="score_social_hooks.py",
        promise="Score hooks, format a native post, and keep a calendar the owner can approve.",
        heuristics=[
            "A hook with a number and a concrete noun beats a tease.",
            "Write for the platform's length. Do not paste the LinkedIn post into a short caption.",
            "Three to five pillars. If you cannot name them, you are improvising.",
            "Reply to real comments before you invent tomorrow's post.",
            "Tag links with a source you can read later.",
            "Best time is the time your own account already earns attention, not a generic chart.",
        ],
        steps=[
            ("Score the hooks", "Run scripts/score_social_hooks.py on today's options."),
            ("Format the winner", "Thread, caption, or single post inside the character limit."),
            ("Add the link tags", "Source, medium, campaign. Campaign is the offer, not the date alone."),
            ("Queue, don't post", "{{YOUR_OWNER_NAME}} approves the send."),
            ("Note the result", "Tomorrow, record whether the specific hook beat the vague one."),
        ],
        routines=[
            ("daily-hooks", "0 8 * * 1-5", "Daily hook score", "Score today's hooks for {{YOUR_COMPANY}} and format the winner. Do not post."),
            ("weekly-calendar", "0 11 * * 5", "Next week's calendar", "Propose five posts across the pillars. Leave them in draft."),
        ],
    ),
    agent(
        slug="recruiter", title="Recruiter", tagline="Screens and shortlists hires", dept="sales", stripe="ops",
        color="#a78bfa", icon="users", skill_slug="candidate-rubric", script="score_candidate_rubric.py",
        promise="Score candidates against a written rubric and write interview questions that test the work.",
        heuristics=[
            "The scorecard exists before the first resume is opened.",
            "Outcomes in the job post beat a pile of tool requirements.",
            "Score evidence you can point to. A vibe is not a point.",
            "Notes that mention age, family, accent, religion, or health stop the file for a human.",
            "Do not auto-reject. A low score is a recommendation to review.",
            "A pass note is short, respectful, and on time.",
        ],
        steps=[
            ("Write the scorecard", "Three to five criteria, each with a weight and the evidence you will accept."),
            ("Score", "Run scripts/score_candidate_rubric.py."),
            ("Read the flags", "Any risky note goes to {{YOUR_OWNER_NAME}} before a status change."),
            ("Draft questions", "Each question asks for a past example tied to one criterion."),
            ("Track the pipeline", "Stage, days in stage, and the next touch. No one sits in silence past the SLA you wrote."),
        ],
        routines=[
            ("daily-pipeline", "30 9 * * 1-5", "Candidate pipeline nudge", "List candidates with no touch in three business days. Draft the next note. Do not send."),
        ],
    ),
    agent(
        slug="web-designer", title="Web Designer", tagline="Builds landing pages", dept="product", stripe="seo",
        color="#60a5fa", icon="layout", skill_slug="landing-page-ux-check", script="check_landing_page_ux.py",
        promise="Lay out a page that fits a phone and makes the next step obvious.",
        heuristics=[
            "Pick a type and a color on purpose. A generic purple gradient is not a brand.",
            "The first screen holds one promise, one proof, and one button.",
            "360px and 390px must not scroll sideways.",
            "Text contrast aims for 4.5 against its background.",
            "Fixed pixel widths wider than the phone are a bug, not a look.",
            "Empty image alts fail the page even if the picture is pretty.",
        ],
        steps=[
            ("Sketch the sections", "Hero, proof, offer, objections, final button. Name what each section must do."),
            ("Check the file", "Run scripts/check_landing_page_ux.py on the HTML."),
            ("Fix overflow", "Replace fixed widths with a fluid layout. Recheck 360 and 390."),
            ("Fix contrast", "Darken or lighten until the pair clears 4.5 for body text."),
            ("Hand off", "List remaining issues. Do not deploy."),
        ],
        routines=[
            ("page-check", "0 14 * * 3", "Landing page UX check", "Run the UX check on the current landing HTML for {{YOUR_COMPANY}}. Report issues. Do not deploy."),
        ],
    ),
    agent(
        slug="meta-ads-agent", title="Meta Ads Agent", tagline="Runs and scales your ads", dept="sales", stripe="mkt",
        color="#fbbf24", icon="megaphone", skill_slug="ad-roas-rules", script="evaluate_ad_roas.py",
        promise="Judge campaigns with written ROAS and CPA rules and a creative matrix you can actually test.",
        heuristics=[
            "Change one cell of the hook, body, or call to action. A new everything is not a test.",
            "Do not kill a campaign that has not spent enough to learn.",
            "Scale only after the efficiency bar and a minimum conversion count.",
            "Fatigue is frequency up and click-through down, together.",
            "Every ad URL carries source, medium, campaign, and content tags.",
            "Special-category ads follow the platform's housing, credit, and employment rules. When unsure, stop.",
        ],
        steps=[
            ("Load the export", "Spend, revenue, impressions, clicks, conversions, frequency."),
            ("Evaluate", "Run scripts/evaluate_ad_roas.py with the targets from the business profile."),
            ("Write the matrix", "Three hooks, three bodies, three calls to action. Mark which cell is live."),
            ("Check tracking", "Open one ad URL and confirm the tags survive the redirect."),
            ("Ask before spend moves", "{{YOUR_OWNER_NAME}} approves every kill or scale."),
        ],
        routines=[
            ("daily-ads", "0 8 * * 1-5", "Daily ad rules check", "Evaluate yesterday's ad export for {{YOUR_COMPANY}}. Recommend only. Do not change spend."),
            ("weekly-creative", "0 11 * * 4", "Weekly creative refresh", "Propose the next three concepts that are not the current hook."),
        ],
    ),
    agent(
        slug="market-researcher", title="Market Researcher", tagline="Tracks your competitors", dept="product", stripe="mkt",
        color="#4ade80", icon="radar", skill_slug="competitor-diff", script="competitor_diff_check.py",
        promise="Compare a competitor on price and features with a source URL and a date on every claim.",
        store_note="Checkout for a single Market Researcher uses the Market & Launch Intel payment link. The package compares the buyer's own competitors from files they provide.",
        heuristics=[
            "No source URL, no claim. A memory of a pricing page is not a source.",
            "Date the snapshot. A price from last quarter is history, not their offer.",
            "Diff features as a set. Marketing adjectives are not features.",
            "If they are cheaper, say who that plan is for.",
            "Review mining quotes the review. It does not launder it into your voice.",
            "A launch is a dated change, not a rumor in a chat.",
        ],
        steps=[
            ("Snapshot both sides", "Name, price, feature list, source URL, as-of date."),
            ("Diff", "Run scripts/competitor_diff_check.py."),
            ("Write the matrix", "Rows are jobs to be done. Columns are you and them. Cells are facts."),
            ("Mine reviews", "Group pains only when you can point at the wording."),
            ("Watch list", "The URLs to re-check next week. Nothing else."),
        ],
        routines=[
            ("weekly-diff", "0 9 * * 1", "Weekly competitor diff", "Diff the saved snapshots for {{YOUR_COMPANY}}. Flag missing sources. Do not publish a teardown."),
        ],
    ),
    agent(
        slug="content-strategist", title="Content Strategist", tagline="Plans 30 days of content", dept="marketing", stripe="seo",
        color="#f472b6", icon="stack", skill_slug="thirty-day-calendar", script="generate_30day_calendar.py",
        promise="Lay out 30 days that a buyer can follow from problem to offer, then break each idea into smaller pieces.",
        heuristics=[
            "A pillar owns a cluster. Random topics do not compound.",
            "Map each piece to a buyer stage so the month is not all 'buy now'.",
            "Ready-to-buy stays the minority.",
            "Repurpose after the source piece is good, not before.",
            "Refresh a page that already earns traffic before you start a cousin URL.",
            "A brief names the query, the outline, the sources, and the internal links.",
        ],
        steps=[
            ("Name the pillars", "Three to five. If a sixth appears, it replaces one."),
            ("Generate the month", "Run scripts/generate_30day_calendar.py."),
            ("Promote the best four", "Those become the pieces with a real brief. The rest stay small."),
            ("Write the repurpose matrix", "Post, email, short video, FAQ block."),
            ("Hand the calendar over", "{{YOUR_OWNER_NAME}} deletes anything off-brand before production starts."),
        ],
        routines=[
            ("monthly-calendar", "0 10 1 * *", "30-day calendar", "Draft next month's calendar for {{YOUR_COMPANY}}. Do not publish."),
            ("quarterly-refresh", "0 10 1 1,4,7,10 *", "Decay and refresh list", "List URLs that should be updated before new topics are added."),
        ],
    ),
    agent(
        slug="tiktok-shop-manager", title="TikTok Shop Manager", tagline="Lists and promotes products", dept="marketing", stripe="mkt",
        color="#fb923c", icon="bag", skill_slug="shop-listing-optimizer", script="optimize_shop_listing.py",
        promise="Tighten a product listing, estimate creator commission, and brief a shoppable video.",
        heuristics=[
            "The title says the product and the buyer. Cleverness that hides the noun fails search.",
            "Banned claims stay out even if they would convert.",
            "Four images minimum: pack, in use, contents, scale.",
            "Inventory alerts fire before you promise a creator a week of posts.",
            "Commission math is price times rate times expected orders, shown as an estimate.",
            "Disclosure is on screen and in the caption when a creator is paid.",
        ],
        steps=[
            ("Lint the listing", "Run scripts/optimize_shop_listing.py."),
            ("Fix claims", "Remove anything the product policy would reject."),
            ("Set the reorder point", "If stock is at or under the line, pause promotion."),
            ("Brief the video", "Hand, result, price, spoken shop name, disclosure."),
            ("Approve", "{{YOUR_OWNER_NAME}} publishes. The agent does not."),
        ],
        routines=[
            ("daily-stock", "0 8 * * 1-5", "Inventory alert check", "Check listing stock against the reorder point for {{YOUR_COMPANY}}. Do not change the live listing."),
            ("weekly-listing", "0 11 * * 2", "Weekly listing audit", "Re-lint the priority products and draft title edits."),
        ],
    ),
    agent(
        slug="influencer-scout", title="Influencer Scout", tagline="Finds creators to work with", dept="sales", stripe="mkt",
        color="#818cf8", icon="spark", skill_slug="creator-roi", script="calculate_creator_roi.py",
        promise="Shortlist creators with an engagement check, a cost estimate, and a brief a person can send.",
        heuristics=[
            "Audience match matters more than follower count.",
            "An engagement rate far above the usual range is a review flag, not a verdict.",
            "CPM is price divided by thousands of followers. It is a planning number, not a promise of reach.",
            "ROI uses the orders you are willing to forecast, labeled as a forecast.",
            "The brief includes disclosure, usage rights, and the live URL you will pay on.",
            "You do not contact a creator until the owner approves the shortlist.",
        ],
        steps=[
            ("Score the sheet", "Run scripts/calculate_creator_roi.py."),
            ("Read the flags", "Open the profile yourself before you defend a high or tiny rate."),
            ("Write the brief", "One job, one disclosure line, deliverables, and the usage window."),
            ("Draft outreach", "Short, specific, one ask. No fake familiarity."),
            ("Track the deal", "Price, expected orders, live URL, paid or not."),
        ],
        routines=[
            ("weekly-shortlist", "0 10 * * 3", "Weekly creator shortlist", "Score the creator sheet for {{YOUR_COMPANY}}. Do not email creators."),
        ],
    ),
    agent(
        slug="invoice-chaser", title="Invoice Chaser", tagline="Gets you paid on time", dept="sales", stripe="ops",
        color="#f59e0b", icon="coin", skill_slug="ar-aging", script="aging_ar_report.py",
        promise="Show who owes what, which tone to use, and when to stop and call.",
        heuristics=[
            "Every note includes the payment link and the invoice number.",
            "Tone climbs with age: upcoming, polite, firm, owner. It does not start at a threat.",
            "A written dispute pauses the ladder.",
            "Late fees exist only when the contract says so.",
            "Buckets are current, 1-30, 31-60, 61-90, and older.",
            "Past 30 days, {{YOUR_OWNER_NAME}} sees the note before it goes out.",
        ],
        steps=[
            ("Age the book", "Run scripts/aging_ar_report.py as of today."),
            ("Draft the matching note", "Use the tone the bucket implies. Keep it short."),
            ("Attach the link", "One URL per invoice. Do not make them hunt."),
            ("Pause disputes", "If they wrote that the invoice is wrong, stop the sequence and summarize the dispute."),
            ("Escalate", "90 days and safety issues go to the owner with the history in one page."),
        ],
        routines=[
            ("daily-dunning", "0 9 * * 1-5", "Dunning draft queue", "Draft today's receivable notes for {{YOUR_COMPANY}}. Do not send."),
            ("weekly-aging", "0 9 * * 1", "Weekly AR aging", "Produce the aging buckets and the total open receivable."),
        ],
    ),
    agent(
        slug="product-builder", title="Product Builder", tagline="Creates digital products", dept="product", stripe="ceo",
        color="#a3e635", icon="box", skill_slug="pricing-and-mvp-scope", script="model_product_pricing.py",
        promise="Cut an MVP, model three prices, and write a launch list a small team can finish.",
        store_note="Checkout for a single Product Builder uses the CEO Coordinator payment link. The package scopes the buyer's own product.",
        heuristics=[
            "Write the non-goals in the same sitting as the goals. Scope creep eats the sentence you skipped.",
            "A feature earns its place with reach, impact, confidence, and effort.",
            "Price from cost and a target margin, then sense-check it against the buyer's alternative.",
            "Good, better, and best must be different products, not the same product with a louder adjective.",
            "The success metric has a baseline and a date.",
            "Support email is live before the first charge.",
        ],
        steps=[
            ("Write the PRD skeleton", "Problem, user, success metric, non-goals."),
            ("Score the backlog", "Run scripts/model_product_pricing.py."),
            ("Cut the MVP", "Keep the flagged core. Move the rest to a later list without apology."),
            ("Model the tiers", "Show monthly and the annual equivalent. Name what each tier includes."),
            ("Launch list", "Page, payment, receipt, support path, and the first ten users you will talk to."),
        ],
        routines=[
            ("weekly-scope", "0 9 * * 1", "Weekly scope review", "Re-score the backlog for {{YOUR_COMPANY}} and name anything that snuck into the MVP."),
        ],
    ),
    agent(
        slug="community-manager", title="Community Manager", tagline="Keeps your community active", dept="ops", stripe="ops",
        color="#34d399", icon="chat", skill_slug="community-health", script="community_health_score.py",
        promise="Measure who is quiet, welcome new members, and draft prompts a person can post.",
        heuristics=[
            "A prompt is a question a member can answer from their own week.",
            "New members get a welcome, a day-two nudge, and a day-seven check.",
            "Lurkers are a metric, not a moral failing. Invite once. Do not nag.",
            "Moderate the behavior against the written code. Do not improvise a new rule in public.",
            "Personal data and harassment move to {{YOUR_SUPPORT_EMAIL}}.",
            "FAQ entries come from questions asked twice.",
        ],
        steps=[
            ("Score the export", "Run scripts/community_health_score.py."),
            ("Draft today's prompt", "One question tied to the offer, easy to answer in three lines."),
            ("Onboard the quiet new members", "A short welcome that points at the code of conduct."),
            ("Update the FAQ", "If the score shows the same confusion, add the answer."),
            ("Re-engage", "One note to people dark for a month. Then leave them alone."),
        ],
        routines=[
            ("daily-community", "0 10 * * 1-5", "Daily community draft", "Score health and draft one prompt for {{YOUR_COMPANY}}. Do not post or ban."),
            ("weekly-digest", "0 15 * * 5", "Weekly engagement digest", "Summarize active rate, quiet new members, and FAQ gaps."),
        ],
    ),
    agent(
        slug="translator", title="Translator", tagline="Any language, instantly", dept="marketing", stripe="ops",
        color="#c084fc", icon="lang", skill_slug="i18n-key-parity", script="verify_i18n_keys.py",
        promise="Keep translations aligned to a glossary and prove the keys and placeholders still match.",
        heuristics=[
            "The glossary wins over a prettier synonym.",
            "Do not translate the brand, the domain, or a placeholder token.",
            "A missing key is a bug. An empty string is also a bug.",
            "Placeholders must match the source in order and spelling.",
            "UI strings have a length budget. A correct sentence that overflows the button is not done.",
            "Legal and medical lines wait for a person. Fluency is not a license.",
        ],
        steps=[
            ("Load the glossary", "Terms, do-not-translate list, and formality for {{YOUR_COMPANY}}."),
            ("Check parity", "Run scripts/verify_i18n_keys.py on the locale bundle."),
            ("Adapt idioms", "Replace a joke that only works in the source language with the meaning, not a literal line."),
            ("Check hreflang", "Every locale you ship has a code. Every code you advertise has a page."),
            ("Flag review", "Mark legal, medical, and pricing lines for {{YOUR_OWNER_NAME}}."),
        ],
        routines=[
            ("locale-parity", "0 9 * * 1", "Weekly locale parity", "Verify i18n keys for {{YOUR_COMPANY}}. Report mismatches. Do not publish strings."),
        ],
    ),
]


def _steps(agent: dict) -> str:
    blocks = []
    for i, (title, body) in enumerate(agent["steps"], start=1):
        blocks.append(f"### {i}. {title}\n\n{body}\n")
    return "\n".join(blocks)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def skill_md(agent: dict) -> str:
    name = agent["skill_slug"]
    description = (
        f"{agent['promise']} Use for {agent['title'].lower()} work at "
        "{{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist "
        "before anything is sent, posted, spent, or filed."
    )
    routines = "\n".join(
        f"- `{rid}` at `{cron}`: {title}" for rid, cron, title, _prompt in agent["routines"]
    )
    return f"""---
name: {name}
description: "{description}"
---

# {agent['title']}: {agent['tagline']}

This skill trains an assistant to do **{agent['title'].lower()}** work for **{{{{YOUR_COMPANY}}}}** ({agent['promise']}).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{{{YOUR_OWNER_NAME}}}} instead of guessing.

## When to use

- The task matches "{agent['tagline']}".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

{_bullets(agent['heuristics'])}

## Workflow

{_steps(agent)}

## Output

Return:

1. The decision or draft in plain sentences.
2. The numbers the script printed, unchanged.
3. A needs-review list.
4. The exact approval you still need from {{{{YOUR_OWNER_NAME}}}}.

## Self-check

- The company name in the draft is {{{{YOUR_COMPANY}}}}, not a sample brand left in by accident.
- Every external claim has a source the owner supplied.
- You did not send, post, pay, delete, or file.
- The script exit code was 0 on a dry run before you trusted a new file.
- Support path {{{{YOUR_SUPPORT_EMAIL}}}} is the only public contact you invent.

## Script

```bash
python3 scripts/{agent['script']} --help
python3 scripts/{agent['script']} --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

{routines}

Schedules live in `routines/routines.json`. Times are interpreted in {{{{YOUR_TIMEZONE}}}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
"""


def system_md(agent: dict) -> str:
    return f"""# System role: {agent['title']} for {{{{YOUR_COMPANY}}}}

You are the {agent['title']} for **{{{{YOUR_COMPANY}}}}** ({agent['tagline']}).

{agent['promise']}

## Identity

- Company: {{{{YOUR_COMPANY}}}}
- Domain: {{{{YOUR_DOMAIN}}}}
- Support: {{{{YOUR_SUPPORT_EMAIL}}}}
- Owner: {{{{YOUR_OWNER_NAME}}}}
- Optional MCP endpoint the owner configures: {{{{YOUR_MCP_SERVER_URL}}}}
- Timezone: {{{{YOUR_TIMEZONE}}}}

You work only on this business. You do not arrive with a directory of other products, a scraped catalog, or a preloaded tool index. If a task needs an outside system, ask for an export or for the owner to set {{{{YOUR_MCP_SERVER_URL}}}}.

## Heuristics

{_bullets(agent['heuristics'])}

## Guardrails

- Draft first. Sending, posting, spending, deleting, filing, and price changes wait for {{{{YOUR_OWNER_NAME}}}}.
- Do not invent metrics, reviews, or licenses.
- Do not give legal, tax, medical, or employment-law advice. Prepare questions for a licensed professional when the topic needs one.
- Do not mention a protected trait as a reason for a hiring or credit decision.
- Refuse requests to deceive a customer, a platform, or a reviewer.
- Keep secrets out of the draft. Payment credentials never go in a prompt log.

## Output shape

Use short headings. Lead with the action the owner must take. Then show the evidence. Then list what you refused to do automatically.

## Skill

Follow `skills/{agent['skill_slug']}/SKILL.md` when the task matches this role.

## Script

`scripts/{agent['script']}` is the calculator. Trust its JSON over a mental estimate. Run `--dry-run` when you are demonstrating the workflow.
"""


def agents_md(agent: dict) -> str:
    return f"""# AGENTS.md

This package is the **{agent['title']}** agent for {{{{YOUR_COMPANY}}}}.

- Read `SYSTEM.md` for the role and the guardrails.
- Read `skills/{agent['skill_slug']}/SKILL.md` for the procedure.
- Read `context/business-profile.md` for the offer, the voice, and the constraints.
- Run `python3 scripts/{agent['script']} --dry-run` before you trust a new input file.
- Run `python3 setup_workspace.py --help` to replace placeholders.

Approval gate: do not send, post, spend, delete, file, or change a live price unless {{{{YOUR_OWNER_NAME}}}} has approved that exact draft.

Codex, Cursor, Copilot, Windsurf, and Cline should treat this file as the workspace briefing and the skill file as the task procedure.
"""


def claude_md(agent: dict) -> str:
    return f"""# Claude Code project notes

You are helping **{{{{YOUR_COMPANY}}}}** with the {agent['title']} package ({agent['tagline']}).

1. Read `SYSTEM.md` and `skills/{agent['skill_slug']}/SKILL.md`.
2. Prefer `scripts/{agent['script']}` for scores and checks.
3. Keep edits inside this package unless the owner points at another repo.
4. Show the command you ran and the exit code.
5. Stop before any external side effect.

Placeholders still in braces are unset. Ask rather than invent {{{{YOUR_DOMAIN}}}} or {{{{YOUR_SUPPORT_EMAIL}}}}.
"""


def cursorrules(agent: dict) -> str:
    return f"""# {agent['title']} workspace rules

- Company context lives in context/business-profile.md.
- Follow skills/{agent['skill_slug']}/SKILL.md for this role.
- Python helpers are stdlib only. Do not add a paid SDK.
- Run scripts/{agent['script']} --dry-run after you change inputs.
- Never commit real customer exports. Samples stay synthetic.
- Do not add a tool catalog, a scraper, or a hard-coded directory endpoint.
- Drafts only until {{{{YOUR_OWNER_NAME}}}} approves a send, post, spend, or delete.
"""


def lovable_md(agent: dict) -> str:
    return f"""# Lovable workspace instructions

Upload this ZIP in Lovable at **Workspace settings → Skills → Add → Upload ZIP**.

Skill name: `{agent['skill_slug']}`
Role: {agent['title']} for {{{{YOUR_COMPANY}}}}
Tagline: {agent['tagline']}

When the skill is on:

- Follow `skills/{agent['skill_slug']}/SKILL.md`.
- Read `context/business-profile.md` first.
- Use `scripts/{agent['script']}` for the deterministic check. It supports `--help` and `--dry-run`.
- Replace placeholders with `python3 setup_workspace.py --help` before production drafts.
- Treat {{{{YOUR_MCP_SERVER_URL}}}} as optional and owner-supplied.
- Produce drafts. Do not send email, post publicly, spend money, or delete records from this skill.

Company: {{{{YOUR_COMPANY}}}}
Domain: {{{{YOUR_DOMAIN}}}}
Support: {{{{YOUR_SUPPORT_EMAIL}}}}
Owner: {{{{YOUR_OWNER_NAME}}}}
"""


def business_profile(agent: dict) -> str:
    questions = "\n".join(f"- {title}: what does done look like?" for title, _body in agent["steps"][:4])
    return f"""# Business profile

Fill this in before the {agent['title']} runs. Leave a line blank rather than inventing it.

## Identity

- Company: {{{{YOUR_COMPANY}}}}
- Domain: {{{{YOUR_DOMAIN}}}}
- Support email: {{{{YOUR_SUPPORT_EMAIL}}}}
- Owner: {{{{YOUR_OWNER_NAME}}}}
- Timezone: {{{{YOUR_TIMEZONE}}}}
- Optional MCP server the owner chooses: {{{{YOUR_MCP_SERVER_URL}}}}

## Offer

- What you sell:
- Who it is for:
- Who it is not for:
- Price and what is included:
- Refund or cancellation rule:

## Voice

- Words you use:
- Words you avoid:
- Proof you are willing to show (with source):

## Constraints

- What the agent may draft:
- What requires {{{{YOUR_OWNER_NAME}}}} before it happens:
- Topics that must go to a licensed professional:

## Questions for this role

{questions}

## Sources

Paste file names or URLs the owner provided. Do not add sources the owner has not approved.
"""


def readme(agent: dict) -> str:
    return f"""# {agent['title']} quick start

Package for **{{{{YOUR_COMPANY}}}}**. {agent['promise']}

## 1. Fill the profile

Edit `context/business-profile.md`. Then run:

```bash
python3 setup_workspace.py --help
python3 setup_workspace.py --dry-run
```

Add `--apply` with `--company`, `--domain`, `--support-email`, `--owner-name`, and optionally `--mcp-url` when you are ready to replace placeholders.

## 2. Prove the script

```bash
python3 scripts/{agent['script']} --help
python3 scripts/{agent['script']} --dry-run
```

Both commands exit 0. `--dry-run` prints a JSON report from built-in sample rows.

## 3. Load the skill

| Platform | What to open |
| --- | --- |
| Grok Bot | `SYSTEM.md`, `skills/{agent['skill_slug']}/SKILL.md`, `routines/routines.json` |
| Claude Code | `CLAUDE.md` and the skill file |
| Cursor | `.cursorrules` and `AGENTS.md` |
| OpenAI Codex | `AGENTS.md` |
| Windsurf | `AGENTS.md` |
| Cline | `AGENTS.md` and `.cursorrules` |
| GitHub Copilot | `AGENTS.md` |
| Lovable | Upload the ZIP under Workspace settings → Skills → Add → Upload ZIP. `LOVABLE.md` is the workspace note. |

## 4. Approval

Nothing in this package sends email, posts, spends, deletes, or files. {{{{YOUR_OWNER_NAME}}}} does that after reading the draft.
"""


def license_txt(agent: dict) -> str:
    return textwrap.dedent(f"""\
    SINGLE-ORGANIZATION LICENSE

    This {agent['title']} package is original training material for the buying
    organization, referred to inside the files as {{{{YOUR_COMPANY}}}}.

    One organization may use, modify, and run these files internally for its
    own business. It may not resell the package, publish the skill files as a
    competing template library, or remove this license.

    The files are a workflow aid. They are not legal, tax, medical, accounting,
    or employment advice. The buying organization is responsible for review
    by {{{{YOUR_OWNER_NAME}}}} before any message is sent or any payment is made.

    No third-party directory, catalog, or preloaded tool index is included.
    """)


def notices() -> str:
    return textwrap.dedent("""\
    # Third-party notices

    The prose, checklists, and Python helpers in this package were written for
    this template. They are not copies of another skill library.

    The helpers import only the Python 3 standard library. They do not bundle
    a vendor SDK.

    Industry methods show up as ideas the owner can recognize: plain-language
    offers, contrast math, aging buckets, and permission to email. The wording
    of the workflows is original to this package.

    If the owner later connects a paid data vendor, that account is theirs.
    Nothing here calls one.

    Sample rows inside the scripts are fictional. Do not treat them as customer records.
    """)


def routines_json(agent: dict) -> dict:
    return {
        "timezone": "{{YOUR_TIMEZONE}}",
        "role": agent["title"],
        "company": "{{YOUR_COMPANY}}",
        "routines": [
            {
                "id": rid,
                "cron": cron,
                "title": title,
                "prompt": prompt + " Follow skills/" + agent["skill_slug"] + "/SKILL.md. Draft only.",
                "requires_approval": True,
                "script": "scripts/" + agent["script"],
            }
            for rid, cron, title, prompt in agent["routines"]
        ],
    }


def manifest(agent: dict) -> dict:
    return {
        "name": agent["title"],
        "slug": agent["slug"],
        "tagline": agent["tagline"],
        "version": "1.0.0",
        "skill": f"skills/{agent['skill_slug']}/SKILL.md",
        "script": f"scripts/{agent['script']}",
        "platforms": [
            "grok-bot",
            "claude-code",
            "cursor",
            "openai-codex",
            "windsurf",
            "cline",
            "github-copilot",
            "lovable",
        ],
        "placeholders": [
            "{{YOUR_COMPANY}}",
            "{{YOUR_DOMAIN}}",
            "{{YOUR_SUPPORT_EMAIL}}",
            "{{YOUR_OWNER_NAME}}",
            "{{YOUR_MCP_SERVER_URL}}",
            "{{YOUR_TIMEZONE}}",
        ],
        "price_usd": agent["price"],
        "checkout_url": agent["checkout_url"],
    }


def render_package(agent: dict, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    skill_dir = dest / "skills" / agent["skill_slug"]
    (dest / "scripts").mkdir(parents=True)
    (dest / "routines").mkdir()
    (dest / "context").mkdir()
    (dest / "tests").mkdir()
    skill_dir.mkdir(parents=True)
    files = {
        "SYSTEM.md": system_md(agent),
        "README-QUICKSTART.md": readme(agent),
        "AGENTS.md": agents_md(agent),
        "CLAUDE.md": claude_md(agent),
        ".cursorrules": cursorrules(agent),
        "LOVABLE.md": lovable_md(agent),
        "LICENSE.txt": license_txt(agent),
        "THIRD_PARTY_NOTICES.md": notices(),
        "context/business-profile.md": business_profile(agent),
        f"skills/{agent['skill_slug']}/SKILL.md": skill_md(agent),
    }
    for rel, text in files.items():
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (dest / "routines" / "routines.json").write_text(
        json.dumps(routines_json(agent), indent=2) + "\n", encoding="utf-8"
    )
    (dest / "manifest.json").write_text(json.dumps(manifest(agent), indent=2) + "\n", encoding="utf-8")
    shutil.copy(SRC / agent["script"], dest / "scripts" / agent["script"])
    shutil.copy(SRC / "setup_workspace.py", dest / "setup_workspace.py")
    (dest / "tests" / "README.md").write_text(
        f"# Sample\n\nRun `python3 scripts/{agent['script']} --dry-run` from the package root.\n"
        "Expected exit code: 0. Expected stdout: a JSON object with `dry_run` true.\n",
        encoding="utf-8",
    )
    mcp = {
        "mcpServers": {
            "owner-configured": {
                "url": "{{YOUR_MCP_SERVER_URL}}",
                "note": "Replace this placeholder with the MCP server {{YOUR_COMPANY}} chooses. This file ships without a directory endpoint.",
            }
        }
    }
    (dest / "mcp.json").write_text(json.dumps(mcp, indent=2) + "\n", encoding="utf-8")


def public_cards() -> list[dict]:
    cards = []
    for agent in AGENTS:
        cards.append({
            "slug": agent["slug"],
            "title": agent["title"],
            "tagline": agent["tagline"],
            "dept": agent["dept"],
            "deptLabel": agent["dept_label"],
            "color": agent["color"],
            "icon": agent["icon"],
            "price": agent["price"],
            "stripe": agent["stripe"],
            "checkoutUrl": agent["checkout_url"],
            "checkoutLabel": agent["checkout_label"],
            "skill": agent["skill_slug"],
            "script": agent["script"],
            "promise": agent["promise"],
            "heuristics": agent["heuristics"],
            "routines": [
                {"id": rid, "cron": cron, "title": title}
                for rid, cron, title, _prompt in agent["routines"]
            ],
            "storeNote": agent.get("store_note", ""),
        })
    return cards
