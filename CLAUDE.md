# CLAUDE.md - Kluvs Discord Bot

## Quick Start

**Core files:**
- `bot.py::BookClubBot` — Main bot
- `cogs/` — Commands (general, session, admin)
- `api/bookclub_api.py` — Supabase API client
- `config.py::BotConfig` — Configuration
- `tests/` — Unit tests

**Commands:**
```bash
make test          # Run tests
make coverage      # Coverage report
make run           # Run bot
```

**Environment:**
```
ENV=dev
DEV_TOKEN=your_token
KEY_SUPABASE=your_key
KEY_OPEN_AI=your_key
DEV_SUPABASE_URL=your_url
URL_EDGE_FUNCTION=your_edge_function_url
```

## Architecture

**Cog pattern:** Commands organized by area (general, session, member, admin)

**Service layer:** `OpenAIService` (GPT), `BookClubAPI` (REST client)

**API client:** Custom exceptions, retry logic, guild-aware ops

**Database (Supabase):** Servers, Clubs, Members, Sessions, Books, Discussions

## Project Structure

```
kluvs-bot/
├── api/              # Supabase API client
├── cogs/             # Commands (general, session, member, admin)
├── events/           # Message handlers
├── services/         # OpenAI integration
├── tests/            # Unit tests
├── utils/            # Utilities
├── bot.py            # Main bot
├── config.py         # Config
└── main.py           # Entry point
```

## Code Patterns

**Error handling:** Custom exceptions from `api.bookclub_api`, user-friendly messages from `utils.constants`

**Embeds:** Use `utils.embeds.create_embed()` with colors from `utils.constants.COLORS`

**Async:** All commands/interactions are async; use `AsyncMock` in tests

**Logging:** Daily rotating logs in `logs/bot.log` with context (guild_id, user_id)

## Testing

```bash
python tests/run_tests.py              # Run all
coverage run --source=. tests/run_tests.py && coverage report  # With coverage
python -m unittest tests.test_bookclub_api  # Specific module
```

## When Working Here

1. **Always run tests** before changes
2. **Add tests** for new features
3. **Follow existing patterns** (cogs, services, API structure)
4. **Use user-friendly messages** from constants
5. **Log with context** (guild_id, user_id)
6. **Update CLAUDE.md** for architecture changes

## External Services

- **Discord API** — Bot interface
- **Supabase** — PostgreSQL + Edge Functions
- **OpenAI GPT-3.5** — Summaries & chat
