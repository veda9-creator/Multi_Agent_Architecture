from typing import Any, Callable

ORDERS = {
    "1234": {"status": "delayed", "days_delayed": 9, "amount": 1499},
    "5678": {"status": "delivered", "days_delayed": 0, "amount": 799},
    "9012": {"status": "in_transit", "days_delayed": 2, "amount": 2499},
}

REFUND_POLICY = {"min_days_delayed_for_refund": 7}


def get_order_status(order_id: str):
    return ORDERS.get(order_id)


def get_refund_eligibility(order_id: str) -> bool:
    order = ORDERS.get(order_id)
    if not order:
        return False
    return (
        order["status"] == "delayed"
        and order["days_delayed"] >= REFUND_POLICY["min_days_delayed_for_refund"]
    )


TOOLS: dict[str, Callable[..., Any]] = {
    "get_order_status": get_order_status,
    "get_refund_eligibility": get_refund_eligibility,
}


def decide_next_action(user_query: str, history: list) -> dict:
    # Extract order id once (simple parse: first 4-digit token in the query).
    import re
    match = re.search(r"\b(\d{4})\b", user_query)
    order_id = match.group(1) if match else None

    if len(history) == 0:
        return {
            "thought": "I need to look up the order status before judging refund eligibility.",
            "action": "get_order_status",
            "action_input": {"order_id": order_id},
        }
    if len(history) == 1:
        return {
            "thought": "Order details retrieved; now check refund eligibility under the policy.",
            "action": "get_refund_eligibility",
            "action_input": {"order_id": order_id},
        }
    # history has both observations; decide the final reply.
    eligible = history[1]["observation"]
    if eligible:
        reply = (
            f"Order {order_id} is significantly delayed and qualifies for a refund "
            f"under the policy. We will initiate the refund shortly."
        )
    else:
        reply = (
            f"Order {order_id} does not meet the refund criteria right now. "
            f"Please reach out again if the situation changes."
        )
    return {
        "thought": "Eligibility decided; ready to respond to the user.",
        "action": "final_answer",
        "action_input": {"reply": reply},
    }


def run_agent(user_query: str, max_steps: int = 5) -> str:
    history: list = []
    for step in range(max_steps):
        decision = decide_next_action(user_query, history)
        print(f"Thought: {decision['thought']}")
        print(f"Action: {decision['action']}")
        print(f"Action Input: {decision['action_input']}")

        if decision["action"] == "final_answer":
            reply = decision["action_input"]["reply"]
            print(f"Final Answer: {reply}\n")
            return reply

        tool = TOOLS[decision["action"]]
        observation = tool(**decision["action_input"])
        print(f"Observation: {observation}\n")
        history.append({
            "action": decision["action"],
            "observation": observation,
        })
    return "Reached max steps without a final answer."


if __name__ == "__main__":
    run_agent("My order 1234 has not arrived, can I get a refund?")
 