# 🍁 Maple Lane Corner Market
### *Open late. Stocked right. Run by agents.*

```
  ╔════════════════════════════════════════════╗
  ║     M A P L E   L A N E   M A R K E T      ║
  ║   ──────────────────────────────────────   ║
  ║    Mon–Sat  6:00 am – 12:00 am             ║
  ║    Sunday   8:00 am – 10:00 pm             ║
  ║    📍 Corner of Maple & 4th                ║
  ╚════════════════════════════════════════════╝
```

**Welcome, Owner!** 👋 You run a busy neighbourhood convenience store: a shelf full
of products, a small team, and never enough hours in the day.
Today you'll build a team of AI assistants to run the back office with Google's
**Agent Development Kit (ADK)**.

## 🗺️ Your shift, step by step
Each step is a git branch. Switch with `git checkout <branch>` and see what changed
with `git diff <previous-branch>`.

| Branch | What happens |
|---|---|
| `step00-setup` | You are here: install and get your key |

> 🔔 *Opening bell: finish setup below before the talk. Conference wifi is slow!*

## Setup (do this before the talk, conference wifi is slow)

**1. Install** (Python 3.11+):
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Get a free Gemini API key**
1. Open https://aistudio.google.com/apikey and sign in with a Google account.
2. Click **Create API key** and copy it.

**3. Give the key to ADK**: one key works for all steps and all agents.
```bash
cp .env.example .env
# open .env and replace paste-your-key-here with your key
```
Alternative: `export GOOGLE_API_KEY=your-key` in the terminal (this overrides `.env`).

Never commit `.env` or share your key.

**4. Check it works**
```bash
adk --version
```
You should see a version number.

## Troubleshooting
- **API key error / 403:** check `.env` has no quotes or spaces around the key, and that you restarted `adk web` after editing it.
- **429 / quota error:** free keys have rate limits. Wait a minute and retry.
- **`adk: command not found`:** activate the virtual environment (`source .venv/bin/activate`).
- **Install fails or `No module named ...`:** check `python3 --version` is 3.11 or newer, then run `pip install -r requirements.txt` again inside the activated virtual environment.
