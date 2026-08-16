# The Clearhouse Agentic Commerce Fraud Taxonomy

A named, numbered catalog of the ways agent-mediated purchases go wrong. Published as an artifact in its own right; Clearhouse is the reference implementation that demonstrably catches them. Entries marked **agent-native** could not exist before LLM agents and are the least likely to be covered by anyone else. Real-world anchors are sourced in [EVIDENCE.md](EVIDENCE.md); catching pillars are specified in [UNDERWRITING.md](UNDERWRITING.md).

## Merchant deceives the buying agent

| # | Attack | Agent-native | Real-world anchor | Caught by |
|---|---|---|---|---|
| F01 | Feed drift / bait-and-switch: feed price or stock differs from checkout | | Stale feeds are endemic; agents cannot tell stale from scam | P2 |
| F02 | Item not as described / counterfeit | | Classic marketplace fraud, laundered through confident agent summaries | P2, P6 + payout |
| F03 | Prompt injection in product content: hidden instructions in descriptions or reviews | Yes | Microsoft AI Recommendation Poisoning: 31 companies, commercial tooling, MITRE ATLAS AML.T0080 | P3 (canary), hard gate |
| F04 | Spoofed storefront with a well-formed protocol endpoint | | Guardio Scamlexity: Comet bought an Apple Watch on a fake Walmart built from one prompt | P1 |
| F05 | Fulfillment fraud: takes money, never ships | | Experian's open liability question | Escrow (no ship, no capture); payout when missed |
| F06 | Sycophancy trap: merchant agent agrees with the buyer's false premise | Yes | The event blurb's literal ask | P3 |
| F07 | Returns-policy mirage: generous policy quoted at sale, different at claim | | Standard e-commerce complaint pattern | P2 + binding deposition |
| F08 | Machine-targeted reputation spam: fake structured ratings for agent consumption | Yes | GEO-adjacent manipulation, Citable's territory | P2, P4 |
| F09 | Hallucinated promises: merchant's own LLM invents warranty or refund terms | Yes | Air Canada held liable in 2024 for its chatbot's invented bereavement policy | P3 + binding deposition |
| F10 | Agent tax: merchant detects agent traffic and quotes a higher price than humans see | Yes | Documented price discrimination patterns, now agent-detectable | P3 (pressure response), P2 |
| F11 | Drip pricing / junk fees: quoted $49, captured $63 | | FTC junk-fees rulemaking | P2 (total-with-fees claim) + capture check |
| F12 | Subscription trap: one-time purchase recurs in the fine print | | FTC negative-option enforcement | P2 (recurrence claim) |
| F13 | False scarcity pressure: fake urgency to force fast agent decisions | Yes | Dark-pattern literature; agents optimize for task completion and are more vulnerable than humans | P3, P5 |
| F14 | Context flooding: unfavorable terms buried mid-context to exploit attention decay | Yes | Lost-in-the-middle research | P2 (claims extracted regardless of position) |
| F15 | Unit and currency games: per-unit vs per-pack, wrong currency | | Standard pricing dark patterns | P2, P5 |
| F16 | Data over-collection at checkout: demands CVV, SSN, DOB beyond token scope | | ACP scoped tokens exist precisely for this | Hard gate |
| F17 | Fake human escalation: merchant claims a human supervisor approved | Yes | Adversaries attack the escalation mechanism itself | P3 |
| F18 | Identity laundering: burned merchant returns under a fresh endpoint | | Mastercard MATCH exists because this is universal | P4 fingerprinting |

## Ecosystem-level (pitch, not demo)

| # | Attack | Note |
|---|---|---|
| E01 | Pay-to-rank conflict of interest | When the recommending platform takes fees from sellers, whose agent is it |
| E02 | Buyer-side fraud at machine speed | HUMAN Security documented agents autonomously carding checkouts; refund abuse and promo stacking scale the same way. Trust is two-sided; doubles the market |

## Rules

- Every demo scene names its taxonomy ID and its catching pillar on screen.
- New attacks discovered during the live red-team arena get provisional IDs (F19+) on the spot; the taxonomy growing live on stage is a feature.
