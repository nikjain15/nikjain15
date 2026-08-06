<div align="center">

# Nik Jain

### I modernize and re-architect 30-year-old, trillion-dollar financial systems into AI-native platforms, and build AI-first products from zero.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/niktechnologist/)
[![X](https://img.shields.io/badge/X-000000?style=flat&logo=x&logoColor=white)](https://x.com/NIkJain1510)
[![Website](https://img.shields.io/badge/Website-nikjain15.github.io-1a1a1a?style=flat)](https://nikjain15.github.io)

</div>

---

I live at the messy edge where AI meets systems that can't go down: modernizing what exists, building what's next. The real value of AI shows up where it's hardest to put it, inside the mission-critical systems a business actually runs on. Decades old, unforgiving, always live. That's where I work, re-architecting legacy finance into AI-native platforms without breaking production, and building AI-first products from zero when a real problem still has no tool for it.

> *I've shipped production AI for over a decade: NLP chatbots cutting resolution time 42% at my own startup, ML engines lifting engagement 30% in asset management today. AI was my job before it was everyone's headline. The models keep getting better; the edge is knowing where they belong.*

The thesis, learned the expensive way: **every AI system needs a deterministic backbone, an eval gate it can fail, and a human approval path for anything irreversible.** Every product below is built on it.

| Product | What it is | Proof | Links |
|---|---|---|---|
| **Conduit** | AI control plane: routing, fallback, eval gates, guardrails, MCP gateway, cost caps | 10 packages · MIT · CI · fail-closed evals | [console](https://nikjain15.github.io/conduit) · [code](https://github.com/nikjain15/conduit) |
| **Penny (FounderFirst)** | Autonomous bookkeeping agent (early access) | 82.5% resolved with zero model calls · 85.6% macro-F1 | [site](https://founderfirst.one) · [code](https://github.com/nikjain15/founderfirst.one) |
| **RoleOS** | Agentic job search over a live index of 1,536 postings across 294 AI-native companies | human-gated outbound, enforced by architecture tests | [live](https://ro.roleos.fyi) · [code](https://github.com/nikjain15/roleos-app) |
| **Pulse** | Project tracking that fills itself in | 934 tests · deterministic guard: 100% must-block recall on a labeled harness | [live](https://pulsecohort.vercel.app) · [code](https://github.com/nikjain15/pulse) |
| **Rally** | Team chat with ungameable recognition | 0.83 P / 0.92 R detection, recall-first by design | [live](https://rally-nikjain15.vercel.app) · [code](https://github.com/nikjain15/rally) |
| **Lossless Modernization** | MIT playbook for money-critical legacy → AI-native | parity-harness templates · costed post-mortem library | [site](https://nikjain15.github.io/lossless-modernization) · [code](https://github.com/nikjain15/lossless-modernization) |
| **Build OS** | Public rubric scoring every product above, nine craft pillars | scores published whether they flatter me or not | [dashboard](https://nikjain15.github.io/build-os/) |

---

## 🏛️ Modernizing a $1.6 trillion investment platform

**Re-architecting a 30-year-old platform that moves $4.5 billion in trades every day into an AI-native cloud system. At this scale, accuracy isn't a feature; it's the whole product.**

**The stakes.** Every output feeds real money movement: trades, positions, NAVs, and dozens of upstream and downstream systems that depend on my numbers. One value off by a rounding error is a reconciliation break, or a real financial one.

**What I own.** The core trading module, end to end: vision → architecture → delivery, as the product lead inside a 50+ team program spanning the US, Ireland, and India.

**The system.** 30 years of business logic locked in **DB2 SQL PL stored procedures and overnight batch jobs**. The rules live in the data layer. Nothing breaks, nothing drifts.

**The hard part, parity to the penny.** Every change produces identical outputs, preserves the logic exactly, and feeds correct data to every up/downstream system. I reconcile new against old, value by value, before go-live.

**My approach.** Strangler-fig decomposition into an **event-driven, saga-based, API-first** cloud architecture, with **AI agents inside workflows that were manual for a generation** — agents draft, humans approve — without loosening the accuracy bar.

| 🎯 Accuracy | ⚡ Batch | 🌍 Scale |
|:---:|:---:|:---:|
| **parity to the penny** | **hours → minutes** | **300K+ advisors** served |

### 🤖 Production AI/ML that moves real numbers

- **A conversational AI agent** (intent recognition, dialogue management, sentiment) triaging issues and running operational workflows end-to-end, released behind eval gates (groundedness, citation accuracy, SME-graded answers) and a human-in-the-loop approval policy.
- **An ML adaptive advisor engine** that decodes behavior across millions of CRM, web, campaign & social touchpoints to personalize journeys and recommendations, lifting qualified-lead volume **+30%** (A/B-validated).
- **A predictive segmentation model** (K-means personas over **300K+ advisors**) powering hyper-targeted outreach, with A/B holdouts validating **+50%** lead-to-opportunity conversion.

### 📈 Strategy & GTM, the full arc from consumer behavior to market entry

- **🪙 Digital-dollar / stablecoin-reserve GTM** *(lead).* Business case for a regulated stablecoin-reserve product: cost-benefit vs. leading reserve-fund financials, systemic-risk (SIFI) evaluation, digital-dollar managed-account capability assessment, presented to senior leadership.
- **Market-opportunity sizing.** Quantified a **~$636B** market opportunity across financial advisors (RIAs, broker-dealers, wirehouses) from industry datasets (SQL/Snowflake).
- **Consumer & advisor behavior.** Mapped end-to-end journeys for **300K+ advisors** into **6 predictive personas** via Jobs-to-Be-Done.
- **Competitive landscape.** Analyzed the **$9 trillion private-equity** market (IRR distribution, vintage analysis, key players) to shape entry strategy.

> → The playbook behind the migration: **[Lossless Modernization](https://github.com/nikjain15/lossless-modernization)**, modernizing money-critical systems without losing a byte of logic or a cent of accuracy. Four stages, seven patterns, parity-harness templates, and a costed post-mortem library of modernizations that failed.

---

## 🚀 Building what's next

*The pillar above proves I can run trillion-dollar AI transformation and strategy. Here I build AI-first products from zero: hands-on, at the frontier, with real guardrails. I lead with the platform they all run on.*

### ⭐ Conduit: *the internal AI platform every product below runs on* &nbsp;·&nbsp; [console →](https://nikjain15.github.io/conduit/) &nbsp;·&nbsp; [code →](https://github.com/nikjain15/conduit)

**One control plane for routing, evals, RAG, agents, and cost, so a new AI use case is a config change, not a rebuild.**

**The problem.** Every AI product re-solves the same plumbing: which model, how to keep it cheap, how to ground it, how to stop it shipping a confidently wrong answer, how to see what it actually costs. Rebuilt per app, it drifts, and both quality and spend become guesswork.

**What I built.** A platform my products plug into, hybrid by design: an embeddable in-process core for low-latency calls, plus a control plane (a console and a gateway that speaks HTTP and MCP) for configuration, evaluation, and cost governance.

**Why it's different**

- **A new use case is a config object, not a code change.** One `UseCaseProfile` composes routing, retrieval, agent, prompts, guardrails, evals, and SLOs. The code ships pluggable registries; config composes them; nothing redeploys.
- **Model-agnostic by design.** Anthropic, Cloudflare Workers-AI, and OpenRouter behind one interface, with a live model catalog and use-case-aware routing: cheap open weights for bulk, a frontier tier for judgment, a spend cap that fails over on its own.
- **Quality as a gate, not a hope.** Declarative evals over a pluggable check-method registry run both inline (fail-closed: a failing floor blocks the answer) and offline (named metrics: precision, recall, F1).
- **Cost and quality are measured, never guessed.** Every call writes one metered decision (cost, latency, gate outcome); the console reads real usage and shows an honest empty state rather than a fabricated number.
- **Distribution built in.** Any capability can be exposed as an MCP server (stdio and hosted), so an external agent can plug straight into it.

**Stack:** TypeScript monorepo (10 packages) · pluggable provider adapters · HTTP + MCP gateway · React console · fail-closed eval gates
**Where it is now:** open source, CI green, live console in demo mode. The four products below embed it.

<br>

### ⭐ FounderFirst: *the autonomous back office founders actually wanted* &nbsp;·&nbsp; [early access →](https://founderfirst.one) &nbsp;·&nbsp; [code →](https://github.com/nikjain15/founderfirst.one)

**Meet Penny: she does your books while you sleep, and only taps you when she needs a call.**

**The problem.** Founders start companies to build, not to reconcile receipts at midnight. Every accounting tool was built for *accountants*, so the owner is still categorizing, chasing invoices, and prepping for the CPA.

**What I built.** Penny, an agent that runs the back office: auto-categorizes every transaction across **Stripe, bank & cards**, captures receipts by photo with one-tap approval, chases late payers, and keeps the books **CPA-ready with real-time profit, not just revenue**.

**Why it's different**

- **Deterministic first.** Exhaustive rules run before any model: **82.5% of transactions resolve with zero model calls.** Only genuine ambiguity escalates — cheap model first, reasoning model when it hedges — scoring **85.6% macro-F1** on the hard remainder.
- **You speak founder; Penny speaks accountant.** Log "paid the AWS bill," she maps the category and attaches the receipt, learning your business's own rules with every transaction.
- **Grounded in your real ledger.** Answers are retrieved, never guessed; a confident wrong number is worse than a question.

**Stack:** TypeScript monorepo · event-driven services · Postgres · multi-model orchestration via Conduit
**Where it is now:** live in early access, referral-driven waitlist (100+ founders), no active users yet — and honest about that.

<br>

### ⭐ RoleOS: *RO runs your job hunt. You make the calls.* &nbsp;·&nbsp; [live →](https://ro.roleos.fyi) &nbsp;·&nbsp; [code →](https://github.com/nikjain15/roleos-app)

**A senior job hunt is the highest-stakes, lowest-leverage thing you do. RO takes the work; you keep every decision.**

**The problem.** AI has broken the senior job hunt from both ends: the roles are being reinvented (AI PM, forward-deployed, applied-AI leadership barely existed two years ago), and AI-written mass applications have flooded the funnel. The people best suited for the new senior roles are the hardest to match and the easiest to lose in the noise.

**What I built.** RO, an agent that runs **Find → Apply → Land** over a **live index of 1,536 postings across 294 AI-native companies**: honest role scoring (*pursue / maybe / skip*, with the why and the gaps), drafted résumés and answers you approve word by word, interview prep and negotiation drafts.

**Why it's different**

- **Reliability as code.** **No "send" tool exists in the agent** — human-gated outbound is guaranteed by dependency-cruiser rules and an invariant test suite, not by a design doc.
- **Grounded matching.** Retrieval over the live corpus (pgvector) with calibrated scoring, not vibes.
- **A five-gate agent under a simple surface** (Match, Screen, Build, Coach, Negotiate) on a metered multi-model registry: right model, right cost, per task.

**Stack:** Next.js 15 · TypeScript · Cloudflare Workers + Workflows · Supabase (Postgres / pgvector, RLS) · Conduit
**Where it is now:** live at [ro.roleos.fyi](https://ro.roleos.fyi).

<br>

### ⚡ Pulse: *the board that updates itself* &nbsp;·&nbsp; [live →](https://pulsecohort.vercel.app) &nbsp;·&nbsp; [code →](https://github.com/nikjain15/pulse)

**Jira, if it filled itself in.**

**The problem.** Every project tool runs on manual upkeep. The tracking becomes a second job, and the minute anyone falls behind, the board quietly lies about where things actually stand.

**What I built.** A board that maintains itself: reads every commit & PR, writes the status in plain English, publishes it live, and flags who's stuck so peers can step in. Built for and piloted with a 65-person developer cohort.

**Why it's different**

- **Prompt-injection defense that's provable.** Commit messages are attacker-controllable yet auto-published to the whole team, so a deterministic server-side guard ensures a summary can only describe its own author — holding **100% must-block recall against a labeled injection harness** that exercises the real shipped function, not a mock.
- **The board is always true.** It reflects the real work, not what someone remembered to type.
- **Cost-engineered:** identity-based caching cuts modeled pilot spend ~10–20×.
- **934 passing tests** (unit + rules + integration + e2e).

**Stack:** Next.js 16 · React 19 · TypeScript · Firestore (realtime) · server-side AI · Vercel

<br>

### ⚡ Rally: *team chat that builds the team* &nbsp;·&nbsp; [live →](https://rally-nikjain15.vercel.app) &nbsp;·&nbsp; [code →](https://github.com/nikjain15/rally)

**Recognition, motivation, and follow-through, not just messages.**

**The problem.** Slack and Discord move messages, but recognition happens by accident, motivation fades, and the human signal (who helped whom, who kept their word) disappears in the scroll. Bolt "points" onto it and they're instantly gamed.

**What I built.** Real-time chat (channels, DMs, threads) with a trust layer: peer-confirmed recognition, commitment tracking wired to GitHub issues, and an assistant that drafts catch-ups for you to confirm.

**Why it's different**

- **Detection tuned recall-first, on purpose: 0.83 precision / 0.92 recall.** A missed thank-you silently erases someone's help; a false positive costs one dismissal. What makes that safe is upstream: **a detection is a suggestion a human confirms, never an award.**
- **Ungameable ledger.** Points live in an append-only collection written only by trusted server routes; rank is computed, never stored; you can't confirm your own recognition.
- **The AI has no authority.** It classifies, summarizes, and drafts, but never writes a points-bearing row.

**Stack:** Next.js 16 · React 19 · TypeScript · Firestore · Firebase Auth · server-side AI

<br>

### 📗 Lossless Modernization: *the playbook, open-sourced* &nbsp;·&nbsp; [site →](https://nikjain15.github.io/lossless-modernization) &nbsp;·&nbsp; [code →](https://github.com/nikjain15/lossless-modernization)

**How to turn money-critical legacy systems into AI-native platforms without losing a byte of logic or a cent of accuracy.** A four-stage method, seven patterns, parity-harness templates you can run, and a post-mortem library of famous modernizations that failed — with what each one cost. MIT-licensed.

### 📊 Build OS: *the scorecard I grade myself with* &nbsp;·&nbsp; [dashboard →](https://nikjain15.github.io/build-os/)

**A rubric that scores every product above across nine craft pillars** (evals, reliability, security posture, docs, and more) **on a public dashboard.** The scores publish whether they flatter me or not. Leaving evals thin feels different when the gap has your name on it in public.

### 🔗 …and they talk to each other

**Pulse and Rally aren't two silos: an agent in one can dispatch work directly to an agent in the other.** Keyed by shared identity, they exchange recognition, progress and "stuck" signals, presence, and commitments — a working **agent-to-agent dispatch mechanism** across independent systems, the exact pattern enterprises are about to face as every tool ships its own agent.

---

## 🌱 A decade of building, the through-line

*Before modernizing trillion-dollar finance, I was founding companies and dragging legacy systems into the future at startup scale.*

**CredR: Co-founder · 2015–2021** &nbsp;·&nbsp; *one of India's largest used two-wheeler marketplaces*
- **Scaled it 0-to-1:** 150K+ transactions, **$29.5M raised** (Yamaha, Eight Roads, Omidyar Network), a **450-person team**
- **Modernized an entire dealer network:** took **1,050 dealers off handwritten ledgers onto a mobile-first, ML-powered platform** (80% adoption, 10× consumer growth) — the same instinct I now apply at $1.6T scale
- **AI from day one:** an ML pricing engine over **800K vehicle histories** that became the category's de facto standard; NLP chatbots that **auto-resolved 35% of inbound and cut resolution time 42%**

**Earlier:** co-founded **Coursewave** (edtech, exited via M&A) and **Enelek Power** (cleantech, acquired); building since college.
**Foundations:** IIT-Bombay (Engineering Physics) · UVA Darden MBA (Batten Fellow, top 0.3% of 3,000) · Forbes 30 Under 30 Asia

---

## Find me

💼 [LinkedIn](https://www.linkedin.com/in/niktechnologist/) &nbsp;·&nbsp; 🐦 [X](https://x.com/NIkJain1510) &nbsp;·&nbsp; ✉️ nikjain1588@gmail.com

<sub>**I work at the intersection of product and engineering for enterprise AI,** a role that goes by many names.</sub>

<sub>AI Product Manager · Technical PM · Staff Product Manager · Principal Product Manager · Forward Deployed Engineer (FDE) · Founding PM · AI Transformation Lead · Enterprise AI Lead · Legacy Modernization · Agentic AI · LLM · RAG · evals · AI governance · human-in-the-loop · AI/ML · fintech · asset management</sub>
