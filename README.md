# SluzBot

Rychlý služebníček pro posílání služeb do bastlírenského Slacku.

## Potřebné proměnné

- `CSV_URL` – URL CSV souboru se službami; bere se hodnota z buňky A22 (sloupec A, řádek 22).
- `SLACK_WEBHOOK_URL` – Slack incoming webhook, kam se má zpráva poslat.

## Volitelné proměnné

- `LOG_LEVEL` – úroveň logování pro loguru (např. DEBUG, INFO, WARNING, ERROR). Výchozí je `INFO`.
- `FORCE_UTF8` – pokud je nastaveno na `1`, `true` nebo `yes`, vynutí dekódování staženého CSV jako UTF-8. Výchozí chování je použít kódování odpovědi nebo její apparent_encoding.

## Ukázkové .env

```env
CSV_URL=https://example.com/services.csv
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
# Volitelné:
LOG_LEVEL=INFO
FORCE_UTF8=0
```