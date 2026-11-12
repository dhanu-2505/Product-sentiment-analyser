# Scraping methodology

The platform follows a layered scraper strategy:

1. Try the platform-specific adapter or scraper.
2. Validate that the result includes a normalized product and review payload.
3. If the live source fails, fall back to generated mock data.
4. Process the same review text through the sentiment and analytics pipeline.

This ensures product intelligence remains available even when live scraping is blocked or rate-limited.

## Guardrails

- Respect site terms and rate limits.
- Do not bypass authentication or CAPTCHA checks.
- Cut off or fail gracefully when the remote service is unavailable.
- Prefer mock data only as an explicit fallback path.
