# Contributing

Thanks for considering a contribution to Aletheia.

## Development setup

1. Use Python 3.11 and a supported Node.js version.
2. Create a virtual environment and install `requirements-dev.txt`.
3. Copy `.env.example` to `.env` and keep all secrets local.
4. Install the desktop dependencies with `cd ui && npm ci`.

## Before opening a pull request

Run from the repository root:

```bash
pytest -q
python -m compileall -q app desktop_agent tests
```

Run for UI changes:

```bash
cd ui
npm run lint
npm run build
```

## Contribution guidelines

- Keep changes focused and preserve existing user data and configuration.
- Do not commit `.env`, access tokens, local memory, audio, model weights, build output or dependency folders.
- Add tests for deterministic behavior and regression fixes.
- Avoid tests that call real hosted services or require a downloaded LLM.
- Update documentation when configuration, API behavior or setup steps change.
- Describe what was tested and what remains unverified in the pull request.

## Pull request checklist

- [ ] Scope and motivation are clear.
- [ ] Tests cover changed behavior.
- [ ] Existing API contracts remain compatible or changes are documented.
- [ ] No secrets or personal runtime data are included.
- [ ] README/docs are updated where necessary.
