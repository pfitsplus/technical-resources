# Saving a PFITS+ Slack DM locally with Slackdump

[Slackdump](https://github.com/rusq/slackdump) saves your own Slack conversations (messages, threads, and attachments) to your computer, with no admin rights or Slack app needed. These steps save one DM from the PFITS+ Slack workspace (`tcanplanetformation.slack.com`) to a folder of your choice. Tested with Slackdump v4.5.4 (Nov 2026) on this workspace; flags checked against the v4.5.4 source.

> **Before you start:** on paid or Enterprise Slack plans, Slackdump can trigger security alerts to workspace admins. Check your organization's policy first. Save only conversations you're part of, and keep the files somewhere appropriate for their content.

## 1. Install

- **macOS:** `brew install slackdump`
- **Windows / Linux:** download the archive for your OS from the [Releases page](https://github.com/rusq/slackdump/releases) and unpack it anywhere.
  - Windows: if SmartScreen warns about an unknown publisher, click **More info → Run anyway**.
  - macOS (manual download): if Gatekeeper blocks it, allow it under **System Settings → Privacy & Security → Open Anyway**.

Check the install:

```
slackdump version
```

*Windows tip:* create a short alias for the session, then use `sd` in place of `slackdump` below:

```powershell
Set-Alias sd "C:\path\to\slackdump.exe"
```

## 2. Sign in to the PFITS+ workspace

```
slackdump workspace new tcanplanetformation
```

A browser window opens; sign in as usual.

- **Interactive** login works for this workspace. Pick **User Browser** instead if you sign in with "Sign in with Google."
- If Slack opens in a different tab, copy that tab's URL, paste it into the original tab, and press Enter.

Confirm:

```
slackdump workspace list
```

## 3. Find the DM's ID

**Easiest:** in Slack, right-click the DM in the sidebar → **Copy link**. The ID is the last part of the link, e.g., `https://tcanplanetformation.slack.com/archives/D0123456789` → `D0123456789`. DM IDs start with `D`.

**Or from the command line:**

```
slackdump list channels -chan-types im -resolve -no-json
```

- `-chan-types im` lists one-on-one DMs only; use `im,mpim` to include group DMs.
- `-resolve` shows names in place of user IDs.
- `-no-json` prints to the screen without saving a file.

> ⚠️ The online user guide lists `-no-save` here. That flag doesn't exist in v4.5.4 and fails with `flag provided but not defined: -no-save`. Use `-no-json`.

## 4. Dump the DM

```
slackdump dump -o "<output folder>" D0123456789
```

- Attachments download by default (`-files=false` skips them).
- Add `-update-links` to point file links in the JSON at the downloaded copies.
- To limit the date range, add `-time-from 2026-01-01T00:00:00` and/or `-time-to …`. These times are **UTC**.
- If the output folder already exists, Slackdump asks `Overwrite? (y/N)`. Answer `y` only if the folder is empty or you're fine replacing it.

The folder will contain:

```
<output folder>/
  D0123456789.json      messages and threads
  D0123456789/          attachments, named <FileID>-<filename>
```

## 5. Match user IDs to names

The dump stores user IDs (`U…`), not names. To look them up:

```
slackdump list users -no-json
```

Windows: append `| Select-String "U0AAAAAAA|U0BBBBBBB"` to filter. macOS/Linux: append `| grep -E "U0AAAAAAA|U0BBBBBBB"`.

## 6. View or reuse it

- Browse it: `slackdump view "<output folder>"`
- Convert it to a readable Markdown transcript with [`dm2md.py`](dm2md.py) (Python 3.9+, no extra packages), using the IDs from step 5 for names:

  ```
  python3 dm2md.py "<output folder>/D0123456789.json" --name U0AAAAAAA=Alice --name U0BBBBBBB=Bob
  ```

  This writes `D0123456789.md` next to the JSON, with threads, times in US Eastern (change with `--tz`), and links to the saved attachments.
- Rerun step 4 any time to refresh with new messages.

**If you process the JSON yourself:** each thread's `slackdump_thread_replies` list also contains the thread's parent message. Skip entries whose `ts` matches the parent's `ts`, or you'll count those messages twice.

## Troubleshooting

- **`invalid_auth`:** run `slackdump workspace new tcanplanetformation` again.
- **Flag errors:** run `slackdump help <command>` (e.g., `slackdump help list users`). The built-in help matches your version; the online guide can lag behind.
- **Free plan:** Slack's API returns only the last 90 days of history.
