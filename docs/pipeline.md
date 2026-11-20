# Pipeline

Times in this note are Pacific (America/Los_Angeles). The refresh workflow has no schedule of its own. It runs when `main` is pushed, when the `auto-rebuild` label is added, or when someone starts it by hand.

## Refreshing generated files on open pull requests

Morning-build pull requests and indexable-page pull requests should carry the `auto-rebuild` label. Create that label once in the repository (a human does this; the workflow does not create labels):

```bash
gh label create auto-rebuild --repo Clampdown-web/agentscout \
  --description "Rebuild generated files when main moves" --color 1d76db
```

Add it only to an open pull request that is ready for review, from a branch in this repository. Drafts are skipped. Forks are skipped. Do not add it to a pull request someone else is updating by hand.

Workflow: `.github/workflows/refresh-pr-builds.yml`

For each labeled pull request:

1. Check out the pull request branch.
2. Run `git merge --no-ff --no-commit origin/main`, then create the merge commit. That is a merge commit (two parents). The workflow never rebases, never force-pushes, and never rewrites history.
3. If every conflict is a generated file, keep main's copy of those files, then run `build_site.py`, `build_lastmod.py`, and `daily_update.py`. The build reapplies the pull request's source and data on top of main. The generated-file list is `is_refresh_generated` in `scripts/guardrails/pages.py`. It includes the guardrail's published HTML and sitemaps (`tools/`, `best/`, `compare/`, and the other public pages), `sitemap*.xml`, `api/*.json`, Pagefind, lastmod and search-index files, catalog snapshots, `cloudflare-mcp-worker/*_snapshot.json`, and `.well-known/*.json`.
4. If any conflict is in a source or data file, the merge is aborted, the branch is left untouched, and one short comment lists the files.
5. Run the morning pipeline's local checks (recheck, predeploy, the local audit, `test_morning_audit.py`, and the publish-gate tests). Push only if they pass. The rebuild commit message is `chore: rebuild generated files on main <shortsha>`.
6. A push made with `GITHUB_TOKEN` does not start `pull_request` or `push` workflows. After a successful push this workflow dispatches `guardrails.yml`, `security.yml`, `gitleaks.yml`, and `codeql.yml` on the new head (`workflow_dispatch` is allowed for `GITHUB_TOKEN`) and waits for them. Those workflows accept a `head_sha` input so they check the refreshed commit. The dispatch inputs are on `main` only after this workflow is merged, so the re-run starts working once that lands.

Runs are serialized. The workflow concurrency group lets one refresh run at a time, and each pull request has its own group so two runs cannot update the same branch. Inside a run, pull requests are refreshed one at a time (`max-parallel: 1`), so two branches are not pushed at once. The job timeout is 120 minutes. `build_site.py` is about 17 minutes, and the rest of the budget covers checkout, cached pip installs, the local checks, and waiting on CI.

### What still needs a human

- Creating the `auto-rebuild` label, and adding or removing it. If it is added while the pull request is still a draft, remove it and add it again after marking the pull request ready, or run the workflow with that pull request number.
- Conflicts in source or data, such as `tools.json` or `tool_rich.json`.
- A failing local check. Nothing is pushed. The comment names the check. The morning pipeline also writes `reports/pipeline-failure-<YYYY-MM-DD>.md`.
- CI that fails after the push. The branch already has the rebuild commit. The comment names the workflow.
- Merging. This workflow never merges.
- The live network audit (`daily_deep_audit.py --live`). The morning run retries that step once after 300 seconds. The refresh workflow sets `PIPELINE_SKIP=live` because the live audit reads the public site, not the pull request.
- A hand edit in generated HTML that the builders do not reproduce. The rebuild writes what the builders produce. Put the change in source data.

## Morning pipeline

`python3 scripts/morning_pipeline.py` runs, in order: recheck, predeploy (`daily_deep_audit.py --predeploy`), the local audit (`daily_deep_audit.py`), the tests (`test_morning_pipeline.py`, `test_refresh_pr_build.py`, `test_publish_gate.py`, `test_morning_audit.py`), then the live audit.

The first failing step stops the run with a nonzero exit. One file is written, `reports/pipeline-failure-<YYYY-MM-DD>.md`, using the Pacific date. The last stdout line is:

```text
PIPELINE FAILED: <step>: <reason>
```

Recheck stops at its first failing check as well. Later pipeline steps do not run, and nothing is pushed.

Only the live audit is retried. It is the network fetch. On failure the pipeline appends one `RETRY` line to `data/discovery-note.txt`, waits 300 seconds, and runs that step once more. The stamp on that line is Pacific time. A network error from the live fetch is a failed response, so the retry runs. Recheck, predeploy, the local audit, and the tests are not retried.
