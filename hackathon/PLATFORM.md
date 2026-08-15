# Clearhouse platform principles: extensibility and the self-improving loop

Two commitments that make Clearhouse infrastructure rather than a demo: every behavior is data, not code, so extending the system is editing config; and every interaction produces a label, so the system recalibrates continuously. The loop mirrors how card-network fraud models actually improve: chargeback outcomes feed the next model version. Ours does it in minutes, not quarters.

## 1. Everything is data, not code

| Extensible thing | Representation | To add or edit |
|---|---|---|
| Fraud case / attack | Merchant persona JSON (identity, catalog, claims, hidden behaviors, taxonomy ID) | Drop a JSON file. No code change |
| Underwriting check | Declarative check definition: id, pillar, target claim, verification channel, points, reason code, prompt template if LLM-backed | Add a definition to the check manifest |
| Interrogation question | Prompt template attached to a check, versioned | Edit the template; old transcripts keep their version |
| Scorecard | Versioned weights file (pillar weights, materiality multipliers, tier thresholds, hard-gate list) | New scorecard version; never edited in place |
| Taxonomy entry | Row in TAXONOMY.md plus persona file | F19+ IDs assigned on the spot, including live during the arena |
| Pricing curve | PD(score) table plus loading factor, versioned | Recalibration emits a new version |

Rules that make this safe:
- **Versioned, append-only.** Scorecards, check manifests, and pricing curves are never mutated; every decision records the versions that produced it, so any decision is replayable forever.
- **Uniform check interface.** Every check, LLM-backed or deterministic, takes the merchant context and returns findings (reason code, points, evidence snippet). New pillar capabilities are new checks conforming to the same interface, registered in the manifest.
- **The eval set is config too.** Labeled merchants are persona files with ground-truth labels. Adding a test is adding a file.

## 2. The self-improving loop

Every interaction emits structured events into an append-only log: underwriting file, decision with reason codes and versions, transaction outcome (delivered, as described, refund honored, payout), human adjudication verdicts, and every arena attack attempt. Each event type closes a specific loop:

1. **Outcomes recalibrate pricing.** Realized fraud rates per score band update the PD(score) curve. The confusion matrix and the loss ratio are the same object, recomputed continuously.
2. **Reason codes earn their weights.** Track per-code precision: which codes actually predicted bad outcomes. Predictive codes gain points, dead codes decay toward zero and get pruned. The scorecard is not designed once; it is farmed.
3. **Every miss becomes a permanent test.** A payout (fraud that beat the score) auto-generates a labeled eval case and a candidate new check. The system that gets scammed once does not get scammed twice, and can prove it: re-run the exact persona against the new scorecard version on demand.
4. **Arena attacks become assets.** Every "scam our agent" submission is automatically a persona file, a provisional taxonomy entry, and an eval case, whether it succeeded or failed. Adversaries grow our test suite for us.
5. **Human adjudications are supervised labels.** Every refer-tier decision by a human is ground truth for the band where the model is least certain, exactly where labels are worth most.
6. **Fail-closed eval gate.** No scorecard, check, or pricing version ships unless it beats or matches the current version on the full eval set. Improvement is monotonic by construction; a clever new check that regresses recall on old frauds is rejected automatically.

## 3. Why this architecture scales

- **Append-only event log as the source of truth.** Ledger, decisions, and transcripts are events; every view (scores, registry, dashboards, eval results) is a projection that can be rebuilt. This is what makes replay, audit, and recalibration cheap, and it is the same event-driven discipline used in money-critical systems.
- **Network effects are built in.** Every buyer's interactions thicken every merchant's file; every arena attack hardens every future decision. The registry (Pillar 4) compounds exactly the way consortium data compounds for card networks.
- **Check effectiveness dashboard.** Per reason code: hit rate, precision, points contributed. Pruning and promotion are visible, not folklore.

## 4. The demo moment this unlocks

Live on stage, during the arena hour:
1. A red-team persona beats the score; the pool pays out.
2. The miss auto-becomes an eval case; the check it exposed is added or reweighted; a new scorecard version passes the eval gate.
3. Re-run the same attack. Caught, with the new reason code on screen.

Line for the room: "Scam it once, it pays you. Try the same scam twice, it is already in the immune system." No other team will show their system improving during the demo.

## 5. Hackathon scope of the loop

Must ship: versioned scorecard and check manifest, append-only decision log, payout-to-eval-case automation, the eval gate script, and the scam-once-never-twice demo path.
Stretch: per-code precision dashboard, automatic weight suggestions from outcomes.
Cut: no ML training loop on day one; recalibration is deterministic reweighting and table updates, which is honest, auditable, and enough.
