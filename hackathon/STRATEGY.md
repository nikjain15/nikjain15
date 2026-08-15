# Clearhouse: strategy for Sundai Hack 136, "Agents that buy"

**Event:** Sundai Hack 136 with Citable and HBS Founder Lab, Sunday Aug 16 2026, 10:00 AM to 10:00 PM, HBS.
**Status:** Strategy locked (v2, final). Design and build begin per Section 8.
**One-liner:** The clearinghouse for agentic commerce. Checkout protocols move the money; Clearhouse underwrites who it moves to, with Amex-grade merchant underwriting that runs in seconds, prices protection from what it finds, holds funds until commitments verify, and pays instantly when its own score is wrong.

Companion docs: [UNDERWRITING.md](UNDERWRITING.md) (the full methodology), [TAXONOMY.md](TAXONOMY.md) (the named fraud taxonomy), [EVIDENCE.md](EVIDENCE.md) (sourced real-world anchors).

---

## 1. Locked decisions

1. **Name: Clearhouse.** The clearinghouse is the precise finance analogy: a central counterparty standing between two parties who do not trust each other, guaranteeing settlement with its own capital.
2. **Core: the Merchant Underwriting File.** Six evidence pillars, hard gates plus a weighted scorecard with reason codes, expected-loss pricing, tiered decisions (clear / conditional / refer / decline). Full spec in UNDERWRITING.md. This replaces the earlier "four probes" framing; interrogation is two pillars of six.
3. **The money layer is the differentiator.** Score prices protection (fee = expected loss x loading factor). Funds run authorize -> hold -> verify commitments -> capture. The deposition transcript is binding: capture executes only against what the merchant said. Rolling reserves for thin files. When the score is wrong, the protection pool pays the buyer instantly. Skin in the game is why anyone trusts the score.
4. **Demo shape: taxonomy + gauntlet.** We publish the fraud taxonomy as a named artifact (TAXONOMY.md) and demo Clearhouse running the full gauntlet live: a board of attacks fills with caught / escalated / paid-out, annotated with which pillar caught which fraud.
5. **Evidence grounding.** Every scenario re-enacts a documented incident; every number traces to EVIDENCE.md; unsourced claims are cut from the pitch.
6. **Stack:** Next.js + Vercel + Claude API. One language, one deploy, native streaming for the live gauntlet.
7. **Pitch: dual audience, scariest first.** Open with the Guardio incident (an agent bought from a fake store with a real card, no confirmation), then Microsoft's finding that 31 companies already manipulate agent recommendations commercially.

## 2. Why this wins

- **The gap is real and open.** UCP (Google/Shopify/Walmart, Jan 2026) and ACP (OpenAI/Stripe, fifth revision Apr 2026) are checkout plumbing. Neither answers whether the agent should trust this merchant, and neither says who pays when it should not have.
- **The threat is documented, not hypothetical.** Agents already buy from fake stores (Guardio/Comet). Merchants already game agent recommendations commercially with off-the-shelf tooling (Microsoft, 31 companies, MITRE ATLAS AML.T0080). Half of commerce traffic is already AI bots (Akamai, 47.9%).
- **The legal turn is 12 days old.** Ninth Circuit vacated Amazon's injunction against Comet on Aug 4 2026; perimeter blocking is legally weakened. Trust, identity, and underwriting are what replace it.
- **The liability question is the industry's open question.** Experian's 2026 forecast asks: when your agent buys from a fake store, who eats the loss? Clearhouse is the entity that answers "we do, priced by our own score."
- **Defensible depth.** Anyone with Claude lands near "trust layer for buying agents." The moat is execution: a real underwriting methodology cloned from mechanisms proven at Amex/Visa/acquirer scale, a published taxonomy, an eval with a confusion matrix that doubles as a loss ratio, and mechanism design that makes lying unprofitable even when undetected.

## 3. The product in four sentences

1. Before money moves, Clearhouse builds a Merchant Underwriting File across six pillars and scores it deterministically with reason codes.
2. The score prices protection and picks a tier: clear, conditional (escrow plus reserve), refer (human adjudication card), or decline.
3. Merchant answers are binding commitments: capture executes only against the deposition, so a lie that evades detection still does not get paid.
4. When a protected purchase goes bad anyway, the dispute agent files the evidence bundle and the protection pool pays the buyer instantly; the merchant's reserve and score absorb the loss.

## 4. Demo: the gauntlet

The board lists the taxonomy attacks across the top. The Clearhouse buyer agent runs the full gauntlet live; each cell resolves to caught (with the reason code and pillar), escalated (adjudication card on screen), or paid-out (the closer). Two hero moments get slowed down:

- **Prompt injection caught** using the Microsoft-documented attack pattern, with the reason code trace on screen.
- **The fraud that beats the score.** An approved purchase never ships. The dispute agent files the deposition transcript as evidence, the pool pays the buyer on stage, the merchant reserve is debited, the registry updates. Showing a priced miss beats claiming perfection.

Close with the eval: labeled merchant set, precision/recall, escalation rate, and the line "our confusion matrix is our loss ratio."

## 5. Pitch framing

- **Hackers:** attack taxonomy x defense pillars, adversarial gauntlet, deterministic scorecard with replayable reason codes, an original test (the instruction canary), a scored eval.
- **HBS Founder Lab:** every buyer agent shipping today has this hole; checkout is commoditized plumbing; the underwriter/clearinghouse position is the durable wedge; the registry compounds (network data is the moat, as MATCH lists and consortium data are for card networks). Thin-file terms make Clearhouse a growth product for honest unknown merchants, not just a shield for buyers.
- **Citable handshake:** Citable helps merchants earn visibility in AI answers; Clearhouse helps them earn transactability by AI buyers. Same thesis, adjacent layer.
- **Key lines:** "Comet asked zero of these questions and bought an Apple Watch from a fake Walmart. Amex would never onboard that merchant. We built Amex-grade underwriting that runs in seconds." / "Each pillar is individually defeatable; jointly, the cost of a profitable attack exceeds the take." / "The score being wrong is a priced event, not a failure mode."

## 6. Sundai fit (from the official intro-for-newcomers doc)

- **Teams are minimum 2 with a Launch Lead; ideas are pitched and voted 10 to 12.** First deliverable is a 60-second pitch that wins votes and recruits 2 to 3 hackers: open with the Guardio incident, then Microsoft's 31 companies, then the one-liner.
- **Ship simple and working beats ambitious and incomplete.** The scope table (Section 7) has pre-decided cut lines.
- **Launch checklist:** live deployed URL, open-source GitHub, project documentation on sundai.club, 30-second video (record in the afternoon), live user testing 8 to 9 PM, attribution to team and Sundai.
- **Live user testing as an open red-team arena: "Scam our agent."** Other hackers submit malicious merchant personas through a form and try to get Clearhouse to buy. Every attempt streams on the board and feeds the eval numbers live. A checklist requirement becomes the most memorable demo in the room and generates real human adversarial data.
- **Sundai-born ideas rule:** this work is preparation and evidence; the idea is pitched fresh at the event for the room to vote on and join.

Team split (2 to 4): Nik as Launch Lead owns scorecard, ledger, policy gate, pitch. Hacker 2: merchant simulator and red-team personas. Hacker 3: gauntlet board UI and streaming. Hacker 4: eval harness and the scam-our-agent submission form.

## 7. One-day scope

**Must ship (morning):** merchant simulator (honest + red-team personas as JSON config), underwriting engine covering pillars 1, 2, 3, 5 live (pillar 4 as seeded registry data, pillar 6 shown via the payout scene), deterministic scorecard with reason codes, tier gate, simulated ledger with authorize/hold/capture and reserves, gauntlet board UI with streaming.
**Must ship (afternoon):** full gauntlet reliable end to end, adjudication card, payout flow, eval harness over the labeled merchant set with confusion matrix view, scam-our-agent form, deploy to Vercel, 30-second video.
**Stretch:** registry page persisting scores across runs, Stripe test-mode manual-capture instead of the simulated ledger, downloadable signed evidence bundle.
**Cut lines (pre-decided):** no real UCP/ACP network integration (ACP-shaped internal API only), no auth/user accounts, no mobile polish, labeled merchant set of about 12 to 15, not 100.

## 8. Next steps

1. Architecture doc: module boundaries matching the team split, merchant persona schema, claims-graph and scorecard data model, ledger design, API routes, streaming design.
2. Repo scaffold ready to deploy from minute one.
3. Event day: pitch at voting, build to Section 7, freeze at 6 PM, checklist 7 to 8, red-team arena 8 to 9, present.
