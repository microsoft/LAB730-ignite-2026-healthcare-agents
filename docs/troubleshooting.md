# Troubleshooting

Common failures and how to fix them. If something here is wrong or incomplete, please open an issue.

## `uv` install / PATH

`uv`'s installer is user-scope by default: `~/.local/bin` on Linux/macOS, `%LOCALAPPDATA%\uv\bin` on Windows. If `uv --version` reports "command not found" after install, your shell isn't seeing the install directory. On Linux/macOS, add it to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Put that line in your shell's rc file (`~/.bashrc`, `~/.zshrc`, etc.) so it persists. On Windows, restart the terminal — the installer updates `PATH` in the registry but the current session won't see it until you open a new window.

## `uv sync` failure

Usually a transient network error. Re-run `uv sync`. If the error persists, rebuild the environment:

```bash
rm -rf .venv
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

The `.env` file belongs at the repository root, next to `pyproject.toml`. Copy the example and fill in the values your instructor hands out:

```bash
cp .env.example .env
# then open the file and paste in your key and endpoint
```

Run `uv run workshop/check_env.py` to check it. The MCP server reads `.env` on launch. If you edit the file after the server is already running, restart it: `Cmd/Ctrl+Shift+P` → **MCP: Reload Servers**.

## Skill not invoked

Two common causes:

The skill directory name must match the `name:` field in the SKILL.md frontmatter exactly. `write-report-simple` and `write_report_simple` are different names.

The `description:` field is what the agent uses to decide whether to invoke the skill. Vague descriptions get ignored. Type `/` in the Copilot Chat input to see the list of registered skills. If yours isn't there, the file isn't being picked up — check the directory name and frontmatter again.

## Agent skips skills and improvises instead

A different problem from the one above: the skill *is* registered (it shows up under `/`), but the agent answers from its own reasoning instead of invoking it. A common symptom is the Radiology Assistant writing a report straight from its own image read for a prompt like *"Please write a radiology report for samples/mri-brain-lesions/case-056/2017-06-13/series-0018.nii.gz"* without ever calling `write-report-measured`, `write-report-segmentation`, or `write-report-simple`.

This is a model-judgment problem, not a registration problem. Try these fixes in order, from cheapest to most involved.

### 1. Confirm the skill is actually discoverable

Rule out the registration causes first. Type `/` in chat and confirm the skill appears with a clear description. If it doesn't, fix the directory name and frontmatter as described in **Skill not invoked** above — an agent can't invoke a skill it can't see.

### 2. Make the skill descriptions less ambiguous

When several skills could plausibly handle the same request, the agent has to disambiguate — and a weaker model often resolves the tie by doing the work itself. If the report skills all read like "Invoke whenever drafting a brain MRI report," the model has no way to choose.

Tighten each `description:` so it states *when* that specific skill applies:

- `write-report-measured` — "…when the `segment`, `clean_segmentation`, and `describe_lesions` tools are available."
- `write-report-segmentation` — "…when `segment` is available but `clean_segmentation` or `describe_lesions` is not."
- `write-report-simple` — "…fallback when the `medimageparse` tools are not available."

Clear, non-overlapping descriptions make the routing decision obvious.

### 3. Make skill use explicit in the agent's workflow

A workflow with generic verbs ("analyze the image", "draft the report") lets the agent satisfy each step by free-writing. Make the workflow step name the skill: *select a skill → invoke it → return its output*. State the priority order in that step:

```markdown
<workflow>
1. **Identify the case.** Find the image path and any clinical context. If no path is given, ask for one.
2. **Write the report with a report skill.** If the user names a skill, use it. Otherwise use the most capable report skill whose tools are available: `write-report-measured` (`segment`, `clean_segmentation`, and `describe_lesions`), else `write-report-segmentation` (`segment` only), else `write-report-simple`. Do not write the report yourself; return the skill's output (`<confidence>` and `<report>` blocks) unchanged.
</workflow>
```

### 4. Upgrade the agent's model

If the agent still skips skills after the changes above, the model itself is likely the bottleneck. Light models are noticeably worse at the multi-step "discover skills → pick the right one → invoke it" chain. Change the `model:` field in the agent frontmatter to a larger model from the chat model picker, for example:

```markdown
---
name: 'Radiology Assistant'
model: ['GPT-5 (copilot)']
...
---
```

This is probably the highest-leverage change for reliable skill adherence — apply it together with steps 2 and 3 rather than on its own.

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

`Missing environment variables: MIP_MODEL_ENDPOINT, ...` — `.env` hasn't been created or isn't at the repository root. See the `.env not loaded` section above.

HTTP 401 or 403 from the MedImageParse endpoint — wrong or expired API key. Get a fresh key from your instructor and paste it into `.env` at the repository root, then reload the server.

### Check the endpoint without MCP

If MCP won't cooperate, check the client and endpoint directly from the repository root:

```bash
uv run workshop/check_env.py --verbose
```

If this passes but the MCP tools still don't appear in the picker, the problem is in server registration, not the model call — go back to the `@mcp.tool(...)` decorator and the `mcp.json` registration.

### MCP server is not discovered

Trust the lab working directory in VS Code so its MCP server can load automatically and make its tools available in the chat session.

1. Open the lab repository folder in VS Code.
2. Open the Command Palette (`Ctrl+Shift+P` on Windows/Linux, `Cmd+Shift+P` on macOS) and run **Workspaces: Manage Workspace Trust**.
3. Under **Trusted Folders & Workspaces**, select **Add Folder** and choose the lab repository root. Only trust folders whose contents you trust.
4. Start a new Copilot Chat session. If prompted, approve the `medimageparse` MCP server, then confirm its tools appear in the chat tool picker.

### MCP server runs locally but is unavailable in Copilot chat

Copilot's runtime maintains a separate workspace-trust list. Register the repository through Copilot CLI rather than editing its managed configuration:

1. Open a terminal in the repository and start Copilot:

   ```powershell
   Set-Location '\path\to\your-repository'
   copilot
   ```

2. At the folder-trust prompt, select **Yes, and remember this folder for future sessions**. Only do this for repositories you trust.
3. Exit the CLI with `/exit`.
4. In VS Code, run **Developer: Reload Window**, then start a new Copilot chat.

This is Copilot CLI's trust prompt, separate from VS Code's Workspace Trust dialog.
