import json
from groq import Groq
from tools import (
    calculate_metrics,
    lookup_food_nutrition,
    save_user_profile,
    log_progress,
    get_user_history,
    retrieve_relevant_guidelines
)

MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a knowledgeable, encouraging AI fitness and nutrition coach.
You help users understand their calorie/macro needs, look up nutrition info for foods,
track their progress over time, and give evidence-based fitness guidance.

Guidelines:
- Always be encouraging and supportive, never judgmental about a user's current stats or habits.
- Use tools whenever the user's question requires specific calculations, food data, saved history, or guidelines -- don't guess numbers yourself.
- When a user shares personal stats (weight, height, age, etc.), consider saving their profile using their user_id.
- If a user asks about their progress or past data, retrieve it first using get_user_history before answering.
- Keep responses concise, clear, and actionable.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_metrics",
            "description": "Calculate BMI, BMR, TDEE, and recommended daily calories/macros for a user based on their body stats, activity level, and fitness goal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "weight_kg": {"type": "number", "description": "User's weight in kilograms"},
                    "height_cm": {"type": "number", "description": "User's height in centimeters"},
                    "age": {"type": "integer", "description": "User's age in years"},
                    "sex": {"type": "string", "enum": ["male", "female"]},
                    "activity_level": {
                        "type": "string",
                        "enum": ["sedentary", "light", "moderate", "active", "very_active"],
                        "description": "sedentary=little/no exercise, light=1-3 days/week, moderate=3-5 days/week, active=6-7 days/week, very_active=intense daily training"
                    },
                    "goal": {"type": "string", "enum": ["lose_weight", "maintain", "gain_muscle"]}
                },
                "required": ["weight_kg", "height_cm", "age", "sex", "activity_level", "goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_food_nutrition",
            "description": "Look up calorie and macronutrient information for a specific food item, scaled to a given quantity in grams.",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_name": {"type": "string", "description": "Name of the food, e.g. 'chicken breast', 'banana'"},
                    "quantity_grams": {"type": "number", "description": "Quantity in grams. Default to 100 if not specified."}
                },
                "required": ["food_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_user_profile",
            "description": "Save or update the user's profile information so it can be remembered for future conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Unique identifier for the user"},
                    "weight_kg": {"type": "number"},
                    "height_cm": {"type": "number"},
                    "age": {"type": "integer"},
                    "sex": {"type": "string", "enum": ["male", "female"]},
                    "activity_level": {"type": "string", "enum": ["sedentary", "light", "moderate", "active", "very_active"]},
                    "goal": {"type": "string", "enum": ["lose_weight", "maintain", "gain_muscle"]}
                },
                "required": ["user_id", "weight_kg", "height_cm", "age", "sex", "activity_level", "goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_progress",
            "description": "Log a new progress entry for the user, such as today's weight and notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "weight_kg": {"type": "number"},
                    "notes": {"type": "string", "description": "Optional notes about today's progress"}
                },
                "required": ["user_id", "weight_kg"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_history",
            "description": "Retrieve the user's saved profile and full progress log history. Use this whenever the user asks about their progress or past stats.",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_relevant_guidelines",
            "description": "Retrieve relevant evidence-based fitness and nutrition guidelines for general questions (safe weight loss rates, protein needs, recovery, hydration, etc.). Not for calculating a specific user's personal numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The user's question or topic"},
                    "top_k": {"type": "integer", "description": "Number of guidelines to retrieve, default 2"}
                },
                "required": ["query"]
            }
        }
    }
]


def make_available_functions(usda_api_key: str):
    """Bind the USDA API key into lookup_food_nutrition via a wrapper, and return the full registry."""
    def _lookup_wrapper(food_name, quantity_grams=100):
        return lookup_food_nutrition(food_name, quantity_grams, usda_api_key=usda_api_key)

    return {
        "calculate_metrics": calculate_metrics,
        "lookup_food_nutrition": _lookup_wrapper,
        "save_user_profile": save_user_profile,
        "log_progress": log_progress,
        "get_user_history": get_user_history,
        "retrieve_relevant_guidelines": retrieve_relevant_guidelines
    }


def run_agent(client: Groq, messages: list, available_functions: dict):
    """
    Runs the tool-calling agent loop:
    sends messages -> checks for tool calls -> executes them -> feeds results back
    -> repeats until the model returns a final text answer.
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    response_message = response.choices[0].message
    messages.append(response_message)

    tool_call_log = []

    while response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            tool_call_log.append({"tool": func_name, "args": func_args})

            function_to_call = available_functions[func_name]
            function_result = function_to_call(**func_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(function_result)
            })

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        response_message = response.choices[0].message
        messages.append(response_message)

    return response_message.content, messages, tool_call_log
