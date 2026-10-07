# Workshop in a GitHub Codespace

If you can't install tools locally (corporate restrictions or you just want a clean VM), run the workshop in a [GitHub Codespace](https://docs.github.com/en/codespaces). A Codespace is a browser-based VS Code with a pre-built Linux environment — the same Copilot Chat, agent picker, and shell you'd use locally.

## Prerequisites

- A GitHub account with Codespaces enabled (free tier includes 60 hours/month for individuals as of 2026; check your account's [billing page](https://github.com/settings/billing/summary) if in doubt).
- Browser access to https://github.com.

## Setup

1. **Fork the workshop repo.**

   <!-- PLACEHOLDER (Ignite 2026): confirm the public repo name and URL. -->
   Open [microsoft/ignite-workshop-2026](https://github.com/microsoft/ignite-workshop-2026) in your browser, click **Fork** (top right), and fork into your own account.

2. **Create a Codespace on your fork.**

   On your fork's page: **Code** (green button) → **Codespaces** tab → **Create codespace on main**.

   First boot takes 2–5 minutes (provisions a 4-core / 8 GB Linux VM and clones your fork). You land in the editor with the repo already cloned.

3. **Run the standard setup.**

   In the Codespace terminal:

   ```bash
   uv sync
   uv run workshop/check_env.py
   ```

   Expect `Workshop env OK — Python 3.11`. The Codespace base image ships with `uv` pre-installed, so no install step needed.

4. **Sign into Copilot Chat.**

   The Copilot extension prompts for sign-in on first use. Use the same GitHub account that has Copilot access.

5. **Get the MedImageParse credentials from the proctors** and paste them into the `.env` file when you reach Chapter 2 Setup. Same path as the local instructions: `mcp/medimageparse-server/.env`.

## Differences from local

- **File paths** are `/workspaces/ignite-workshop-2026/...` not `/home/you/...`. Anywhere the workshop says "workspace root" applies the same way.
- **Image samples in the chat input** — you reference images by repo-relative path (`samples/SYN0417_003.png`), the same as local.
- **Persistence** — Codespaces auto-stop after 30 min idle but retain state. Your code and `.env` survive restarts.
- **Cost** — a single workshop session is well under 1 hour of Codespace time. After the workshop you can delete the codespace to free your quota.

## Cleanup

When you're done:

- **Stop:** https://github.com/codespaces → click **...** next to your codespace → Stop. (Keeps state but stops billing.)
- **Delete:** same menu → Delete. (Reclaims storage.)
