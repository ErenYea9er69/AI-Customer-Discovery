# Sessions & Dedicated Browser

Read this reference when the user wants to log in, log out, switch accounts, or when results return `NEED_LOGIN`.

## Dedicated Browser

- All browser channels share one dedicated browser profile, completely separated from the user's daily Chrome; Agent Reach never modifies or closes the user's personal browser.
- Prefers CloakBrowser engine; falls back to installed local Chrome if download/installation fails, and remembers this fallback. Once network issues are resolved, run `agent-reach browser setup --retry-cloak` to retry.
- `agent-reach add <channel>` automatically sets up Node, OpenCLI, the browser engine, and required extensions using verified versions. On Windows Chrome fallback, the user may need to click "Add to Chrome" once for the helper extension.
- Headless by default (no popup windows). Only `agent-reach login <channel>` opens an interactive window. While open, queries reuse this window without closing it. When the user finishes logging in, queries return to headless execution once the window is closed.
- Closes automatically after 10 idle minutes and reopens on demand; active page actions and Reach calls reset this idle timer. Sessions save periodically during login.
- Supports concurrency: up to 2 concurrent queries per platform, 4 across all platforms; excess queries queue up for up to 2 minutes before returning `BUSY`. Successive searches on the same platform enforce a minimum 10-second gap. Opening login windows, logging out, or reinstalling waits for active queries to complete.
- Commands: `agent-reach browser status` checks status, `browser setup` prepares engines and extensions, and `browser stop` closes the browser.

## Automatic Login Session Reuse

1. When a platform is first accessed, if the user's Chrome is connected via the OpenCLI extension, the site's session cookies (and only that site's cookies) are copied once into the dedicated browser. It never copies passwords, full profiles, or unrelated sites.
2. Once copied, the saved session is reused indefinitely without timed re-copying. Note that valid cookie presence is verified by actual action success.
3. If the user's Chrome lacks the extension, automatic reuse is not possible; Reach relies on existing saved sessions.
4. When multiple local profiles exist: `agent-reach browser profiles` lists them, and `agent-reach browser use <ID>` selects a specific profile without random switching.
5. `agent-reach login <channel> --import-existing` manually triggers session import without opening a browser window.
6. If the user manually logs in via the dedicated window or runs `logout` / `remove`, automatic copying is disabled for that platform to prevent resurrecting explicitly forgotten sessions.

## When Manual Login Is Required

- Only ask the user to log in when an action actually returns `NEED_LOGIN` and the task strictly depends on authentication. A login button on a public webpage does not constitute a login requirement.
- `agent-reach login <channel>` opens the dedicated browser directly to the platform's login page for the user to complete. Never log in on their behalf, never request passwords, and never output cookies.
- If the output contains a `next` field, follow the instructions; certain native channels (such as Xueqiu) require `agent-reach login <channel> --sync` after browser login.
- Once the user confirms completion, re-execute the original action.

## Platform-Specific Details

- **Boss Zhipin:** Site search uses OpenCLI in the shared browser. If job details trigger upstream login warnings, do not ask the user to log in repeatedly.
- **Bilibili:** Session is only supplied to the CLI tool for subtitle fetching; standard search does not initialize browser sessions.
- **Xueqiu:** Community actions require authentication; sessions expire within hours, requiring re-login when expired.

## Logout and Removal

- `agent-reach logout <channel>`: Clears saved credentials and cookies for that platform only; all other sites remain intact.
- `agent-reach remove <channel>`: Removes the channel and clears its stored credentials and caches while preserving other sites.
- Neither command will automatically re-import credentials afterwards.
