# Sentiment analysis

The sentiment engine uses VADER, a lexicon-based sentiment model designed for social and product review text.

## Score interpretation

- compound >= 0.05 => positive
- compound <= -0.05 => negative
- otherwise => neutral

## Stored signals

Each review stores:

- `sentiment_label`
- `sentiment_score`
- `compound_score`
- `positive_score`
- `neutral_score`
- `negative_score`

These values are used in summary metrics, dashboard cards, and review filtering.