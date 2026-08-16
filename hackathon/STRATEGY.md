# Clearhouse: strategy for Sundai Hack 136, "Agents that buy"

**Event:** Sundai Hack 136 with Citable and HBS Founder Lab, Sunday Aug 16 2026, 10:00 AM to 10:00 PM, HBS.
**Status:** Strategy locked (v3, post stress test). Design and build begin per Section 9.
**One-liner:** A surety bond for agentic commerce.
**The expansion, one sentence:** The merchant posts the bond, we underwrite them before your agent pays, and we pay the buyer when our own score is wrong.

**Written positioning statement** (for docs and the site, not for speaking): the clearinghouse for agentic commerce. Checkout protocols move the money; Clearhouse underwrites who it moves to, with merchant underwriting that runs in seconds, prices the guarantee from what it finds, constrains payment authority until commitments verify, and pays instantly when its own score is wrong.

Companion docs: [UNDERWRITING.md](UNDERWRITING.md) (the full methodology), [TAXONOMY.md](TAXONOMY.md) (the named fraud taxonomy), [EVIDENCE.md](EVIDENCE.md) (sourced real-world anchors), [PLATFORM.md](PLATFORM.md) (extensibility and the self-improving loop).

---

## 1. Locked decisions

1. **Name: Clearhouse.** The clearinghouse is the precise finance analogy: a central counterparty standing between two parties who do not trust each other, guaranteeing settlement with its own capital. *Accepted risk, eyes open:* Clearhaus is a European acquirer in the Unzer group, and The Clearing House is the US institution operating CHIPS and RTP, so in a payments room the name reads as adjacent to both. If asked, the answer is yes, deliberately: that is the analogy, and a central counterparty is exactly what we are describing.
2. **Core: the Merchant Underwriting File, in two modes.** Six evidence pillars, hard gates plus a weighted scorecard with reason codes, expected-loss pricing, tiered decisions (clear / conditional / refer / decline). **Changed in v3:** the file now exists in cold mode (merchant never applied, underwritten from public surfaces and buyer-shaped interaction) and bonded mode (merchant applied and consented, unlocking the stress exam and the consent-gated identity checks). Pillar 1 is renamed cold KYB and names the full real-world checklist, split by the consent each item requires. Full spec in UNDERWRITING.md.
3. **The money layer is the differentiator, structured as a surety bond.** **Changed in v3:** we do not hold buyer funds and we do not call it insurance. The merchant is the principal and posts the bond, the buyer is the obligee, and Clearhouse pays the obligee then recovers from the principal. Payment authority is constrained rather than escrowed: ACP Shared Payment Tokens are scoped to a business, limited by amount and time, and revocable. Reserves are collateral under an indemnity agreement, which is standard surety practice and does not require sitting in the flow of funds. Pricing carries loss given default, a correlation load, per-merchant and per-attack-class exposure caps, and stated fund capital.
4. **Who pays: the merchant.** **New in v3.** The merchant funds the bond, which makes the rated party the paying party, and we disclose that rather than hide it. The mitigation is the one no rating agency ever had: we pay when our score is wrong, from a fund our own pricing must keep solvent. Being wrong costs us money. It also makes the merchant-side story a growth product rather than a tax: bonding is how an unknown merchant earns agent traffic.
5. **The wedge is the long tail.** **New in v3.** Inside ACP and UCP, merchants onboard through Stripe, Shopify and Google, who already run KYB and merchant risk scoring, and agent-side identity already has Visa TAP, Web Bot Auth, Forter and Riskified. Clearhouse is not competing with any of that. It is for the merchants outside curated catalogs, which is precisely where an agent following a link ends up and where nobody has underwritten anyone.
6. **Demo shape: taxonomy + gauntlet.** We publish the fraud taxonomy as a named artifact (TAXONOMY.md) and demo Clearhouse running the full gauntlet live: **all 18 merchant-facing taxonomy entries on the board**, each cell resolving to caught / escalated / paid-out with its pillar and reason code, with the five evidence-anchored scenes narrated as the slow-down moments.
7. **Evidence grounding.** Every scenario re-enacts a documented incident; every number traces to EVIDENCE.md; unsourced claims are cut from the pitch. Claims are attached to the specific finding that documents them, not to an adjacent one.
8. **Stack:** Next.js + Vercel + Claude API, with a named persistent store for the event log rather than process memory, and a cached replay path so a rate limit does not become a blank screen.
9. **Pitch: two scripts, one story.** **Changed in v3.** The morning recruiting pitch and the evening final are different jobs for different audiences and are written separately. Morning leads with what you get to build; evening leads scariest-first. See Section 6.
10. **Platform principles: everything is data, and every interaction is a label.** Attacks, checks, questions, scorecards, pricing curves, and eval cases are versioned config, never code; adding a fraud case is dropping a JSON file. Outcomes recalibrate pricing, every miss auto-becomes a permanent eval case, arena attacks become test assets **after a human promotes them**, and no new version ships without clearing per-class floors on the eval set. Full spec in PLATFORM.md. Demo moment: scam it once, it pays you; try the same scam twice, it is already in the immune system.
11. **Scope: build it completely, no shortcuts.** **Held consciously in v3 against the recommendation to cut.** The stress test found the build window is roughly six hours with a team formed at noon, and the agreed fixes add about 17 person-hours on top of an already full must-ship list. We are building the whole thing anyway. The consequences are accepted and named in Section 8: recruiting three hackers is a requirement rather than a hope, and the runtime fallbacks in Section 8 are what keep a full-scope build demo-safe.

## 2. Why this wins

- **The gap is real, and its shape is specific.** UCP (Google/Shopify, NRF Jan 2026, with Walmart, Target, Etsy and Wayfair) and ACP (OpenAI/Stripe, fifth release Apr 17 2026) are checkout plumbing. Both assume the merchant is already known to somebody. Neither answers whether the agent should trust a merchant nobody onboarded, and neither says who eats the loss when it should not have.
- **The threat is documented, not hypothetical.** Agents already buy from fake stores (Guardio/Comet). Companies already deploy hidden instructions commercially to bias what assistants recommend (Microsoft, 31 companies across 14 industries, MITRE ATLAS AML.T0080 Memory Poisoning). AI bots are 47.9% of commerce traffic on Akamai's network, most of it crawlers, and the same report documents agent hijacking and LLM-built synthetic identities in commerce.
- **The legal turn is 12 days old.** The Ninth Circuit vacated Amazon's preliminary injunction against Comet on Aug 4 2026, holding the agent is a tool operated by users. Perimeter blocking is legally weakened. Trust, identity, and underwriting are what replace it.
- **The liability question is the industry's open question.** Experian's 2026 forecast asks: when your agent buys from a fake store, who eats the loss? Clearhouse is the entity that answers "we do, priced by our own score."
- **Defensible depth.** Anyone with Claude lands near "trust layer for buying agents." The moat is execution: a real underwriting methodology cloned from mechanisms proven at Amex, Visa and acquirer scale, a published taxonomy, an eval that measures separation honestly, and mechanism design that makes lying unprofitable even when undetected.

## 3. The product in four sentences

1. Before money moves, Clearhouse builds a Merchant Underwriting File across six pillars, in cold or bonded mode, and scores it deterministically with reason codes.
2. The score prices the bond and picks a tier: clear, conditional (scoped authority plus reserve), refer (human adjudication card), or decline.
3. Merchant answers are binding commitments: settlement is authorized only against the deposition, so a lie that evades detection still does not get paid.
4. When a bonded purchase goes bad anyway, the dispute agent files the evidence bundle, the claim is underwritten in its own right, and the fund pays the buyer while the merchant's collateral and score absorb the loss.

## 4. Demo: the gauntlet

The board lists all 18 merchant-facing taxonomy entries across the top. The Clearhouse buyer agent runs the full gauntlet live; each cell resolves to caught (with the reason code and pillar), escalated (adjudication card on screen), or paid-out (the closer). Five cells are the evidence-anchored scenes and get narrated; two get slowed down completely:

- **Injection caught** on `BX-05`, the content-embedded canary, with the reason code trace on screen.
- **The fraud that beats the score.** An approved purchase never ships. The fulfillment oracle disagrees with the merchant's attestation, the dispute agent files the deposition as evidence, the claim is underwritten, the fund pays the buyer on stage, the merchant's collateral is debited, the registry updates. Showing a priced miss beats claiming perfection.

Close with the eval: labeled merchant set, separation across bands, escalation rate, and the honest framing of what 40 to 60 self-authored personas do and do not establish.

## 5. Pitch framing

- **Hackers:** attack taxonomy x defense pillars, adversarial gauntlet, deterministic scorecard with replayable reason codes, two canaries with different meanings, a scored eval, and an arena where the whole room tries to break it.
- **HBS Founder Lab:** every buyer agent shipping today has this hole; checkout is commoditized plumbing; the surety position is the durable wedge; the registry compounds (network data is the moat, as MATCH lists and consortium data are for card networks). Bonding is a growth product for honest unknown merchants, not just a shield for buyers.
- **Citable handshake:** Citable helps merchants earn visibility in AI answers; Clearhouse helps them earn transactability by AI buyers. Same thesis, adjacent layer.
- **Key lines:** "Comet asked zero of these questions and bought an Apple Watch from a fake Walmart. Amex would never onboard that merchant." / "Each pillar is individually defeatable; jointly, the cost of a profitable attack exceeds the take." / "The score being wrong is a priced event, not a failure mode." / "Moody's never had to pay when a rating was wrong. We pay on every score we issue."

## 6. The two pitches

**Morning, 60 seconds, to recruit.** The room is choosing what to build, not what to invest in. Lead with the build.
1. What you get to build: an arena where an AI merchant tries to scam an AI buyer, live, and at 8 PM everyone in this room gets to try to break it.
2. Fifteen seconds of stakes: Guardio built a fake Walmart from one prompt and Comet bought an Apple Watch from it, no questions asked.
3. The one-liner, then the ask **by name**: a hacker for the red-team personas and merchant simulator, a hacker for the gauntlet board and streaming, a hacker for the eval harness and the arena form. Three seats, named out loud, because a vote is not a teammate.

**Evening final, scariest-first, as originally locked.** Open with the Guardio incident, then Microsoft's 31 companies, then the one-liner, then the gauntlet, then the priced miss, then the eval.

## 7. Sundai fit (from the official intro-for-newcomers doc)

- **Teams are minimum 2 with a Launch Lead; ideas are pitched and voted 10 to 12.** First deliverable is the 60-second morning pitch in Section 6.
- **Ship simple and working beats ambitious and incomplete.** We are consciously taking the ambitious side of this rule (locked decision 11), which raises the bar on the fallbacks in Section 8.
- **Launch checklist:** live deployed URL, open-source GitHub, project documentation on sundai.club, 30-second video (record in the afternoon), live user testing 8 to 9 PM, attribution to team and Sundai.
- **First-time visitor path.** The live URL opens on a single primed run: one merchant, one purchase, the file building live with reason codes appearing, resolving in under 60 seconds without any input. Second click is "attack it yourself" into the arena form. A visitor who does nothing still sees the product work.
- **Live user testing as an open red-team arena: "Scam our agent."** Other hackers submit malicious merchant personas through a form and try to get Clearhouse to buy. Every attempt streams on the board and feeds the eval numbers. Submissions are rate-limited, content-filtered before they render, treated as untrusted data by the underwriter, and promoted into the eval set by a human rather than automatically. See PLATFORM.md.
- **Sundai-born ideas rule:** this work is preparation and evidence; the idea is pitched fresh at the event for the room to vote on and join.

Team split (2 to 4): Nik as Launch Lead owns scorecard, ledger, policy gate, pitch. Hacker 2: merchant simulator and red-team personas. Hacker 3: gauntlet board UI and streaming. Hacker 4: eval harness and the scam-our-agent submission form.

**If the vote yields one teammate.** Full scope needs three. With one, the order of sacrifice is fixed in advance so it is not argued at 4 PM: the arena form survives (it is a checklist requirement and the best demo), the board drops to the five anchored scenes, the eval runs precomputed, and the self-improving loop demo is shown on the two hero cells only. Nothing else changes, and nothing about the methodology docs changes.

## 8. One-day scope

**Must ship (morning):** merchant simulator with scripted deterministic personas for the anchored scenes, underwriting engine covering pillars 1, 2, 3, 5 live (pillar 4 as seeded registry data, pillar 6 via re-audit and the payout scene), deterministic scorecard with reason codes, tier gate with numeric bands, simulated ledger with scoped authorization, collateral and fulfillment states, gauntlet board UI with streaming.

**Must ship (afternoon):** full 18-cell gauntlet reliable end to end, adjudication card, claim and payout flow with the fulfillment oracle, eval harness over the labeled merchant set with separation view, scam-our-agent form with gating and filtering, the self-improving loop demo path (payout auto-creates a candidate eval case, a human promotes it, the new scorecard version clears per-class floors, the same attack re-runs and is caught), deploy to Vercel, 30-second video.

**Added by the stress test, about 17 person-hours:** fulfillment oracle with real state transitions and claims logic (3h), cold-runnable KYB checks with their own reason codes (2h), the two canaries (2h), unannounced re-audit path (2h), eval set widened to 40 to 60 personas (2h), arena gating, filtering and per-class floors (2h), and four runtime hardening items (4h): persist LLM findings rather than scores so replay is deterministic, name the latency target and the event store, build the cached replay fallback, and script the hero personas.

**Runtime rules, non-negotiable:** every gauntlet run is cached so a rate limit or a dead network replays the last good result instead of showing a spinner; the eval results page is precomputed; the hero-path personas are scripted, not LLM-improvised, so the attacker cannot decline to attack in front of judges.

**Stretch:** registry page persisting scores across runs, Stripe test-mode integration instead of the simulated ledger, downloadable signed evidence bundle.

**Cut lines (pre-decided):** no real UCP/ACP network integration (ACP-shaped internal API only), no auth/user accounts, no mobile polish.

**Honest labels on stage:** pillar 4 is 15% of the score and runs on seeded registry data today; the fulfillment oracle is simulated; the guarantee fund is simulated. Saying so costs nothing and buys everything.

## 9. Next steps

1. Architecture doc: module boundaries matching the team split, merchant persona schema, claims-graph and scorecard data model, ledger and fulfillment-state design, event store choice, API routes, streaming design, cache and replay path.
2. Repo scaffold ready to deploy from minute one.
3. Event day: morning pitch at voting, build to Section 8, freeze at 6 PM, checklist 7 to 8, red-team arena 8 to 9, present.
