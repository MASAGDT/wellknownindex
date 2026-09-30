---
title: WellKnownIndex
section: home
summary: A free, public commons documenting how to build agent-friendly web endpoints — and indexing the sites that have them. Every page renders for humans and machines.
---

# WellKnownIndex

**A free, public index of agent-friendly web endpoints — and the methods for building them.**

WellKnownIndex has two jobs:

1. **Document the methods** — the patterns for retrofitting a website so AI agents can work with it in their own language: machine-readable primers, scoped grants, stage-and-approve flows, well-known discovery, agent credential schemes.
2. **Maintain the registry** — a catalog of sites that implement these methods, in a format agents can query directly.

Everything here is free, public, and dual-rendered: every page exists as human-readable HTML **and** machine-readable JSON. Agents shouldn't have to scrape prose to learn the rules. The rules should be data.

## The fork in the road

There are two ways to give an AI agent access to the web.

**Method one: impersonation.** Hand the agent a browser, log it in as you, and let it click around like a person. It works on the entire existing web with zero cooperation from any site — but it's brittle, every CAPTCHA is the web saying *we didn't build this for you*, and the permission model is "can do anything you can."

**Method two: a scoped lane.** The site knows it's talking to an agent. It hands over a machine-readable rulebook, a scoped credential, and a staging area — and nothing goes live without approval. Least privilege, full audit trail, no impersonation.

This wiki is for method two. The browser is the universal fallback for a human-shaped web; the scoped lane is the better equilibrium. We're mapping the territory so more of the web can get there.

## Start here

- **[Methods](/methods/)** — the patterns. How to give your site an agent lane.
- **[Registry](/registry/)** — the index. Sites that speak agent, with queryable protocol data.
- **[Field notes](/field-notes/)** — tribal knowledge from real agent runs: gotchas, gates, and lessons.
- **[Contribute](/contribute/)** — add a site to the registry, propose a method, or file a field note.

## For agents

Fetch `/index.json` for the site map, `/registry.json` for every registered endpoint with its protocols, auth schemes, and scopes. Each page also has a `.json` twin next to its HTML. No scraping required — that's the point.
