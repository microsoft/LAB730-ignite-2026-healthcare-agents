# Troubleshooting

Common failures and how to fix them. If something here is wrong or incomplete, please open an issue.

## `uv` install / PATH

`uv`'s installer is user-scope by default: `~/.local/bin` on Linux/macOS, `%LOCALAPPDATA%\uv\bin` on Windows. If `uv --version` reports "command not found" after install, your shell isn't seeing the install directory. On Linux/macOS, add it to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Put that line in your shell's rc file (`~/.bashrc`, `~/.zshrc`, etc.) so it persists. On Windows, restart the terminal — the installer updates `PATH` in the registry but the current session won't see it until you open a new window.

## `uv sync` failure

Usually a stale lock or a transient network error. Re-run `uv sync`. If the error persists, rebuild from scratch:

```bash
rm -rf .venv uv.lock
uv sync
```

## VS Code on a locked-down machine

VS Code ships a [Portable Mode](https://code.visualstudio.com/docs/editor/portable) that requires no installer and no admin rights. Download the `.zip` (Windows) or `.tar.gz` (Linux), or move the `.app` to `~/Applications` (macOS). Create a `data/` folder next to the binary and VS Code keeps all settings and extensions inside it.

## No admin for Python

You don't need system Python. `uv` manages Python entirely in user space:

```bash
uv python install 3.11
```

All workshop commands run via `uv run …`, so nothing touches system Python.

## `.env` not loaded / `MIP_MODEL_API_KEY` missing

The `.env` file belongs at `mcp/medimageparse-server/.env` in your workspace root. You create it in Chapter 2 Setup by copying the example and filling in the values your instructor hands out:

```bash
cp mcp/medimageparse-server/.env.example mcp/medimageparse-server/.env
# then open the file and paste in your key and endpoint
```

The MCP server reads `.env` on launch. If you edit the file after the server is already running, restart it: `Cmd/Ctrl+Shift+P` → **MCP: Reload Servers**.

## Skill not invoked

Two common causes:

The skill directory name must match the `name:` field in the SKILL.md frontmatter exactly. `write-report-simple` and `write_report_simple` are different names.

The `description:` field is what the agent uses to decide whether to invoke the skill. Vague descriptions get ignored. Type `/` in the Copilot Chat input to see the list of registered skills. If yours isn't there, the file isn't being picked up — check the directory name and frontmatter again.

## Agent skips skills and improvises instead

A different problem from the one above: the skill *is* registered (it shows up under `/`), but the agent answers from its own reasoning instead of invoking it. A common symptom is the Radiology Assistant writing a report straight from its own image read for a prompt like *"Please write a radiology report for samples/SYN0417_003.png"* without ever calling `write-report-measured`, `write-report-segmentation`, or `write-report-simple`.

This is a model-judgment problem, not a registration problem. Try these fixes in order, from cheapest to most involved.

### 1. Confirm the skill is actually discoverable

Rule out the registration causes first. Type `/` in chat and confirm the skill appears with a clear description. If it doesn't, fix the directory name and frontmatter as described in **Skill not invoked** above — an agent can't invoke a skill it can't see.

### 2. Make the skill descriptions less ambiguous

When several skills could plausibly handle the same request, the agent has to disambiguate — and a weaker model often resolves the tie by doing the work itself. If the report skills all read like "Invoke whenever drafting a brain MRI report," the model has no way to choose.

Tighten each `description:` so it states *when* that specific skill applies:

- `write-report-measured` — "…when both the `segment_lesions` and `measure_lesions` tools are available."
- `write-report-segmentation` — "…when `segment_lesions` is available but `measure_lesions` is not."
- `write-report-simple` — "…fallback when no vision model is available."

Clear, non-overlapping descriptions make the routing decision obvious.

### 3. Make skill use mandatory and explicit in the agent

Soft guidance like "use available skills when present" is easy for a model to skip. Promote it to a hard rule in `.github/agents/radiology-assistant.agent.md`, and remove generic workflow verbs ("analyze the image", "draft the report") that the agent can satisfy by free-writing.

State that improvising the report is a failure, and give an explicit priority/fallback order:

```markdown
<rules>
- **Always draft reports through a report-writing skill — never improvise the prose yourself.**
  Any request to read a brain MRI or write a report MUST go through one of the report
  skills. Writing a report from your own image read without invoking a skill is a failure.
  Select the skill using this priority order, falling back only if the higher option is
  unavailable or its tool call fails:
  1. `write-report-measured` — preferred when both MedImageParse tools (`segment_lesions`, `measure_lesions`) are available.
  2. `write-report-segmentation` — use if `segment_lesions` is available but `measure_lesions` is not.
  3. `write-report-simple` — final fallback when no vision model tool is available.
</rules>
```

Then rewrite the workflow so the steps name the action — *select a skill → invoke it → return its output* — instead of generic verbs the model can satisfy without a tool call:

```markdown
<workflow>
1. **Identify the case.** Find the image path and any clinical context. If no path is given, ask for one.
2. **Select the report skill** using the priority order in `<rules>`.
3. **Invoke that skill** with the resolved image path. Do not write the report yourself.
4. **Return the skill's output** (`<confidence>` and `<report>` blocks) unchanged.
</workflow>
```

### 4. Upgrade the agent's model

If the agent still skips skills after the changes above, the model itself is likely the bottleneck. Smaller models (e.g. `GPT-5 mini`) are noticeably worse at the multi-step "discover skills → pick the right one → invoke it" chain. Bump the `model:` field in the agent frontmatter to a larger model:

```markdown
---
name: 'Radiology Assistant'
model: ['GPT-5 (copilot)']
...
---
```

This is probabaly the highest-leverage change for reliable skill adherence — apply it together with steps 2 and 3 rather than on its own.

### 5. Restart the chat session

Agent and skill files are read when the session starts. After editing `.agent.md` or `SKILL.md`, start a fresh Copilot Chat session so the changes take effect — edits are not picked up mid-conversation.

## "Radiology Assistant" not in agent picker

The agent file must be at `.github/agents/radiology-assistant.agent.md` at workspace root, not inside a chapter directory. After copying it there, restart the Copilot Chat session — new agent files are not picked up mid-session.

## MCP tool doesn't appear in chat

Open the VS Code Output panel (`View → Output`), then switch the dropdown on the right to **MCP Servers → medimageparse**. The server logs there on launch; Python tracebacks here indicate a syntax error or missing import.

If the panel shows the server started cleanly but the tool still doesn't appear in the chat tool picker, check that the function in `server.py` has the `@mcp.tool(...)` decorator.

### Where the MCP server logs go

If you need the raw log files:

- **macOS:** `~/Library/Application Support/Code/logs/<date>/window<N>/exthost/mcp/`
- **Linux:** `~/.config/Code/logs/<date>/window<N>/exthost/mcp/`
- **Windows:** `%APPDATA%\Code\logs\<date>\window<N>\exthost\mcp\`

The most recent `<date>` folder is the current session. Each server gets its own subdirectory inside `mcp/`.

### Common error signatures

`ModuleNotFoundError: No module named 'X'` — the workshop environment isn't active or `uv sync` didn't run. Re-run `uv sync` from the repo root.

`Address already in use` — a previous MCP server process didn't shut down cleanly. Run `MCP: Reload Servers` (`Cmd/Ctrl+Shift+P`) or restart VS Code.

`KeyError: 'MIP_MODEL_ENDPOINT'` (or any similar env-var error) — `.env` hasn't been created or isn't in the right place. See the `.env not loaded` section above.

HTTP 401 or 403 from the MedImageParse endpoint — wrong or expired API key. Get a fresh key from your instructor and paste it into `mcp/medimageparse-server/.env`, then reload the server.

`NotImplementedError: TODO(mip): ...` — 🚧 placeholder: the MedImageParse or measurement code hasn't landed yet. The tool is wired correctly; it just has nothing behind it.

### Direct-Python fallback

If MCP won't cooperate during the workshop, you can still test the underlying logic by calling the Python directly. The MCP server is a thin wrapper around `segmentation.segment(...)` and `measurement.measure(...)` — both scripts run standalone:

```bash
uv run python mcp/medimageparse-server/segmentation.py samples/SYN0417_003.png
uv run python mcp/medimageparse-server/measurement.py outputs/masks/SYN0417_003__enhancing-tumor.png
```

Add `--help` to either for options (custom `--prompts` for segmentation).

If these scripts work but the MCP tool still doesn't appear in the picker, the problem is in server registration, not the foundation model code — go back to the `@mcp.tool(...)` decorator and the `mcp.json` registration.
