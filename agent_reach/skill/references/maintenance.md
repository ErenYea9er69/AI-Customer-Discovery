# Maintenance

Read this reference when an update fails, the browser will not start, a channel errors, or the user wants to uninstall.

- **Update:** `agent-reach update` upgrades Agent Reach, tools for added channels, and the agent skill; `agent-reach update --check` checks for newer versions without installing. Run only after the user agrees.
- **Status:** `agent-reach doctor --text` reads local status without network access; `agent-reach check <channel> --text` tests live network connectivity and actions (`--search` tests search/jobs only). Successful installation does not guarantee live testing passes.
- **Dedicated Browser:** `agent-reach browser status` checks status, `browser setup` prepares the browser engine and extensions, `browser stop` closes it; if CloakBrowser download fails, run `browser setup --retry-cloak` after repairing network connectivity.
- **Diagnose Failure Stages:** Distinguish dependency downloading, browser connection, authentication, page rendering, and platform rate-limiting; never mislabel a network timeout as expired login.
- **Upstream Tool Errors:** Note the error and version, and run `agent-reach update` once after user consent; never modify upstream tool files manually, and never retry in a loop.
- **Rate Limits & Blocks:** On `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN`, or `BUSY`, stop the current attempt and wait for user resolution; do not reopen windows repeatedly.
- **Keys & Proxies:** `agent-reach configure groq-key | openai-key | gemini-key | anthropic-key | deepseek-key | proxy | github-token | reddit-client-id | reddit-client-secret`; values must be provided directly by the user.
- **Uninstall:** Run `agent-reach uninstall --dry-run` first to show the user what will be removed, then run `agent-reach uninstall` once they confirm. Only files and tools installed by Agent Reach are removed; user files and personal browsers remain untouched.
