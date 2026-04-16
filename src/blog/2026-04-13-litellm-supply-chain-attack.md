---
title: "LiteLLM Got Backdoored. Your Agent Infrastructure Might Already Be Compromised."
date: 2026-04-14
description: "The LiteLLM supply chain attack slipped credential-harvesting malware into 1.82.7 and 1.82.8. Here's what actually happened, who got hit, and what you need to check right now."
author: "TopClanker"
tags: [security, supply-chain, litellm, agent-infrastructure]
---

On March 24, 2026, two new versions of LiteLLM landed on PyPI: **1.82.7 and 1.82.8**. Both were malware.

LiteLLM is the library that tens of thousands of local AI agent builders use every day — it's a universal proxy that converts API calls for 100+ LLMs into OpenAI format. If you're running Ollama behind a LiteLLM proxy, or routing multiple providers through it, you're in the affected group. The packages were uploaded at 08:30 UTC and quarantined by PyPI at 11:25 UTC. Three hours. That's all it took for 97 million monthly downloads to be at risk.

## What the Malware Actually Did

The TeamPCP threat actor — the same group behind the Trivy and KICS supply chain attacks — used a maintainer account compromised via the prior Trivy incident to publish the poisoned packages.

Version 1.82.7 dropped a double base64-encoded payload to disk (`p.py`) and executed it whenever `litellm --proxy` ran or `litellm.proxy.proxy_server` was imported.

Version 1.82.8 went further. It abused Python's `.pth` file mechanism, which runs arbitrary code during interpreter initialization. The malicious `litellm_init.pth` file triggered on *any* Python invocation on the system — not just when LiteLLM was explicitly called. Open a Python script for unrelated work? The malware ran.

Once active, the payload systematically harvested:

- Environment variables (API keys, tokens)
- SSH keys (`~/.ssh/`)
- Cloud credentials: **AWS, GCP, Azure**
- Kubernetes configs
- CI/CD secrets (GitHub Actions, GitLab, etc.)
- Docker configurations
- Database connection strings
- Cryptocurrency wallets

Data was encrypted with AES-256, the key further encrypted with an embedded RSA public key, and exfiltrated to attacker-controlled domains: `checkmarx[.]zone` (1.82.7) and `models[.]litellm[.]cloud` (1.82.8).

## The Transitive Dependency Problem Nobody Talks About

PyPI pulled the packages fast. But the damage window was real — and the cascade is what makes this interesting for agent builders specifically.

GitGuardian found that **1,705 PyPI packages were configured to automatically pull the compromised LiteLLM versions as transitive dependencies**. Packages you've never heard of, installed as sub-dependencies of tools you do use, were triggering malware execution silently.

Packages affected:
- **dspy** — 5 million monthly downloads
- **opik** — 3 million monthly downloads
- **crawl4ai** — 1.4 million monthly downloads

If any of those are in your agent's dependency tree, you were exposed even if you never installed LiteLLM directly. That's supply chain depth most agent developers haven't modeled.

## Why Developer Endpoints Are the Target

The LiteLLM attack is the latest example of a pattern that's been accelerating: adversaries targeting the machine where credentials accumulate, not the network perimeter.

When GitGuardian analyzed 6,943 compromised developer machines from a prior campaign, researchers found **33,185 unique secrets** — with at least 3,760 still valid at the time of analysis. More striking: each valid secret appeared in roughly eight different locations on the same machine. The same AWS key in `.env`, in `~/.aws/credentials`, in a shell profile, in an agent's memory store.

For local AI agent builders, this is the real alert: your dev workstation is dense with credentials because you need them there. Model provider keys. Cloud access tokens. API secrets for tools your agents call. And if you're running local LLMs with LiteLLM as your proxy layer, you're adding one more trusted pathway that attackers know to probe.

## What You Need to Check Right Now

If you've touched LiteLLM in the past 30 days, work through this:

**1. Check your installed version.**
```bash
pip show litellm
```
If it's 1.82.7 or 1.82.8, you're in the blast radius. Update immediately:
```bash
pip install --upgrade litellm>=1.82.9
```

**2. Audit your dependency tree.**
```bash
pip install pipdeptree
pipdeptree | grep -i litellm
```
Check every package that pulls LiteLLM in as a sub-dependency. If dspy, opik, crawl4ai, or anything else in your stack touched a compromised version, assume exposure.

**3. Rotate every credential that touched a machine running those versions.**
This means: every model API key, cloud credential, SSH key, and secrets store access token that existed on that host. Don't wait for IOCs. Assume compromise and rotate.

**4. Scan your filesystem for secrets that shouldn't be there.**
Use [ggshield](https://docs.gitguardian.com/) to scan project directories, home folders, and agent memory stores:
```bash
ggshield secrets scan path ~/
```
Pay special attention to directories where local AI agents store their state: agent config folders, log directories, memory files.

**5. Check your LiteLLM proxy logs.**
If your proxy was running during March 24–25 with a compromised version, the exfiltration may have already occurred. Review outbound connections from your proxy host to `checkmarx[.]zone` or `models[.]litellm[.]cloud` — those are the attacker domains.

## The Harder Problem: Credential Hygiene for Agent Builders

This attack exploited something deeper than a bad package. It exploited the fact that developer machines accumulate plaintext credentials by design.

Agents need credentials. Local LLMs need API keys. Tool-calling agents need cloud access. Retrieval-augmented agents need vector store connections. And on a dev workstation, all of those end up in `.env` files, shell profiles, IDE configs, and agent memory stores — often as plaintext because "it's just local."

The mitigation isn't just "don't install bad packages." It's reducing the credential surface area on the machine where you build and test agents:

- Use environment variable injection at runtime, not `.env` files committed to project trees
- Move model API keys into a secrets manager (1Password CLI, HashiCorp Vault, AWS Secrets Manager) rather than keeping them on disk
- Treat agent state directories (wherever your agent stores memory, context, and logs) as sensitive — don't let credentials accumulate there
- Set up `ggshield` pre-commit hooks to catch credential leaks before they enter version control
- Run agents in sandboxed environments when possible — the credential scope of a compromised agent is bounded by what it can access

## The Take

The LiteLLM supply chain attack is a reminder that your local AI stack isn't isolated just because it's running on your laptop. Every package you install, every dependency your tools pull in, every credential sitting in plaintext on disk is attack surface. The TeamPCP campaign — Trivy, KICS, now LiteLLM — shows this isn't opportunistic. Threat actors are systematically mapping the open-source toolchain and finding the nodes with the most credential density.

If you're running local AI agents in production or building tools for others who do, treat your dependency tree as a security perimeter. Audit it, pin it, and assume the next supply chain compromise is already in PyPI waiting to be discovered.

Rotate your keys. Check your versions. Then go lock down your agent's credential hygiene.

---

## Sources

- [Wiz: Three's a Crowd — TeamPCP trojanizes LiteLLM](https://www.wiz.io/blog/threes-a-crowd-teampcp-trojanizes-litellm-in-continuation-of-campaign)
- [The Hacker News: How LiteLLM Turned Developer Machines Into Credential Vaults](https://thehackernews.com/2026/04/how-litellm-turned-developer-machines.html)
- [OX Security: LiteLLM PyPI Malware Steals Cloud, Crypto, Slack, and Discord Keys](https://www.ox.security/blog/litellm-malware-malicious-pypi-versions-steal-cloud-and-crypto-credentials/)
- [GitGuardian: TeamPCP snowball analysis — 1,705 packages with LiteLLM dependency](https://blog.gitguardian.com/team-pcp-snowball-analysis/)
- [PyPI Security Advisory](https://github.com/pypa/advisory-database/blob/b0f7a727494c977b29c998bc9199de5891f8f302/vulns/litellm/PYSEC-2026-2.yaml)
- [LiteLLM Official Security Update (March 25, 2026)](https://docs.litellm.ai/blog/security-update-march-2026)
