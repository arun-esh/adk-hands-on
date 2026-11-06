import re

LOW_REVENUE = 100  # dollars for the week; below this the owner should hear about it first


def flag_low_revenue(callback_context):
    """before_agent_callback for the writer: code reads the revenue helper's text.

    The helper's answer is free text, so this has to dig a number out of a sentence.
    """
    text = callback_context.state.get("revenue_report", "")
    match = re.search(r"\d[\d,]*\.?\d*", text)

    alert = ""
    if match:
        amount = float(match.group().replace(",", ""))
        if amount < LOW_REVENUE:
            alert = f"ALERT: revenue looks low (${amount:g} this week)."

    callback_context.state["revenue_alert"] = alert  # the writer's instruction reads this
