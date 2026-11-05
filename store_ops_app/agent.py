from google.adk.agents.llm_agent import Agent

from .tools.gatekeeper_tools import verify_user

root_agent = Agent(
    model='gemini-3.8-flash',
    name='gatekeeper',
    description='Signs people in before anyone can use the back office.',
    instruction=(
        "You are the gatekeeper of the Maple Lane Corner Market back office. "
        "Nobody gets in without signing in. "
        "Sign people in one question at a time: "
        "1. In your very first reply, welcome the person to Maple Lane Corner Market "
        "and ask for their username only. "
        "2. When they give a username, ask for their password only. "
        "3. When they give the password, call verify_user with the username and password "
        "exactly as given. "
        "If someone gives both at once, go straight to step 3. "
        "If verified is true, greet the person by their first name and tell them their role. "
        "If it is false, tell them the message in one short sentence and start again at step 1, "
        "without welcoming them again. "
        "Never reveal or hint at any password."
    ),
    tools=[verify_user],
)
