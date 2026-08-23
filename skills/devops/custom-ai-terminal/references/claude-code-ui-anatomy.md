# Claude Code Terminal UI Anatomy (captured from live v2.1.241)

How to make an AI CLI look *exactly* like Claude Code. Captured by running `claude` in a tmux pane (`tmux new-session -d -s cc -x 140 -y 45 'claude'`) and reading `tmux capture-pane -t cc -p` to get the real rendered output — do NOT trust memory or screenshots, capture the live pane.

## Header (startup banner — 3 lines, left-aligned)

```
▐▛███▛█   Claude Code v2.1.241
▝▜██████▀  Opus 5 (1M context) · API Usage Billing
  ▝▝ ▝▝    ~/pentest-cli
```

- Line 1: blocky ASCII logo `▐▛███▛█` (bold accent color) + `  ` + product name + version.
- Line 2: second ASCII row `▝▜██████▀` + `  ` + **model · billing** `"Opus 5 (1M context) · API Usage Billing"`.
- Line 3: `  ▝▝ ▝▝` (third logo row, plain accent, no bold) + `    ` + working directory (dim).

BEAST ported this verbatim: `▐▛███▛█   BEAST Terminal v5.3` / `▝▜██████▀  <model> · API Usage` / `  ▝▝ ▝▝    <cwd>`.

## Thinking indicator: `✻` (U+273B, not the spinner itself)

Claude Code shows `✻ Baked for 5s` while the model reasons. The `✻` is the reference-mark/asterisk-dingbat character. BEAST replaced its `💭 Thinking` panel title with `✻ Thinking`; the response header also uses `✻ <model> · N tokens · $cost`.

## Input prompt: bare `❯ `

Claude Code's prompt is literally `❯ ` (an arrow + one space). No username, no host, no gateway tag. BEAST changed from `❯ beast@tr >` to plain `❯ `.

## Status bar (bottom) — mode symbols

```
  ⏸ manual mode on · ? for shortcuts · ← for agents
```

Mode symbols map:
- `⏸` — manual / normal mode (asks before each tool)
- `⏵⏵` — auto-accept / bypass-permissions mode
- `○` — plan mode

BEAST maps `{"auto": "⏵⏵", "plan": "○", "normal": "⏸"}`. Right side of a status bar should read `<N> tok · $cost · <mm m ss s>`.

## Horizontal rule separators

Claude Code separates sections with a full-width `─────` (═/─ repeated). BEAST uses `console.print("─" * min(console.width, 100), style=dim)`.

## First-run dialogs (in tmux, before the main TUI)

1. Theme picker: `1. Auto ... ❯ 2. Dark mode ✔ ...` — press Enter for default.
2. Workspace trust: `❯ 1. Yes, I trust this folder` — Enter.
3. Settings warning (invalid permission rule) — Enter to Continue.

These appear only on first launch per directory; handle with `tmux send-keys En` + `sleep`.

## Replication checklist (porting to a custom CLI)

- [ ] ASCII logo 3-row header, left-aligned, model + billing on row 2
- [ ] `✻` thinking + `✻ <model> · tokens · cost` response header
- [ ] bare `❯ ` prompt (prompt_toolkit `HTML('<prompt>❯ </prompt>')`)
- [ ] mode symbol in status bar (`⏵⏵`/`○`/`⏸`) + `tok · cost · time`
- [ ] horizontal rule separators between turns