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
| `step04-guards` | A `before_agent_callback` checks the role in code before a role agent runs |
| `step05-parallel` | The owner's morning briefing, built by helpers that run at the same time |
| `step06-schema` | Helpers hand over validated reports (`output_schema`), so code can read them |
| `step07-critic` | A writer and a critic loop until the reorder message is right |
| `step08-a2a` | You are here: the order goes to a separate supplier agent over A2A |

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

A refused user is handed back to the gatekeeper. Without that, ADK keeps the conversation with the
agent that spoke last, so the user would stay stuck behind the refusal.

Check it without any model calls:

```bash
python -m tests.test_guards
```

Not covered by that test: a live chat in `adk web` (staff logs in, then asks for the owner agent).

## Step 5: a morning briefing, built in parallel
The owner can ask for a morning briefing. Three small helpers each do one job at the same time, then a
writer turns their answers into one short note.

```
briefing_agent (Sequential, owner only)
 ├─ gather_facts (Parallel)
 │    ├─ stock_checker    -> state["stock_report"]
 │    ├─ sales_checker    -> state["sales_report"]
 │    └─ revenue_checker  -> state["revenue_report"]
 └─ briefing_writer  reads the three reports from state
```

- `ParallelAgent` runs its helpers at the same time. Each saves its answer with `output_key`.
- `SequentialAgent` fixes the order: gather first, then write. No model decides that order.
- The writer's instruction uses `{stock_report}`, `{sales_report}` and `{revenue_report}`, which ADK fills from state.
- The files live in `sub_agents/briefing/`: one file per helper, plus `briefing_agent.py` that builds the pipeline.
- `owner_agent` calls the whole pipeline as a tool (`AgentTool`), so the owner stays in the conversation afterwards.
- The pipeline has the owner guard from step 4, so only the owner can start it.
- `revenue_alert.py` is code that reads the revenue helper's text and flags low revenue for the writer. Reading a number out of a sentence is fragile: if the revenue tool fails, the helper writes "Unable to retrieve total revenue for the last 7 days..." and the code finds the `7`, so the owner gets a false "revenue looks low ($7)" alert. `python -m tests.test_briefing` shows this as `KNOWN BREAK`. Step 6 fixes it with a schema.

Check it without any model calls (a fake model proves the helpers overlap and the reports reach the writer):

```bash
python -m tests.test_briefing
```

Try it: sign in as `maya` and say `Give me the morning briefing`.

## Step 6: hand-offs with a schema
Step 5 passed sentences between agents. When code reads a sentence it has to guess, and it guessed wrong:
the error text "Unable to retrieve total revenue for the last 7 days" became a false "$7" alert.

Now each helper has an `output_schema` (`briefing/reports.py`), so what it saves in state is a validated dict:

```python
class RevenueReport(BaseModel):
    status: Literal["ok", "error"]
    total_cad: Optional[float] = None
    note: Optional[str] = None
```

- `revenue_alert.py` now checks `report["status"] == "ok"` and reads `total_cad`. An error report can never look like revenue.
- A helper that answers in free text fails validation instead of passing along silently.
- The writer still reads the reports through `{stock_report}` etc. in its instruction.

```bash
python -m tests.test_briefing   # fake model: no network, no model calls
```

Not covered by that test: a real Gemini model filling these schemas while it also calls a tool (ADK adds a `set_model_response` tool for this). Try it live: sign in as `maya` and say `Give me the morning briefing`.

## Step 7: a writer and a critic
The owner can ask for a reorder message to the supplier. A writer drafts it, a critic reviews it, and they
loop until the critic is happy or 3 rounds have passed.

```
reorder_agent (LoopAgent, owner only, max 3 rounds)
 ├─ reorder_writer   drafts the message        -> state["reorder_draft"]
 └─ reorder_critic   reviews it                -> state["critique"], or calls exit_loop
```

- The writer's instruction ends with `{critique?}`: the `?` means "empty on the first round".
- The review is split in two. The exact part (does the draft name every low-stock item?) is plain code in a tool,
  `check_reorder_items`. The fuzzy part (is it polite, is anything made up?) is the critic model's judgement.
- The critic stops the loop by calling `exit_loop`. `max_iterations=3` is the safety net.
- When the loop ends, plain code (`publish_draft`) returns the last draft, so no extra model call is needed.
- `owner_agent` calls the loop as a tool, and the owner guard from step 4 covers it.

```bash
python -m tests.test_reorder   # scripted fake models: no network, no model calls
```

Not covered by that test: how a real model behaves as writer and critic (does it fix the draft, does it ever approve too early?).
Try it live: sign in as `maya` and say `Draft a reorder message for the supplier`.

## Step 8: a supplier agent in another service (A2A)
The supplier is another company, so its agent runs as its own service. Our store agent only knows its address.

```
store_ops_app (owner_agent)  ── A2A over HTTP ──>  supplier_service (supplier_agent + its own catalogue)
```

- `supplier_service/` is a separate app: its own agent, its own tool (`check_availability`) and its own data. `a2a_app.py` serves it with `to_a2a(...)`.
- `store_ops_app/sub_agents/supplier_agent.py` is a `RemoteA2aAgent`: just a name and the URL of the supplier's agent card.
- `owner_agent` calls it as a tool: `AgentTool(agent=supplier_agent)`.
- Session state does not cross the boundary. Only the message goes over, so the supplier never sees the user's role or name.
  That is also why the guard in step 4 stays on our side: the supplier cannot enforce our roles.

Run the supplier in a second terminal, then use `adk web .` as before:

```bash
uvicorn supplier_service.a2a_app:a2a_app --port 8001
```

Try it: sign in as `maya` and say `Draft a reorder message for the supplier, then send it to the supplier`.
Golden Ring is backordered on purpose, so the supplier reply should say so.

```bash
python -m tests.test_a2a   # starts the supplier on localhost with a fake model: no model calls
```

Not covered by that test: how a real model uses the supplier's answer. Set `SUPPLIER_URL` if the supplier runs elsewhere.

## Troubleshooting
- **API key error / 403:** check `.env` has no quotes or spaces around the key, and that you restarted `adk web` after editing it.
- **429 / quota error:** free keys have rate limits. Wait a minute and retry.
- **`adk: command not found`:** activate the virtual environment (`source .venv/bin/activate`).
- **Install fails or `No module named ...`:** check `python3 --version` is 3.11 or newer, then run `pip install -r requirements.txt` again inside the activated virtual environment.
