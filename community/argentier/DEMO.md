# Argentier — 3-minute demo script (hackathon recording)

Goal of the recording: prove it **runs on real Qonto data**, calls the **MCPs
live** (Qonto + Linkup), does **deterministic math**, and produces something
**useful** you'd send today. Record the Claude Code session; keep tool calls
visible on screen.

**Before you hit record**
- Qonto MCP re-authorized (`/mcp` → qonto → authorize), Linkup MCP connected.
- `ANTHROPIC_API_KEY` set. `python3 -m unittest discover -s tests` green.
- Web dashboard running (`cd argentier && npm run dev`) in a browser tab for the finale.

---

### 0:00 – 0:20 · The hook
Say it straight to camera:
> "Ninety percent of small businesses will never hire a CFO. Their Qonto account
> is full of data and nobody to read it. **The statement lies** — it blends
> recurring tools, structural costs and one-off spend into one number. Meet
> Argentier: the CFO they'll never hire."

### 0:20 – 1:15 · OBSERVE + ANALYSE — real data, deterministic math
In Claude Code, run the skill on the **real account**:
> `/audit` (or: "Argentier, audit my Qonto account")

On screen, let these land and **point at them**:
- The live `mcp__qonto__get_organization` and `mcp__qonto__list_transactions`
  tool calls — "this is my real account, read-only."
- `python3 engine.py …` running — "the model labels; **this** does every euro,
  so nothing is hallucinated and every number is auditable."
- The headline: **"You can recover ≈ X €/year"**, and the 3-natures split
  (pilotable / structurel / ponctuel / perso). "My true controllable run-rate,
  not my statement."

### 1:15 – 2:05 · BENCHMARK — live, sourced, dated (Linkup MCP)
> "Optimizing means comparing. With my green light, it benchmarks the top tools
> on the live web."

Approve the benchmark. Show the `mcp__linkup__linkup-search` call firing, then
the recommendation card:
> "Ringover today vs. the market — **$21 / $44 per user/month, sourced from
> ringover.com, dated 2026** — that's a real, verifiable saving, not a guess."

Emphasize: only the merchant name + category left the machine (rule 3), and the
saving is `engine.py` math, not the model's.

### 2:05 – 2:40 · GATE — a letter you'd actually send
Open the file Argentier just wrote in `drafts/`:
> "It drafts the renegotiation letter, **citing those dated prices**, ready to
> send — but it sends nothing. I approve, I send. Argentier prepares, I decide."

### 2:40 – 3:00 · The proof loop + the finale
> "In 30 days, `/verify` re-reads the account and **proves** the money actually
> dropped. Operator acts, Analyst explains — **Argentier optimizes**."

Flash the web dashboard (simulator + sourced letters) for one beat, then land:
> "**The CFO your business will never hire.**"

---

## What to make sure is visible on screen
- [ ] Real `mcp__qonto__*` tool calls (read-only) on a real account
- [ ] `engine.py` running — deterministic euros
- [ ] Real `mcp__linkup__linkup-search` call returning a **dated, sourced** price
- [ ] A ready-to-send letter in `drafts/` citing that price
- [ ] The headline €/year figure and the 3-natures split
