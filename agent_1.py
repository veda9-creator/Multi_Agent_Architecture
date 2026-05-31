from openai import OpenAI
import re
import json

client = OpenAI()

# Customer Support Agent - ReAct Agent

# Sample Products Database
PRODUCTS = [
    {"id": "P101", "name": "Mechanical Keyboard", "category": "keyboard", "price": 2499},
    {"id": "P102", "name": "Wireless Mouse", "category": "mouse", "price": 999},
    {"id": "P103", "name": "Laptop Stand", "category": "accessory", "price": 1499},
]

# Sample Order Database
ORDERS = {
    "ORD-1001": {"status": "delivered", "days_since_delivery": 10, "amount": 2499},
    "ORD-1002": {"status": "in_transit", "days_since_delivery": None, "amount": 999},
    "ORD-1003": {"status": "delivered", "days_since_delivery": 35, "amount": 1499},
    "ORD-1004": {"status": "processing", "days_since_delivery": None, "amount": 4999},
}

def get_order_status(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return {"found": False, "message": "Order not found"}
    return {"found": true, "order_id": order_id, **order}

def get_refund_eligibility(order_id):
    order= ORDERS.get(order_id)
    if not order:
        return {"found": False, "message": "Order not found"}
    status = order["status"]
    if status == "processing":
         return {"found" : True, "eligible" : True, "reason": "Order not shipped yet, that's why eligible for refund"}
    elif status == "in_transit":
         return {"found" : True, "eligible" : False, "reason": "Order is already shipped, that's why not eligible for refund"}
    elif status == "delivered":
            days = order["days_since_delivery"]
            if days <= 30:
                return {"found" : True, "eligible" : True, "reason": f"Order delivered {days} days ago, that's why eligible for refund"}
            else:
                return {"found" : True, "eligible" : False, "reason": f"Order delivered {days} days ago, that's why not eligible for refund"}

    TOOLS ={
         "order_status": get_order_status,
         "refund_eligibility": get_refund_eligibilty
    }       

def call_tool(tool_name:str, order_id: str):
    if tool_name not in TOOLS:
        return {"error": "Tool not found"}
    TOOLS[tool_name](order_id)

ACTION_RE = re.compile(r"Action:\s*(.+)")
ACTION_INPUT_RE = re.compile(r"Action Input:\s*(\{.*\})", re.DOTALL)
    
SYSTEM_PROMPT = """
You are an e-commerce support agent using the ReAct pattern.

Available tools:
1. get_order_status(order_id: string)
2. refund_eligibility(order_id: string)

Rules:
- Think step by step.
- Use only one action at a time.
- Always follow this exact format:

Thought: <short reasoning>
Action: <tool name OR finish>
Action Input: <JSON object>

- If you need tool output, wait for an Observation.
- When you are ready to answer the user, use:
Thought: <short reasoning>
Action: finish
Action Input: {"answer": "<final answer>"}

Do not output anything else.
"""
def run_react_agent(user_query, max_steps=5):

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]

    for step in range(max_steps):

        response = client.responses.create(
            model="gpt-5.4",
            input=messages
        )

        llm_output = response.output_text.strip()

        print(f"------ Step: {step + 1} ------")
        print(llm_output)
     

        tool_name = ACTION_RE.search(llm_output)
        tool_name = tool_name.group(1).strip()


        tool_input = ACTION_INPUT_RE.search(llm_output)
        tool_input = json.loads(tool_input.group(1))

        print("Tool name: ", tool_name)
        print("Tool input: ", tool_input)

        order_id = tool_input['order_id']

        # call_tool(tool_name, tool_input)
        tool_output = get_refund_eligibility(order_id)
        print("Final Output: ", tool_output)

user_query = "My order ORD-1002 has not arrived. Can I get a refund?"
run_react_agent(user_query=user_query)


    
        
     