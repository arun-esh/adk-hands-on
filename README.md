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
| `step00-setup` | Install and get your key |
| `step01-create-agent` | Create your first agent with `adk create` |
| `step02-gatekeeper` | Turn it into a gatekeeper that signs people in |
| `step03-roles` | After login, each role gets its own agent with its own tools |
| `step04-guards` | You are here: a `before_agent_callback` checks the role in code before a role agent runs |

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

## Step 1: create your first agent
```bash
adk create store_ops_app      # pick backend 1 (Google AI), then accept the model
adk web .                     # open the URL it prints and pick store_ops_app
```
`adk create` asks for your API key. If you already exported `GOOGLE_API_KEY`, it shows that key in
brackets as the default, so do not share your screen at this prompt.

`adk create` writes a small agent: a model, a name, and an instruction. Ask it
"What is the shelf price of Toblerone?" and notice it can only guess. It has never
seen this store's shelves.

## Step 2: the gatekeeper
Nobody should reach the back office without signing in, so the agent becomes a **gatekeeper**: it
welcomes you, asks for a username and password, and checks them with a `verify_user` tool.

```bash
adk web .       # pick store_ops_app, say hi, then sign in
```
👉 The demo logins and things to try are in [`store_ops_app/README.md`](store_ops_app/README.md).

## Step 3: one agent per role
After sign-in the gatekeeper hands you to the agent for your role. Each agent only has the tools
that role may use, so a staff member cannot see sales because their agent has no sales tool.

| Role | Agent | Tools | Files |
|---|---|---|---|
| staff | `staff_agent` | `get_product_details`, `get_low_stock` | `sub_agents/staff_agent.py`, `tools/staff_role_tools.py` |
| manager | `manager_agent` | the staff tools + `get_sales_summary`, `get_top_sellers` | `sub_agents/manager_agent.py`, `tools/manager_role_tools.py` |
| owner | `owner_agent` | the manager tools + `get_revenue` | `sub_agents/owner_agent.py`, `tools/owner_role_tools.py` |

`agent.py` still holds the gatekeeper. It lists the three role agents with `sub_agents=[...]`.

The data is plain JSON in `store_ops_app/data/`: `products.json` (10 products) and `sales.json`
(30 days of sales). Everything is read-only.

```bash
adk web .       # pick store_ops_app, say hi, sign in (logins are in store_ops_app/README.md), then try:
```
- staff (`sam`): `What is the price of Toblerone?`, `Which items are low on stock?`, then `What sold best last week?` (refused)
- manager (`daniel`): `Top 3 sellers over the last 30 days?`, then `How much revenue did we make?` (refused)
- owner (`maya`): `How much revenue did we make in the last 30 days?`

Each role agent is set with `disallow_transfer_to_peers=True`, so one role cannot hand you sideways to another.

## Step 4: guard the doors with `before_agent_callback`
Up to step 3, the hand-off from the gatekeeper to a role agent was the model's decision. A model can
be talked into the wrong choice, so now plain code checks it too.

1. `verify_user` writes `user_role` and `user_name` into session state (it only does this on a correct login).
2. `guards.py` has `require_role("owner")`: a `before_agent_callback` that reads the role from state.
3. Each role agent has its own guard. If the role does not match, the agent never runs and the user
   gets "Sorry, that isn't available for your role."

The model never writes `user_role`, so no message can change it.

Check it without any model calls:

```bash
python -m tests.test_guards
```

Not covered by that test: a live chat in `adk web` (staff logs in, then asks for the owner agent).

## Troubleshooting
- **API key error / 403:** check `.env` has no quotes or spaces around the key, and that you restarted `adk web` after editing it.
- **429 / quota error:** free keys have rate limits. Wait a minute and retry.
- **`adk: command not found`:** activate the virtual environment (`source .venv/bin/activate`).
- **Install fails or `No module named ...`:** check `python3 --version` is 3.11 or newer, then run `pip install -r requirements.txt` again inside the activated virtual environment.
