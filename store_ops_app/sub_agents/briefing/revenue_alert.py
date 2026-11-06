LOW_REVENUE = 100  # dollars for the week; below this the owner should hear about it first


def flag_low_revenue(callback_context):
    """before_agent_callback for the writer: code reads fields from the revenue report.

    The report is a validated dict, so there is no digging a number out of a sentence.
    """
    report = callback_context.state.get("revenue_report") or {}

    alert = ""
    if report.get("status") == "ok" and report.get("total_cad") is not None:
        if report["total_cad"] < LOW_REVENUE:
            alert = f"ALERT: revenue looks low (${report['total_cad']:g} this week)."

    callback_context.state["revenue_alert"] = alert  # the writer's instruction reads this
