from google.genai import types


def require_role(*allowed_roles):
    """Builds a before_agent_callback that only lets the listed roles run an agent.

    The role comes from session state, which verify_user writes in plain code.
    The model never writes it, so a clever message cannot change it.
    """

    def check(callback_context):
        role = callback_context.state.get("user_role")
        if role in allowed_roles:
            return None  # allowed: let the agent run as normal

        # Returning content skips the agent and sends this text back instead.
        return types.Content(
            role="model",
            parts=[types.Part(text="Sorry, that isn't available for your role.")],
        )

    return check
