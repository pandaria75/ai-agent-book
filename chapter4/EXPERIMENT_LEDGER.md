# Chapter 4 experiment ledger

This ledger separates execution coverage from the manuscript hypothesis and from external credential availability. `official_complete` is true only when every gate named by the manuscript has substantive real evidence. Mechanism tests and credential probes are retained, but never promoted as successful external executions.

| Experiment | Canonical run | Status | `official_complete` | Manifest SHA-256 |
| --- | --- | --- | --- | --- |
| 4-1 | `active-tool-discovery/validation/experiment_4_1/rerun_20260825` | passed | true | `e5a70588804b8bc1a5ba38c18fe7f4537e8284e62f745d8a6e03401833046dae` |
| 4-2 | `perception-tools/validation/experiment_4_2/real_mcp_20260922T153733Z` | blocked | false | `9a96ef7b2b0195bd174e276a8daf1ac55f25c2c95cab8504550e02c630a73f96` |
| 4-3 | `multimodal-agent/validation/runs/20260729T185433Z-4_2-e028c9db` | passed | true | `1a9cc7bfd48717e73a03ebbde7fd786c7da2811a15267715a3794c0f1220362e` |
| 4-4 | `execution-tools/validation/experiment_4_4/real_mcp_20260923T125311Z` | blocked | false | `f3fc7481d0d44a5dc94ea07f878d92925915c94703a76be9f3a0f78754c75f0f` |
| 4-5 | `collaboration-tools/validation/experiment_4_5/real_mcp_human_20260803_v2` | blocked | false | `9fae8eadec1f9583ba03e21df5c8bc660cc8bec2ba328cf304bcaa0039bd97a3` |

> **Numbering.** Chapter 4 renumbered its experiments when the “too many tools” section moved ahead of the
> three tool categories: active tool discovery 4-5 → 4-1, perception 4-1 → 4-2, multimodal 4-2 → 4-3,
> execution 4-3 → 4-4, collaboration 4-4 → 4-5. Run directories under `validation/` were renamed to match,
> but the sealed manifests and receipts inside them were left byte-identical, so every hash below still
> verifies against the file it was computed from. Receipts written before the renumber therefore still
> quote the old `experiment_4_N` paths and the old experiment label; that is a record of the run as it
> happened and is deliberately not rewritten.

> **One recorded hash still does not verify, predating this renumber and left as-is rather than
> silently replaced:** the mailbox experiment that became 6-1 has a manifest that now hashes to
> `5b8befd0…` after its `experiment` field was relabelled 4-5 → 6-1 during the chapter-6 split,
> while both `chapter6/EXPERIMENT_LEDGER.md` and `chapter6/.../latest.json` still record the
> pre-relabel `3f689dfe…`. Its Unipile credential still returns 401, so a re-run cannot lift the
> block; only the hash can be corrected, and that is left to a deliberate, documented recomputation.
> The 4-1 hash that previously matched no file has been resolved by the re-run recorded below.

## Experiment 4-1 — active tool discovery

The canonical campaign `rerun_20260825` uses local Ollama `qwen3:4b`, 127
complete schemas listed by the real perception MCP server, a 50,597-token
schema catalog, a local `all-MiniLM-L6-v2` index, five-schema user-history
injection with a cumulative status bar, and the three exact manuscript tasks in
both arms. All twelve formal gates are true. Both groups selected every
required capability and completed 3/3 tasks, so the manuscript's expected
accuracy/completion improvement was **not observed**: both arms scored 100%.
Active discovery was faster in this run (783.442 versus 3,056.294 seconds,
3.90×) and exposed much less schema text (1,251 initial system tokens per
treatment task plus 8,424 dynamic tokens across the group, versus 50,829 system
tokens per control task).

This campaign replaces `qwen3_4b_exact_v2_20260730T130600Z` as the canonical
run. That earlier run was made with MCP SDK v1 (`server_version` 1.26.0) and its
recorded manifest hash `ce9d6eda…` matched no file left in the directory, so it
could no longer be verified. The runner had also stopped working entirely: the
v2 migration in #630 covered only the perception experiment, leaving this runner
on the v1 `serverInfo` attribute that v2 renamed to `server_info`. Both are fixed
here, and the re-run reproduces the earlier campaign's qualitative finding —
no accuracy uplift, a large speed and schema-exposure advantage. Note that the
run requires `OLLAMA_FLASH_ATTENTION=0`: with flash attention enabled, ollama
0.20.7 crashes its llama runner on Metal when the control arm's ~50K-token
prompt is prefilled. That is a runtime workaround only; no experiment parameter
was changed.

The successful aggregate must not be read as clean treatment behavior. On the
Apple task, Qwen first issued a vague discovery, malformed JSON, an irrelevant
Google search and a real but irrelevant `code_interpreter` call that wrote a
215-byte empty contributor chart; two premature finishes were rejected before
it discovered and executed `yfinance_quote` and `search_news`. The recovered
arXiv task retained two protocol parse errors and a redundant vague discovery.
Those trajectories remain in the canonical receipts.

Failed evidence is also preserved. The first exact campaign
`qwen3_4b_exact_20260730T061700Z` completed but had treatment at only 1/3 tasks
(manifest SHA-256
`e3b98be25fca51e3454e442f2e312ff84aad24c89c2d44a7c1e46628cdbebe09`).
The canonical v2 campaign's first terminal attempt hit real arXiv
429/503/disconnect failures; its final search succeeded only on turn 12, too
late to download. Its failed manifest SHA-256 is
`e18bc4465606087c195a2abafbd375048c2921233bae812ef3bc3f522eb9b86b`.
A bounded same-campaign resume archived that failed summary, manifest and task
receipt, reused the other five completed receipts, then made one fresh real
attempt. With the arXiv client page bounded to the requested three results,
the official endpoint succeeded on its first call and all three PDFs were
downloaded, signature-checked and hashed. No cached result or mock substituted
for either failed attempt.

## Experiment 4-2 — perception MCP

Manuscript gates: a real MCP catalog covering search, multimodal understanding, filesystem operations, public data, and authorized private data.

The canonical campaign is `real_mcp_20260922T153733Z` (2026-09-22), the first
run recorded after the SDK v2 migration: its `catalog_receipt.json` proves an
mcp 2.2.0 client negotiating the stateless `2026-07-28` protocol against a
live `tools/list` of 127 unique tools, and all 46 manifest-listed files verify
against manifest SHA-256 `9a96ef7b…`. Ten of eleven formal gates are true:
search, multimodal, filesystem, and public-data categories all pass, with23
substantive non-simulated successes. Vision calls used the OpenAI-compatible
`mimo-v2.6-pro` endpoint and retained raw provider receipts: `image_analyze`
response `cfe592b7…` (437+212 tokens, 7.558 s) and the `video_analyze` frame
receipt `be463cd8…` (442+153 tokens, 5.697 s, `finish_reason: stop`). OCR read
the fixture marker through Tesseract, local Whisper transcribed the
PowerShell-SAPI-generated speech fixture, the three escape probes were rejected
with `PermissionError` while `outside_witness_unchanged` held, and
`credential_preflight` shows Calendar/Notion credentials genuinely absent.

- Blocked: Google Calendar and Notion. No usable OAuth token or Notion integration credential exists in the environment; both calls fail with `missing_credentials` and can never be promoted to successes. The other nine gates pass, so the campaign status is honestly `blocked`, not `passed`.
- The previous canonical run `real_mcp_dashscope_intl_20260730T070000Z` is retained as prior evidence; its manifest still verifies against its recorded SHA-256 `f93ee0ad9bd1121ed9e7c9d730bbaf85847d03e89c9024487cfdf9f62b8557ab`. It predates the SDK v2 migration (no recorded `mcp_sdk_version`/`protocol_version`) and its vision calls used DashScope international `qwen-vl-max`.
- Failed provenance retained: the first DashScope attempt used the mainland endpoint with an international-region key and received 401; the corrected run used `dashscope-intl.aliyuncs.com`.
- Windows portability, applied before the canonical run: the speech fixture is synthesized with PowerShell `System.Speech` (the macOS `say` dependency is not portable), the OCR image fixture falls back to `C:\Windows\Fonts\arial.ttf`, filesystem mutations reject any drive-anchored path (`Path("/tmp").is_absolute()` is false on Windows), the runner repairs stale user-PATH installs (Tesseract) before spawning the MCP server, and tracked evidence files are pinned byte-exact via `.gitattributes` (`validation/** -text`) after a CRLF→LF restoration whose per-file hashes all verify against their manifests.

## Experiment 4-3 — multimodal processing

Manuscript gates: run the same nontrivial image/PDF and questions through native multimodal, extract-to-text, and tool-on-demand paradigms, retaining real vision calls, tool-use traces, exact-answer quality, latency, usage, and an external judge for free-form output. The canonical run is retained under `multimodal-agent/validation/runs/20260729T185433Z-4_2-e028c9db/`.

## Experiment 4-4 — execution MCP

Manuscript gates: verified file write/edit, terminal timeout and dangerous-command review, sandboxed Python, long-output persistence, Excel operations, external system mutations, and browser/desktop/mobile execution.

The canonical campaign is `real_mcp_20260923T125311Z` (2026-09-23, run on the
Windows host after the SDK v2 migration): its `catalog.json` records 13 tool
schemas (`schema_sha256` `56172624f62c914b…`) served by the real
`execution-tools` MCP server over stdio, and all 34 manifest-listed files
verify against manifest SHA-256
`f3fc7481d0d44a5dc94ea07f878d92925915c94703a76be9f3a0f78754c75f0f`. Ten of
fifteen formal gates are true — the deterministic Python `compile()` and Node
`--check` linters with structured invalid-code rejections; workspace escape
rejection while `outside-witness.txt` held; terminal timeout; a real
mimo-v2.6-pro dangerous-command review that rejected `rm -rf` as an
"irreversible, force-delete operation" with raw provider receipts
(`dangerous_operation_review` 632+667 tokens, 13.641+10.936 s); a Docker
`--network none`, read-only-root sandbox whose network probe failed with
`URLError` exactly as designed; the 260-line output truncated with the
`[省略 … 行]` marker while the immutable full text (2,600 bytes, `9c69930e…`)
was retained; XLSX formulas rendered through LibreOffice and PyMuPDF; a real
postman-echo HTTPS webhook; and real Playwright Chromium navigation with a
hashed screenshot. Failures carry `error_analysis` so the
execute-verify-feedback loop closes as the manuscript specifies. The same-day
campaign `real_mcp_20260923T115618Z` (manifest
`e3dcca31935fd2b3979ed10acfb51793bf88ba4e1c365dcc5d6e5d3504e98332`) ran the
same code and produced the identical `schema_sha256`, cross-checking the
deterministic gates.

- Blocked: five credential/backend gates. Google Calendar (`credentials.json` absent), GitHub PR (no token configured), and the SMTP email tool all fail explicitly with credential errors; `send_email` now reports `credential_status: missing_credentials` behind its two-phase LLM-precheck-then-send design, replacing the earlier runner's hardcoded `real_email_mutation: False` so the email gate carries real evidence of its block. The virtual desktop (Xvfb/xdotool) and AndroidWorld (KVM) backends do not exist on this Windows host, and `environment_capabilities` records `android_active_devices: []`. None of these may be promoted to successes, so the campaign status is honestly `blocked` with `official_complete: false`.
- The previous canonical run `real_mcp_gui_20260802T093657Z` is retained as prior evidence; its manifest still verifies against its recorded SHA-256 `fde8976b91b149a61b7d468f4c825c1bdfdc9da3062cbfa66aaa1fd0f3d1966f`. On the author's KVM host it passed 13/15 gates — PR #605 created through the GitHub execution tool and then safely reused through query-before-mutation idempotency; headful Chromium on Xvfb driven through OS keyboard events with a hashed framebuffer; and a KVM-backed AndroidWorld API-33 emulator that opened Wi-Fi Settings, verified focus, captured pixels, and returned home through ADB input — leaving only Calendar and email blocked there. Its danger reviews used OpenRouter GPT-4.1-mini with raw usage/latency receipts.
- Windows portability, applied before the canonical runs: the code executor no longer hard-codes `executable='/bin/bash'` (CreateProcess failed with WinError 3 on Windows), Docker volume mounts normalize to forward slashes (`shlex.quote` single quotes reached cmd.exe verbatim and produced an invalid spec), LibreOffice is discovered through known install paths when `shutil.which` misses it, the runner's terminal probes use cmd.exe equivalents and honor `REVIEW_PROVIDER`/`REVIEW_MODEL` (the danger reviews ran on the OpenAI-compatible mimo endpoint), and tracked evidence files are pinned byte-exact via `.gitattributes` (`validation/** -text`) after a CRLF→LF restoration of 111 tracked text files whose per-file hashes all verify against their manifests (18 binary files untouched).
- Failed provenance retained: `real_mcp_gui_20260802T093348Z` established the GitHub/desktop/mobile gates but failed the spreadsheet gate because LibreOffice and the Chapter 4 PyMuPDF dependency were missing; the corrected historical run installs/declares both, passes the spreadsheet gate, and reuses the already-open PR instead of creating a duplicate. Two attempts, `real_mcp_20260923T114730Z` and `real_mcp_20260923T115556Z`, died during the SDK v2 API migration (constructor-based handler registration, `serverInfo` → `server_info`) and are kept as 2-file remnants referenced by no test.

## Experiment 4-5 — collaboration MCP

Manuscript gates: sync/async sub-agent lifecycle, messages, cancellation/status, two context-passing strategies, HITL requests with timeout/default behavior, and real multi-channel notification.

- Passed: the canonical v2 run retains six unique Kimi K3 response/usage/latency receipts; real minimal and LLM-generated handoffs; privacy filtering; synchronous and asynchronous completion/status; follow-up messages; cancellation; a conservative timeout; and a live repository-user approval delivered to the same pending MCP request in 1,423.272 seconds within its four-hour response window. The independent validator checks the human/MCP IDs and decision, 55 tool receipts, all 61 manifest hashes, and credential absence.
- Blocked only on delivery: no real SMTP/SendGrid, Telegram, or Slack configuration exists. Credential-free preflights fail explicitly, so `official_complete` remains false even though the human-decision gate is now closed.
- Failed provenance retained: `real_mcp_human_20260803_v1` used a 30-minute live window; the response arrived just after timeout and exposed that an expired request could still be mutated. The failed run preserves the timeout and late-response receipts. The production HITL primitive now rejects late or duplicate responses to terminal requests, with focused regression tests. The earlier `real_mcp_kimi_20260730T063500Z` run also preserves the original too-short async polling failure.
- Windows portability and SDK 2.x migration applied before the local attempts: the live-decision stdin reader no longer calls `select()` on plain descriptors (Windows restricts select to sockets) but polls a non-blocking descriptor against the deadline — a timed-out read leaves no pending I/O, which would otherwise deadlock the stream close; the server entry migrates from the removed `mcp.server.fastmcp.FastMCP` to `mcp.server.mcpserver.MCPServer` (mcp 2.2.0 keeps the `tool()` / `run_stdio_async()` API); the runner reads `server_info`, honors an explicitly configured `COLLAB_PROVIDER`/`OPENAI_MODEL` instead of hardcoding Moonshot so receipts record the model that actually answered, and redacts `DASHSCOPE_API_KEY`/`DASHSCOPE_BASE_URL`/`OPENAI_BASE_URL`; the Excel tools now close every openpyxl/pandas handle (a leaked workbook handle made test cleanup fail with WinError 32 on Windows).
- Experiment-requirement addition: `src/hitl_policy.py` ships the HITL-recognition system prompt (when to request approval vs input vs proceed, with timeout + conservative default) and exposes it as `mcp_assess_hitl_requirement`; the runner exercises it plus a `request_admin_input` timeout probe behind a new `hitl_policy_system_prompt_recognition` gate, and the independent validator pins the model receipts via `--expected-receipts`/`--expected-model` (gate renamed `pinned_real_model_receipts`; defaults preserve the historical kimi-k3 × 6 pin).
- Line-ending governance: the 242 tracked evidence text files of the four retained campaigns had been CRLF-converted by `core.autocrlf=true`, invalidating every recorded SHA-256; restoring LF reproduces all manifest hashes exactly, including this section's anchored v2 digest `9fae8eadec1f9583ba03e21df5c8bc660cc8bec2ba328cf304bcaa0039bd97a3`, and `collaboration-tools/.gitattributes` (`validation/** -text`) now pins the bytes.
- Local attempts retained on this Windows host: `real_mcp_20260926T100753Z` (1-file remnant, died at server startup during the FastMCP migration); `real_mcp_20260926T101024Z` (complete non-interactive cross-check: 37 manifest files, six core gates true, honestly `blocked`); `real_mcp_human_20260926_v3` (a real live approval is recorded — 2,008.905 s inside the four-hour window — but the run is honestly `failed`: the policy probe hit `finish_reason: length` at the old 800-token budget with empty content and the fail-closed parser rejected it; `max_tokens` was then raised to 8000, the same remedy as Experiment 4-4); and `real_mcp_human_20260926_v4` (24-file remnant whose runner was terminated mid-HITL before any decision was recorded). The operator stopped the interactive canonical attempt here, so the canonical row above remains `real_mcp_human_20260803_v2`.
