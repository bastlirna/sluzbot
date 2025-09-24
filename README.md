# SluzBot

Rychlý služebníček pro posílání služeb do bastlírenského Slacku.

## Potřebné proměnné

- `CSV_URL` – URL CSV souboru se službami; bere se hodnota z buňky A22 (sloupec A, řádek 22).
- `SLACK_WEBHOOK_URL` – Slack incoming webhook, kam se má zpráva poslat.

## Ukázkové .env

```env
CSV_URL=https://example.com/services.csv
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```