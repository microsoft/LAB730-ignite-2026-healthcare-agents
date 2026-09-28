# Workshop on a locked-down machine

You don't need admin/root to do the workshop. This guide covers the no-admin path for the three tools we use: VS Code, uv (Python), and Git.

## VS Code — use Portable Mode

VS Code ships a [Portable Mode](https://code.visualstudio.com/docs/editor/portable) that doesn't need an installer or admin rights. The official docs cover the details; the short version:

- **Windows / Linux:** download the `.zip` (Windows) or `.tar.gz` (Linux) archive, extract to a user-writable directory (e.g., `~/Apps/vscode/`), and create a `data/` folder next to the binary. VS Code keeps settings and extensions inside `data/`.
- **macOS:** download the `.zip`, move `Visual Studio Code.app` to `~/Applications/`, and create a `code-portable-data/` directory next to it (per the official docs).

Open the VS Code binary you just extracted to confirm it launches.

## uv — install user-scope, or fall back to pip

The official installer is user-scope by default — see the [uv install / PATH](troubleshooting.md#uv-install--path) section in the troubleshooting docs for what to do if `uv --version` still fails after install.

If the installer scripts are blocked on your machine entirely (e.g., outbound `astral.sh` blocked, or curl/PowerShell restricted), install uv via pip into a user-writable Python:

```bash
python -m pip install --user uv
```

This puts the `uv` binary in your user's Python `Scripts/` (Windows) or `bin/` (macOS/Linux). If your shell can't find it on PATH, get the full path explicitly and use it directly:

- **macOS / Linux:** `which uv` or `command -v uv`
- **Windows (PowerShell):** `Get-Command uv`
- **Windows (cmd):** `where uv`

Then either add that directory to PATH, or call uv with the full path everywhere the workshop says `uv` (e.g., `/home/you/.local/bin/uv sync` instead of `uv sync`).

## Git — usually already there

Git ships pre-installed on most macOS and Linux corp images. On Windows, [Git for Windows](https://git-scm.com/download/win) has a "single-user install" option in its installer that doesn't need admin. The portable version is also fine.

## Still stuck?

If the no-admin path doesn't work on your machine, use [Codespaces](codespaces.md) — runs the whole workshop in a browser-based VM, no local install needed.
