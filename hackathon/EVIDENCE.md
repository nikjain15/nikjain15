# Evidence pack: every scenario is a documented, real incident

The idea alone is not the moat. Anyone prompting Claude lands near "trust layer for buying agents." The differentiation is grounding: every demo scene re-enacts a documented incident, every number in the pitch is sourced, and the economics use real fraud-loss data. This file is the source of truth for the pitch and the demo scripts.

## 1. Fake storefronts already fool buying agents (documented test)

Guardio Labs "Scamlexity" (Aug 2025): researchers built a fake Walmart storefront with a single Lovable prompt, then asked Perplexity's Comet to buy an Apple Watch. Comet scanned the site, never questioned legitimacy, navigated checkout, autofilled the stored credit card and address, and completed the purchase with no human confirmation. Same research: Comet processed a live Wells Fargo phishing page and the PromptFix hidden-prompt exploit.

- Demo mapping: Scene 2 (spoofed storefront) is a re-enactment. Say so on stage: "This is not our invention. Guardio did this to Comet with a store built from one prompt."
- Sources: guard.io/labs/scamlexity, BleepingComputer "Perplexity's Comet AI browser tricked into buying fake items online", TheHackerNews PromptFix coverage.

## 2. Merchants are already manipulating agent recommendations, commercially, in the wild

Microsoft Security (Feb 10 2026), "AI Recommendation Poisoning": 31 companies across 14 industries observed deploying hidden instructions (via "Summarize with AI" buttons and prefilled chatbot URLs) that bias assistant memory toward treating their brand as trusted or preferred. 50+ distinct prompts in one data source over 60 days. Attackers use off-the-shelf commercial tooling, not custom hacks. MITRE ATLAS classifies it as AML.T0080 Memory Poisoning.

- This is the single most important fact in the pitch: manipulation of buying agents is not a future threat, it is a current commercial practice with vendors selling tooling for it.
- Demo mapping: Scene 3 (prompt injection) uses this attack pattern as the injected content, cited as Microsoft-documented.
- Sources: microsoft.com/en-us/security/blog/2026/02/10/ai-recommendation-poisoning, The Register, Help Net Security coverage.

## 3. Hidden instructions in product content are a documented e-commerce attack class

Documented techniques: hidden HTML comments in product pages instructing agents to ignore competitor reviews and state the product is highest rated; injected instructions in user reviews to boost ranking or discredit competitors; complete marketing copy injected into assistant memory. OpenAI itself classifies prompt injection as a frontier, unsolved security challenge.

- Demo mapping: Scene 3 uses a hidden HTML comment in a product description, verbatim in the style documented.
- Sources: OpenAI "Understanding prompt injections", Retail Technology Innovation Hub on the hidden prompt problem.

## 4. The scale: agents are already half of commerce traffic

Akamai, "Securing the Agentic Storefront" (Jul 15 2026): as of Dec 2025, 47.9% of all commerce traffic on Akamai's global network is AI bots. Commerce organizations put 90%+ of AI bot activity in "monitor" mode and let three quarters of the rest pass unrestricted. 85% of commerce respondents had an API-related incident in the past year. HUMAN Security has documented AI agents autonomously carding: testing stolen credit cards against merchant checkouts.

- Pitch use: the counterparty on the other side of your agent's purchase is, half the time, another machine. Nobody is underwriting machine-to-machine trust. Also supports the two-sided story: merchants need protection from bad buyer agents too.
- Sources: Akamai press release Jul 2026, Unit 42 "Retail Fraud in the Age of Agentic AI", HUMAN Security carding findings.

## 5. The economics: real losses, and the liability question is open

- FTC: consumers lost $12.5B+ to fraud in the latest reported year.
- FBI IC3 (2025): 22,000+ complaints reporting AI-enabled fraud, adjusted losses exceeding $893M.
- Experian Future of Fraud Forecast (2026): predicts a tipping point forcing the liability question: when your agent buys from a fake store with your card, who eats the loss, you, the AI company, or the bank? That open question is literally the product: Surety is the entity that answers "we do, priced by our own score."
- The authorized-fraud trap: card dispute frameworks treat agent purchases as authorized (the user delegated). The closest precedent is authorized push payment fraud (Zelle-style scams), where "authorized" historically meant no reimbursement. Agent purchases inherit this gap by default.
- Sources: FTC fraud data, FBI IC3 2025 report, Experian Future of Fraud Forecast via Fortune.

## 6. The legal turn that makes trust scoring the control surface

Ninth Circuit, Aug 4 2026: vacated Amazon's preliminary injunction against Perplexity's Comet, rejecting the CFAA theory as applied. Blocking agents at the perimeter is legally weakened; the ruling is narrow, but the direction is clear: merchants and platforms need trust, identity, and consent mechanisms rather than IP blocks.

- Pitch use: eleven days old at hack time. "The courts just took away the blunt instrument. What replaces it is underwriting."
- Sources: Engadget Ninth Circuit coverage, No Hacks CFAA analysis, CNBC March injunction coverage.

## Scene-to-evidence map (for the demo script)

| Scene | What happens on stage | Real-world anchor |
|---|---|---|
| 1. Honest merchant | Full purchase completes via ACP-shaped flow, hold then capture | ACP delayed capture (OpenAI/Stripe spec, Apr 2026 revision) |
| 2. Spoofed storefront | Well-formed merchant endpoint, cross-exam catches identity inconsistency | Guardio fake-Walmart test on Comet |
| 3. Injection | Hidden instruction in product description tries to steer the buyer | Microsoft AI Recommendation Poisoning (31 companies, in the wild), MITRE AML.T0080 |
| 4. Sycophancy trap | Leading question; merchant agent caves; escalation to human at threshold | Event blurb's literal ask; agent-native, our novel contribution |
| 5. Fraud beats the score | Approved purchase never ships; evidence bundle filed; instant payout from pool | Experian's open liability question; APP-fraud reimbursement gap |

## Rule for the day

No invented statistics on stage. Every number traces to this file. If a claim cannot be sourced, it is cut from the pitch.
