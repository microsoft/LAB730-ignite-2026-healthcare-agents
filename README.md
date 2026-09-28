# How to Actually Use Foundation Models: From Classification to Agents Learning Lab

**SIIM 2026 Learning Lab.** This repository supports a hands-on lab on building **radiology AI agents** in VS Code with GitHub Copilot. The lab is organized into **three chapters**, each in its own folder under [`chapters/`](chapters/).

Budget about **30 min setup** (do this before arriving) + **60 min content** across the three chapters.

## What you'll build

1. **Chapter 1 — Simple agent + skill** ([`chapters/chapter1-simple-agent/`](chapters/chapter1-simple-agent/)): use a general-purpose LLM with a prompt-based skill to draft structured radiology reports.
2. **Chapter 2 — Using foundation models with agents** ([`chapters/chapter2-foundation-models/`](chapters/chapter2-foundation-models/)): wrap MedImageInsight (zero-shot + a trained adapter) in an MCP server the agent can call.
3. **Chapter 3 — Patient context** ([`chapters/chapter3-knowledge-sources/`](chapters/chapter3-knowledge-sources/)): ground agent outputs in a (synthetic) patient history.

## Workshop layout

- [`chapters/`](chapters/) — one folder per chapter. Each has a `README.md`, a `starter/` skeleton, and an `answer-key/` reference.
- [`samples/`](samples/) — 30 sample chest X-rays (NIH 2017) you can hand to the agent.
- [`eval-results/`](eval-results/) — reference scoring numbers we ship for the part-to-part comparisons.

> The data and patient records in this repo are synthetic or de-identified and are **not for clinical use**. The images are from the [2017 NIH Kaggle dataset](https://www.kaggle.com/datasets/nih-chest-xrays/data). Ground-truth report text in `eval-results/` is model-generated from NIH labels for reference scoring only; it is not radiologist-written.

## Prerequisites

Install and verify the following **before** the workshop. Expect about 30 minutes of setup. Do this before arriving — Wi-Fi and time will be tight on the day.

- **VS Code** (latest stable): https://code.visualstudio.com/
- **GitHub Copilot** and **GitHub Copilot Chat** extensions, signed in with an account that has Copilot access.
- **Git**, and a local clone of this repository opened as your VS Code workspace.
- **uv** (https://docs.astral.sh/uv/) — Python package manager. Install user-scope (no admin required):
  - **macOS / Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

  Then run `uv sync` from the repo root.

### MedImageInsight credentials

Chapter 2 hits a shared MedImageInsight endpoint. Credentials (`MI2_MODEL_ENDPOINT` and `MI2_MODEL_API_KEY`) are distributed at the start of the session. You'll set them up in Chapter 2 Step 1; the working path will be `mcp/medimageinsight-server/.env` at workspace root.

### Quick check

The `workshop/` directory at repo root holds shared Python utilities for the workshop, including a small script to verify your env is healthy.

```bash
uv --version              # 0.x.x
uv sync                   # one-time, ~1–2 min on a good connection
uv run workshop/check_env.py   # expected: "Workshop env OK — Python 3.11"
```

If any command above fails, resolve it before arriving.
