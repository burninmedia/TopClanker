---
layout: post
title: "The Harvest-Now-Decrypt-Later Window Is Closing Faster Than Your PKI Rotation"
date: 2026-04-03
tags: [security, quantum, enterprise, post-quantum]
---

Two years ago, the conventional wisdom was that quantum computers capable of breaking P-256 encryption were decades away. That math is broken now — and the enterprise world is not moving.

In February 2026, researchers at a major quantum computing lab (name withheld under responsible disclosure agreements with affected vendors) demonstrated an optimized attack pathway that reduces the qubit requirements for cracking a single P-256 ECDH key from previously estimated 4,000–10,000 logical qubits down to approximately **1,900 logical qubits** using a hybridized variant of Shor's algorithm with error-corrected surface codes. IBM's 1,000-qubit Condor chip shipped in 2023. Google's Willow processor hit 105 qubits with error correction in late 2024. The qubit count is climbing. The error rates are falling. The math that kept your TLS connections private for fifteen years is approaching a cliff — not in theory, not in speculation, but in published preprints and lab benches.

This is not a hypothetical future problem. **Harvest-now-decrypt-later (HNDL)** attacks are already operational. Three separate intelligence agencies — unattributed in declassified assessments but characterized as "near-peer state actors" in a January 2026 NSA advisory — have been systematically recording encrypted TLS 1.2 and 1.3 session traffic transiting backbone infrastructure. The targets: financial messaging (SWIFT-adjacent), defense contractor VPN tunnels, and diplomatic cable archives. The rationale is straightforward cold-war logic: store everything now, decrypt when the hardware is ready. At scale, the cost of storing exabytes of encrypted traffic is trivial relative to the intelligence value of a five-year-old diplomatic cable decrypted in 2031.

## The Numbers Don't Lie, and Neither Does the CSA Survey

The Cloud Security Alliance published its 2026 State of AI Security survey in January. The findings are quietly alarming:

- **14% of organizations** report that AI agents in their environment already operate with some form of independent cryptographic action — signing documents, approving transactions, authenticating to third-party APIs — without human-in-the-loop oversight.
- **97% of security practitioners** surveyed said they expected a "significant" or "major" AI-security incident within the next 12 months.
- **Less than 3%** of respondents had any cryptographic inventory — a map of which keys protect which data, what algorithms are in use, what the rotation cadence is.

That last number is the tell. You cannot migrate what you cannot count. And the majority of enterprises cannot count their cryptographic assets.

NIST finalized its post-quantum cryptography standards in August 2024. ML-KEM (formerly CRYSTALS-Kyber), ML-DSA (CRYSTALS-Dilithium), and SLH-DSA (SPHINCS+) are in FIPS 203, 204, and 205 respectively. The algorithms are chosen, the reference implementations are published, the performance benchmarks are done. The National Institute of Standards and Technology ran a six-year competition process involving academics and cryptographers worldwide. The standards are mature.

Enterprise adoption: **essentially zero** outside of a handful of hyperscalers and defense contractors under regulatory mandate.

## The Migration Gap Is a Governance Gap

Let's be precise about what "migration" actually requires. Post-quantum migration is not a firmware update. It is a multi-year cryptographic inventory, classification, and rotation program that touches every TLS library, every HSM firmware, every certificate authority configuration, every secret management system, every application that has ever hardcoded a key length or specified a named curve. For organizations running hybrid on-premises and cloud infrastructure, the blast radius is every API endpoint, every mTLS service mesh, every code-signed binary.

The cost of a coordinated enterprise migration is estimated at **$1.2–3.5M per major application** in a 2025 Gartner analysis — not for the entire enterprise, per major application. Conservative estimate for a Fortune 500 with 200 meaningful applications: $240M–$700M. That figure includes HSM replacements, library updates, testing, certificate chain rebuilds, and rollback procedures. It does not include the cost of the organizational disruption.

No CFO is approving a $500M cryptographic overhaul for a threat that "isn't here yet." And that's the trap. By the time the threat is unambiguously here, the data is already harvested.

## What "Good Enough" Migration Actually Looks Like

There is no finish line. There is only risk reduction. The goal is not to be perfectly post-quantum — it is to reduce the harvest-now-decrypt-later window to something below your data's intelligence value horizon.

The practical minimum:

**1. Hybrid key exchange, now.**
Deploy TLS 1.3 with hybrid key exchange (X25519 + ML-KEM-768) on all new connections. OpenSSL 3.3+ and BoringSSL support this. Cloudflare and Google have been doing this for internal traffic since late 2024. This costs essentially nothing on new connections and prevents HNDL collection of future traffic.

**2. Cryptographic inventory in 90 days.**
You cannot rotate what you cannot find. Every TLS certificate, every signed artifact, every HMAC key, every SSH host key. Document the algorithm, the key length, the issuance date, the rotation date, the data it protects. This is a spreadsheet and a grep command at first — it does not need to be perfect to be useful.

**3. Prioritized rotation cadence.**
Rotate anything protecting data with a useful intelligence shelf life of >3 years first. Financial records, diplomatic communications, health data, source code. These are your HNDL targets. Rotate them on a 12-month cadence minimum; 6 months is better for high-sensitivity data.

**4. HSM firmware and library updates on a timeline.**
Your HSM vendor has a post-quantum roadmap. It is probably not public. Push them on it. Any HSM purchased after 2022 from a major vendor (Thales, Entrust, AWS CloudHSM) likely has a firmware path to PQC support. Anything older than 2019 probably requires hardware replacement.

**5. Agent framework requirements, before agents become your signing authority.**
This is where the governance gap is sharpest. The CSA's 14% figure — agents acting independently with cryptographic authority — should be zero until you have a cryptographic governance policy for agents. That policy does not exist in any major agent framework (LangChain, AutoGen, CrewAI, OpenAI Agents SDK) as of April 2026. No published PQC migration timeline. No cryptographic signing requirements for agent actions. No audit trail for which agent signed what with which key.

If you are deploying agents that take actions requiring authentication — approving a payment, signing a document, accessing a vault — you are running a cryptographic signing infrastructure that your security team has not designed, audited, or rotation-managed. That is a problem today, not a quantum problem.

## The Real Cost of Doing Nothing

Equifax. 2017. 147 million records. $1.7B in settlement costs, $400M in stock drop, ongoing litigation. The breach was facilitated by an expired TLS certificate on a public-facing service — a single oversight in cryptographic inventory management.

Now imagine that breach is not opportunistic financial theft but a state actor that has held encrypted backups for seven years, waiting for the hardware. The data is already out. The decrypt happens on their timeline, not yours. There is no incident response window, no firewall rule to block the intrusion, no patch to apply. The harvest is already complete.

That is the harvest-now-decrypt-later threat model. Not "someone will break in." **"Someone already has the ciphertext. They are waiting."**

The window is not hypothetical. The standards are not missing. The migration path is known.

What is missing is the organizational will to start — and that clock started ticking long before most enterprises realized it was running.

---

*If you're building agent infrastructure and care about cryptographic governance for AI systems, this is the area we're tracking closely at TopClanker. DM if you're working on this and want to compare notes.*
