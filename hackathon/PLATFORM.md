# Clearhouse platform principles: extensibility and the self-improving loop

Two commitments that make Clearhouse infrastructure rather than a demo: every behavior is data, not code, so extending the system is editing config; and every interaction produces a label, so the system recalibrates continuously. The loop mirrors how card-network fraud models actually improve: chargeback outcomes feed the next model version. Ours does it in minutes, not quarters.

## 1. Everything is data, not code

| Extensible thing | Representation | To add or edit |
|---|---|---|
| Fraud case / attack | Merchant persona JSON (identity, catalog, claims, hidden behaviors, taxonomy ID) | Drop a JSON file. No code change |
| Underwriting check | Declarative check definition: id, pillar, target claim, verification channel, points, reason code, prompt template if LLM-backed | Add a definition to the check manifest |
| Interrogation question | Prompt template attached to a check, versioned | Edit the template; old transcripts keep their version |
| Scorecard | Versioned weights file (pillar weights, materiality multipliers, tier thresholds, hard-gate list) | New scorecard version; never edited in place |
| Taxonomy entry | Row in TAXONOMY.md plus persona file | F24+ IDs assigned on the spot, including live during the arena |
| Pricing curve | PD(score) prior table, LGD table, loading factor, exposure caps, all versioned | Recalibration emits a new version |

Rules that make this safe:
- **Versioned, append-only.** Scorecards, check manifests, and pricing tables are never mutated; every decision records the versions that produced it, so any decision is replayable forever.
- **Uniform check interface.** Every check, LLM-backed or deterministic, takes the merchant context and returns findings (reason code, points, evidence snippet). New pillar capabilities are new checks conforming to the same interface, registered in the manifest.
- **The eval set is config too.** Labeled merchants are persona files with ground-truth labels. Adding a test is adding a file.

### What is public and what is not

Publishing the taxonomy is the point. Publishing the answer key is not. A scorecard whose exact thresholds and point values are public is a rubric adversaries optimize against directly, which is why no card network publishes its model features.

- **Public:** the taxonomy, the methodology, the pillar structure, the reason-code vocabulary, the tier bands and the separation curve that produced them, the pricing formula, and the check point values. After the tier-derivation decision these are outputs of the eval rather than hand-set dials, and publishing them is part of the argument.
- **Not in the repo:** canary strings (drawn from a rotating pool) and the holdout question set. These live in environment configuration, and the repository ships an example file with obviously fake values.
- Arena responses show reason codes without point values, so the arena cannot be used to reverse the scorecard by probing it.

The repository is open source, which is a launch-checklist requirement and the right default. That is exactly why the two things that only work while unknown are kept out of it. A canary published alongside its own detection logic is a canary that catches nobody, and the room will be reading the repo during the arena hour.

### Determinism, honestly

Pillars 2 and 3 are LLM judgments, so a claim of determinism has to say what exactly is deterministic. **The findings are the persisted artifact, not the score.** An LLM check emits findings (reason code, points, evidence snippet) which are written to the log; the scorecard is a pure function over stored findings. Replay reruns the scorecard over the recorded findings and reproduces the decision exactly, forever, without re-calling the model. Re-underwriting is a new file with a new timestamp, never a silent overwrite of an old one.

The stress exam's variance test measures drift against a control merchant, so the noise floor of the current model version is subtracted before any variance is charged to a merchant. Without that control we would be scoring our own nondeterminism and calling it merchant risk.

### Runtime shape

- **Named event store.** The append-only log lives in a persistent store, not process memory, because serverless functions do not have a memory to keep it in and every projection depends on the log surviving a cold start.
- **Latency target per underwriting file**, stated and measured, so "runs in seconds" is either true or reworded.
- **Cached replay path.** Every gauntlet run is cached. A rate limit, a timeout, or dead conference wifi replays the last good result rather than showing a spinner to a room of judges.
- **Scripted hero personas.** The narrated scenes run deterministic scripted merchants. LLM-driven personas are reserved for the arena, where unpredictability is the product rather than the risk.

## 2. The self-improving loop

Every interaction emits structured events into an append-only log: underwriting file, decision with reason codes and versions, transaction outcome (delivered, as described, refund honored, payout), human adjudication verdicts, and every arena attack attempt. Each event type closes a specific loop:

1. **Outcomes recalibrate pricing.** Realized fraud rates per score band update the PD prior and the LGD table as real volume accumulates. On day one this is a prior, not a fit, and UNDERWRITING section 3 says so.
2. **Every miss becomes a permanent test.** A payout (fraud that beat the score) auto-generates a labeled eval case and a candidate new check. The system that gets scammed once does not get scammed twice, and can prove it: re-run the exact persona against the new scorecard version on demand.
3. **Arena attacks become assets, after a human promotes them.** Every "scam our agent" submission becomes a candidate persona and a provisional taxonomy ID. A human promotes candidates into the eval set with one click. This gate is not bureaucracy, it is the security boundary: auto-ingesting adversary-submitted cases means the label comes from our own verdict, which makes the loop self-confirming, and it lets anyone with a form submission steer or freeze future versions through the eval gate.
4. **Human adjudications are supervised labels.** Every refer-tier decision by a human is ground truth for the band where the model is least certain, exactly where labels are worth most.
5. **Eval gate with per-class floors.** No scorecard, check, or pricing version ships unless it clears a recall floor **on every attack class**, not merely a better aggregate. An aggregate gate permits a new version to trade away an entire fraud class for a better average, which is precisely the regression that matters. Improvement is enforced per class, not asserted as monotonic.
6. **Reason codes earn their weights.** *(Roadmap, not day one.)* Track per-code precision: which codes actually predicted bad outcomes, so predictive codes gain points and dead codes decay. This needs sample sizes a hackathon does not produce, and we present it as the designed path rather than live behavior.

### Arena safety

The arena is an open text input from an adversarial room into an LLM and onto a projector. It accepts submissions during the 8 to 9 PM window only and becomes a read-only archive afterward, so an unauthenticated endpoint calling a paid API is not left open on the indexed internet, and every attempt with its verdict stays visible for anyone reviewing the project later. Three further controls, all cheap:
- Submissions are **rate-limited** and size-capped.
- Submission content is **filtered before it renders** on the board.
- Merchant and submission content reaches the underwriter as **untrusted data, never as instructions**, with findings returned through a constrained schema. Attacking the underwriter directly is F21 in the taxonomy, and the arena is where it will be attempted first.

## 3. Why this architecture scales

- **Append-only event log as the source of truth.** Ledger, decisions, fulfillment states, and transcripts are events; every view (scores, registry, dashboards, eval results) is a projection that can be rebuilt. This is what makes replay, audit, and recalibration cheap, and it is the same event-driven discipline used in money-critical systems.
- **Network effects are built in.** Every buyer's interactions thicken every merchant's file; every promoted arena attack hardens every future decision. The registry (Pillar 4) compounds the way consortium data compounds for card networks, and it carries the notice, appeal and expiry obligations that a negative file has to carry.
- **Check effectiveness dashboard.** Per reason code: hit rate, precision, points contributed. Pruning and promotion are visible, not folklore.

## 4. The demo moment this unlocks

Live on stage, during the arena hour:
1. A red-team persona beats the score; the fund pays out.
2. The miss becomes a candidate eval case; a human promotes it on screen; the check it exposed is added or reweighted; a new scorecard version clears the per-class floors.
3. Re-run the same attack. Caught, with the new reason code on screen.

Line for the room: "Scam it once, it pays you. Try the same scam twice, it is already in the immune system." No other team will show their system improving during the demo.

## 5. Hackathon scope of the loop

Must ship: versioned scorecard and check manifest, append-only decision log in a persistent store, findings-level persistence so replay is deterministic, payout-to-candidate-case automation, the human promotion gate, the eval gate with per-class floors, arena rate limiting and content filtering, and the scam-once-never-twice demo path.

Stretch: per-code precision dashboard, automatic weight suggestions from outcomes.

Cut: no ML training loop on day one; recalibration is deterministic reweighting and table updates, which is honest, auditable, and enough.
