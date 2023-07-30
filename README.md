# KP Checker

Automated tool to check Polish residence permit status on [klient.gdansk.uw.gov.pl](https://klient.gdansk.uw.gov.pl) and notify about updates in Telegram

## How to run

```bash
# Copy and fill keys and passwords
cp secret-example.env secret.env

# Copy and fill klient.gdansk.uw.gov.pl login data and telegram ID
cp mongo-init-example.js mongo-init.js

# Run in docker
docker compose up -d

# Add the following command to cron (daily/hourly is recommended)
docker start kp_checker
```

### secret.env

- `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD` - root auth data for MongoDB. No separate user is created for the app, root is used
- `TELEGRAM_API_TOKEN` - Telegram bot token. [See here](https://core.telegram.org/bots/tutorial#obtain-your-bot-token) on how to create a bot and get it.
- `TELEGRAM_ADMIN_ID` - ID of the user that would receive all updates and error reports. You can find your own ID by [@userinfobot](https://t.me/userinfobot)

### mongo-init.js

This file initializes MongoDB with the list of users that would be checked. For each user you need:

- `name` - any **unique** display name that would be shown in the report (also used for query filtering)
- `login`, `password` - user auth data for [klient.gdansk.uw.gov.pl](https://klient.gdansk.uw.gov.pl) ⚠️
- `telegram` - user telegram ID. You can find your own ID by [@userinfobot](https://t.me/userinfobot)

`data` field would store last known state. You can always add more users to db manually (accessible over 27017 port).

## Warning ⚠️

Your [klient.gdansk.uw.gov.pl](https://klient.gdansk.uw.gov.pl) password is stored with **NO encryption** in MongoDB. Think twice before running this in any unsafe environment. You've been warned.

---

## Tech

Uses python with selenium chrome emulator to log in onto the website and fetch the data. Stores it in MongoDB, sends update notifications over Telegram.

If you want to run the python script locally outside of a container, set the same env vars and change connection strings from docker network to `localhost`:

- `http://chrome:4444/wd/hub` -> `http://localhost:4444/wd/hub`
- `mongodb://{username}:{password}@mongo:27017/` -> `mongodb://{username}:{password}@localhost:27017/`
