# Synthetic capture check

Offline check of a proposed ratings backup. It does not call Cloudflare, read credentials, or write production data.

## What was checked in public docs

Data Studio sends each SQL statement as its own Durable Object request, bills rows read and written, and requires Editor access. Durable Object `sql.exec` cannot run `BEGIN TRANSACTION`. A cursor held across an await is not a snapshot.

`POST /accounts/{account_id}/workers/durable_objects/namespaces/{id}/query/v2` appears in a public Data Studio bug report. The OpenAPI file retrieved on 2026-11-08 does not define that operation or its body. This tool does not send it. `sendProvider()` always throws `remote_disabled`.

Workers KV list/get is a different API. A KV read cannot share a Durable Object transaction. Vote aggregates (`votes:YYYY-wWW`) are separate from rate-limit, salt, and seen keys.

## What the tool will and will not do

`capture()` accepts one in-memory fixture with both tables in a single response, `rows_written` exactly 0, and no truncation cursor. Two responses, a missing `rows_written`, a non-zero `rows_written`, extra columns, or a truncated page throw before any file is written. The archive still says `snapshot_claimed: false` and `provider_snapshot_proven: false`.

The file is AES-256-GCM ciphertext (`ASBK1`). Errors use a code only. Restore loads a fresh local SQLite file, checks the status index, and can reopen that file. Expired `sub:` keys are omitted. A missing submission expiry fails closed. Retention is a `retain_until` timestamp seven days after capture. Nothing here deletes a real archive.

Caps, tested with the injected clock and fixture size: 10,000 records, 32 MiB plaintext, 10 minutes.

## Not a recovery

This does not prove the account can call the API, that one provider response is a snapshot, or that a production import exists. Point-in-time recovery stays on the object and is out of scope. A real capture needs a later owner approval and a documented single-transaction read, or an explicit decision to keep a labeled non-snapshot interval copy.

Run:

```
node --experimental-sqlite --test scripts/recovery-capture/capture.test.mjs
```
