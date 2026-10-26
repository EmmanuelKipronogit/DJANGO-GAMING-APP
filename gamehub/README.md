# Number Guess: Django + PostgreSQL

Users create accounts and play a number-guessing game written in Python. The server picks a secret number
from 1 to 100 and the player has 7 guesses, with "higher" or "lower" hints after each one. Fewer guesses
means more points, and a leaderboard ranks players.

- Accounts: sign up, log in, log out (Django auth)
- Game rules in plain Python: `game/logic.py`
- Secret number stays on the server and is never sent to the browser while playing
- One active game per player, enforced by a database constraint
- Guess handling locks the game row, so rapid double-submits can't cheat the attempt limit
- Admin at `/admin/` for browsing games and guesses

## Run it locally

You need Python 3.10+ and PostgreSQL 14+ (or Docker).

```bash
# 1. Database (pick one)
docker compose up -d
#   ...or, with Postgres installed locally, in psql:
#   CREATE USER gamehub WITH PASSWORD 'gamehub' CREATEDB;
#   CREATE DATABASE gamehub OWNER gamehub;

# 2. Python environment
python -m venv venv
source venv/bin/activate            # Windows PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Settings
cp .env.example .env                # Windows PowerShell: copy .env.example .env
# set DJANGO_SECRET_KEY, and change DB_* if your Postgres differs

# 4. Tables, admin user, run
python manage.py migrate
python manage.py createsuperuser    # optional
python manage.py runserver
```

Open http://127.0.0.1:8000

Run the tests (they run on Postgres and need the `CREATEDB` permission on the database user):

```bash
python manage.py test
```

## Deploying

Set these environment variables on your host, and don't upload `.env`:

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<long random string>
DJANGO_ALLOWED_HOSTS=yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com
DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT
```

Then:

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi
```

Static files are served by WhiteNoise. Use a managed Postgres in production for backups.
Generate a secret key with:
`python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`

## Layout

```
config/            settings, root urls
game/logic.py      the game rules (pure Python)
game/models.py     GameSession, Guess
game/views.py      signup, play, guess, leaderboard
game/templates/    HTML pages
game/tests.py      logic + flow tests
```

## Ideas to extend

Difficulty levels (change the range and attempts in `logic.py`), a daily challenge, email verification
and password reset, or a different Python game by replacing `logic.py` and the play view.
