# Contributing

Thanks for improving VideoForge Agent.

1. Open an issue before a large behavioral change.
2. Create a focused branch from `main`.
3. Install with `python -m pip install -e ".[dev]"`.
4. Add tests and run `make check`.
5. Submit a small pull request explaining tradeoffs and validation.

Do not commit copyrighted source footage, model weights, generated videos,
credentials, or OAuth tokens. New publisher adapters must remain behind the
explicit publish approval gate and include a dry-run test.
