# Contributing to Prompt Sentry

Thanks for considering a contribution. This is a small, focused project, so the bar for getting a change merged is mostly just: does it work, is it tested, and does it match the style already in the codebase.

## Getting set up

```bash
git clone https://github.com/JOSIAHTHEPROGRAMMER/prompt-sentry.git
cd prompt-sentry
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Add at least one provider API key to `.env` if you want to run real scans. The test suite itself does not need any keys, since every provider and judge call is mocked.

## Before opening a pull request

Run the full check locally, the same three commands CI runs:

```bash
ruff check src tests
mypy src
pytest tests -v --cov=prompt_sentry --cov-report=term-missing
```

All three should pass cleanly. Coverage should not drop below 90 percent, that is the gate CI enforces.

## Code style

* Type hints on every function signature. `mypy` runs in strict mode (`disallow_untyped_defs`) and will fail otherwise.
* Line length is capped at 100 characters, enforced by ruff.
* Favor explicit code over clever code. If a change needs a comment to explain what it does rather than why, it probably needs to be simpler instead.
* Comments explain reasoning, not mechanics. A comment like `# increment counter` adds nothing, a comment like `# retry once, free tier rate limits usually clear within a few seconds` explains a decision.
* New modules follow the pattern already in the codebase: a `base.py` for shared data shapes, dependency injection over global state (see how `Console` and `Provider` instances get passed into functions rather than constructed globally), and errors that get caught and wrapped rather than left to crash a whole scan.

## Adding a new provider

1. Add the default model and API key handling to `src/prompt_sentry/utils/config.py`, following the pattern already used for Groq, Gemini, and Mistral.
2. Create `src/prompt_sentry/providers/your_provider.py`, subclassing `Provider` from `providers/base.py` and implementing only `_call_api`. Timing and error wrapping are handled by the base class already.
3. Register the new provider in `PROVIDER_CLASSES` in `src/prompt_sentry/cli/main.py` and in `PROVIDER_NAMES` in `src/prompt_sentry/cli/parser.py`.
4. Add a mocked test file under `tests/`, following the pattern in `tests/test_groq_provider.py`. Never call the real API in a test.

## Adding a new attack

Attacks are plain data, not classes. To add one:

1. Open the relevant category file under `src/prompt_sentry/attacks/` (for example `injection.py` for a new prompt injection technique).
2. Add a new `Attack` entry to that file's tuple, with a unique `id`, a clear `name`, the `prompt` itself, a `description` explaining what the attack is testing and why it works, and at least one entry in `references` pointing to a real, verifiable OWASP or MITRE ATLAS citation.
3. Do not invent a citation. If you cannot confirm a specific technique id from a primary source, cite the closest accurate umbrella category instead and note the gap in a comment, the same approach already used in a few places in this codebase.
4. The existing tests in that category's test file (uniqueness, non empty prompts, at least one reference) will run automatically against your new entry, no new test code required unless you are adding a whole new category.

## Adding a new attack category

This is a larger change. It touches the `AttackCategory` enum in `attacks/base.py`, a new category file, the registry aggregation in `attacks/registry.py`, and the CLI's `--attack-category` choices. Open an issue first to discuss the category before writing the attacks themselves, since the framework citations should be settled before the payloads are.

## Commit messages

Short, imperative, lower case, in the style of `feat: add mistral provider` or `fix: wrap long line in judge prompt template`. Doesn't need to be strict conventional commits, just clear about what changed and why at a glance.

## Reporting a bug

Open an issue with the command you ran, the full output, and your Python version. If it involves a specific provider's API response, redacting any real API keys from the output is appreciated, though none of the SDKs used here echo the key back in error messages under normal circumstances.
