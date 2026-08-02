# Prompt Sentry

A red teaming tool for evaluating and comparing how different LLM APIs respond to common security attacks, including prompt injection, jailbreaks, role manipulation, data extraction, system prompt leakage, and encoding based obfuscation.

[![Tests](https://github.com/JOSIAHTHEPROGRAMMER/prompt-sentry/actions/workflows/tests.yml/badge.svg)](https://github.com/JOSIAHTHEPROGRAMMER/prompt-sentry/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-blueviolet)](https://github.com/astral-sh/ruff)

## Overview

Prompt Sentry runs a library of adversarial prompts against multiple LLM providers (currently Groq, Gemini, and Mistral) and uses a second LLM as an automated judge to classify how each response held up. It was built to demonstrate practical AI security testing, not just prompt engineering: every attack in the library is mapped to a real framework reference (OWASP's LLM Top 10 or MITRE ATLAS), and the judging methodology was designed specifically to avoid a documented failure mode of LLM as judge setups, a model favoring its own output when asked to grade itself.

The result of a scan is a structured JSON report plus a readable console summary, comparing resistance rates, average severity, and category level breakdowns across every provider tested.

## Features

**Modular attack library**
48 attacks across six categories: prompt injection, jailbreaks, role manipulation, data extraction, system prompt leakage, and encoding or obfuscation based evasion. Every attack cites the specific OWASP LLM Top 10 category and MITRE ATLAS technique it demonstrates.

**Multi provider support**
Groq, Gemini, and Mistral are supported out of the box, each behind a shared `Provider` interface. Adding a new provider means writing one small subclass, nothing else in the codebase needs to change.

**LLM as judge scoring**
Each response is graded by a randomly selected provider other than the one that generated it, so no provider ever judges its own output by default. Every scored result records which model judged it and whether self judging occurred, so the methodology stays fully visible in the report rather than hidden behind a single opaque score.

**Structured and human readable output**
Every scan produces a timestamped JSON report under `reports/` and a color coded console summary built on `rich`, including per provider resistance rates, average severity, and category breakdowns.

**Flexible CLI**
Run the entire library, a single category, or specific attacks by id, against one provider or all configured providers, with optional rate limiting between calls.

## Architecture

```
src/prompt_sentry/
    providers/        Provider abstraction plus Groq, Gemini, and Mistral implementations
    attacks/           The attack library, one file per category, aggregated into a registry
    scoring/           LLM as judge logic, severity aggregation, and per provider summaries
    reporting/         JSON export and console rendering
    cli/               Argument parsing and scan orchestration
    utils/             Environment and settings loading

tests/                 Mocked unit tests, no real API calls
```

**Design principles worth calling out**

*Providers never judge themselves by default.* Research on LLM as judge setups has found that models tend to favor their own output when evaluating it. Rather than accept that bias silently, the judge is chosen at random from the providers not being scored, and every result records `judged_by` and `self_judged` so the methodology is auditable, not assumed.

*Errors never crash a scan.* A single failed API call, whether from the provider under test or from the judge, is caught, retried once, and recorded as a structured error on that one result. A rate limited call on attack 30 of 48 does not lose the other 47.

*Attacks are data, not behavior.* Each attack is a plain, immutable record: an id, a category, a prompt, a description, and its citations. Sending the prompt is the provider's job and judging the response is the scorer's job, so the attack library itself stays a simple, reviewable list rather than a class hierarchy.

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/JOSIAHTHEPROGRAMMER/prompt-sentry.git
cd prompt-sentry
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows, activate the virtual environment with `.venv\Scripts\activate` instead.

## Configuration

Copy the example environment file and add your own API keys. All three providers offer a free tier.

```bash
cp .env.example .env
```

```
GROQ_API_KEY=
GEMINI_API_KEY=
MISTRAL_API_KEY=
```

You do not need all three keys configured. Prompt Sentry will run against whichever providers have a key set and will tell you clearly if you request one that does not.

Keys are sourced from:
* Groq: https://console.groq.com/keys
* Gemini: https://aistudio.google.com/apikey
* Mistral: https://console.mistral.ai/api-keys

## Usage

List every attack in the library without making any API calls:

```bash
prompt-sentry --list
```

Run one specific attack against one provider:

```bash
prompt-sentry --provider groq --attack injection-ignore-previous-instructions --verbose
```

Run an entire category against every configured provider:

```bash
prompt-sentry --attack-category jailbreak --json
```

Run the full library against everything, exporting a JSON report and spacing calls out to stay under free tier rate limits:

```bash
prompt-sentry --all --json --delay 2
```

### CLI reference

| Flag | Description |
|---|---|
| `--provider` | Limit the scan to this provider. Repeatable. Defaults to every provider with a key configured. |
| `--attack` | Run this specific attack by id. Repeatable. |
| `--attack-category` | Run every attack in this category. Repeatable. |
| `--all` | Run the entire attack library. |
| `--list` | Print every available attack and category, then exit without scanning. |
| `--json` | Export the scan report as JSON under `reports/`. |
| `--verbose` | Print a detailed per attack table alongside the summary. |
| `--judge` | Force this provider to judge every response, bypassing random non self judge selection. |
| `--delay` | Seconds to wait between each attack, useful for staying under free tier rate limits. |

## Sample output

```
                     Prompt Sentry Scan Summary — 2026-08-01T18:58:34+00:00
┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Provider ┃ Total ┃ Resisted ┃ Partial ┃ Compromised ┃ Errors ┃ Resistance Rate┃ Avg Severity ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ groq     │ 48    │ 31       │ 1       │ 7           │ 9      │ 79%            │ 11.2         │
│ gemini   │ 48    │ 38       │ 1       │ 9           │ 0      │ 79%            │ 14.6         │
│ mistral  │ 48    │ 12       │ 1       │ 11          │ 24     │ 50%            │ 36.7         │
└──────────┴───────┴──────────┴─────────┴─────────────┴────────┴────────────────┴──────────────┘
```

Every result in the underlying JSON report includes the full attack prompt, the provider's full response, the verdict, the severity score, which model judged it, and the judge's reasoning, so a finding can always be traced back to exactly what was asked and what came back.

## Testing

The full test suite mocks every provider SDK and every judge call. No test in this repository makes a real network request, so it runs the same way locally and in CI, with no API keys required.

```bash
pytest tests -v --cov=prompt_sentry --cov-report=term-missing
```

Linting and type checking:

```bash
ruff check src tests
mypy src
```

The project currently sits at 130 tests with roughly 98 to 100 percent coverage across every module.

## Continuous integration

Every push and pull request runs lint, type checking, and the full test suite across Python 3.10 through 3.14 on GitHub Actions. See the badge at the top of this file or the [workflow file](.github/workflows/tests.yml) for details. No secrets are required to run CI, since every test is fully mocked.

## Future work

* Additional providers (Cerebras, OpenRouter, local models via Ollama)
* Multi turn attack simulation, running a sequence of prompts within a single conversation rather than one shot payloads
* A `--compare` mode that diffs two prior JSON reports to track whether a provider's resistance has changed over time
* An ensemble judging mode using more than one judge per result, for higher confidence scoring at the cost of additional API calls

## Security disclaimer

This tool is built for authorized security research and evaluation of publicly available LLM APIs. The attack library contains prompts designed to probe known weaknesses including jailbreaks, prompt injection, and data extraction techniques, some of which reference genuinely dangerous topics because a red teaming tool that only tests trivial cases does not demonstrate anything meaningful.

Do not use this tool against any system you do not own or have explicit permission to test. The authors are not responsible for misuse. Running this tool against a provider's API is subject to that provider's own terms of service and rate limits.

## Findings report template

When documenting results from a scan, the following structure is a reasonable starting point for a writeup:

```
## Scan Summary
Date:
Providers tested:
Total attacks run:

## Key Findings
1. [Provider] showed the lowest resistance rate at [X]%, concentrated in [category].
2. [Provider] fully resisted [category] but showed partial compliance under [attack type].
3. [Notable individual result, attack id, verdict, and why it matters]

## Category Breakdown
| Category | Groq | Gemini | Mistral |
|---|---|---|---|
| Prompt Injection | | | |
| Jailbreak | | | |
| Role Manipulation | | | |
| Data Extraction | | | |
| System Prompt Leak | | | |
| Encoding Obfuscation | | | |

## Recommendations
[Guidance based on the findings, for example which provider is better suited
to a use case with a higher risk profile]
```

## License

MIT
