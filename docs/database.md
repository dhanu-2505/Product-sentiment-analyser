# Database design

The project currently uses SQLite for local development and preserves PostgreSQL-ready configuration through the `database_url` setting.

## Primary tables

- `products`
- `reviews`
- `sentiment_results`
- `analysis_history`
- `users`
- `saved_products`
- `search_history`

## Relationships

- One product has many reviews.
- One review has one sentiment result.
- One user has many saved products.
- One user has many search history items.

## Notes

The schema is intentionally lightweight while still supporting product analysis, review persistence, and user-level saved items. For managed production deployment, the same models can be pointed to PostgreSQL with minimal configuration changes.