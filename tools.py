import requests
import sqlite3
from datetime import datetime
import numpy as np

# =========================
# TOOL 1: Calculator
# =========================
def calculate_metrics(weight_kg: float, height_cm: float, age: int, sex: str, activity_level: str, goal: str):
    """Calculate BMI, BMR, TDEE, and recommended daily calories/macros."""
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    if sex.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9
    }
    multiplier = activity_multipliers.get(activity_level.lower(), 1.2)
    tdee = round(bmr * multiplier)

    if goal == "lose_weight":
        target_calories = tdee - 500
    elif goal == "gain_muscle":
        target_calories = tdee + 300
    else:
        target_calories = tdee

    protein_g = round((target_calories * 0.30) / 4)
    carbs_g = round((target_calories * 0.40) / 4)
    fat_g = round((target_calories * 0.30) / 9)

    return {
        "bmi": bmi, "bmr": round(bmr), "tdee": tdee,
        "target_calories": target_calories,
        "macros": {"protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g}
    }


# =========================
# TOOL 2: Nutrition Lookup
# =========================
NUTRIENT_NUMBERS = {"calories": "208", "protein_g": "203", "fat_g": "204", "carbs_g": "205"}
EXCLUDE_KEYWORDS = ["lunchmeat", "breaded", "roll", "oscar mayer", "deli", "fat-free",
                    "honey", "mesquite", "seasoned", "prepackaged", "rotisserie", "bbq", "tenders"]

def _get_nutrients_by_number(food):
    nutrients = {}
    for n in food["foodNutrients"]:
        num = n.get("nutrientNumber")
        val = n.get("value", 0)
        if num not in nutrients or (nutrients[num] == 0 and val != 0):
            nutrients[num] = val
    if nutrients.get(NUTRIENT_NUMBERS["calories"], 0) <= 0:
        return None
    return nutrients

def lookup_food_nutrition(food_name: str, quantity_grams: float = 100, usda_api_key: str = None):
    """Look up calorie and macro info for a food using USDA FoodData Central (SR Legacy dataset)."""
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": food_name, "api_key": usda_api_key,
        "pageSize": 15, "dataType": ["SR Legacy"]
    }
    resp = requests.get(search_url, params=params)
    data = resp.json()

    if not data.get("foods"):
        return {"error": f"No nutrition data found for '{food_name}'"}

    candidates = [f for f in data["foods"] if not any(kw in f["description"].lower() for kw in EXCLUDE_KEYWORDS)]
    if not candidates:
        candidates = data["foods"]

    def sort_key(f):
        desc = f["description"].lower()
        return (0 if "raw" in desc else 1, len(desc))

    candidates = sorted(candidates, key=sort_key)

    chosen_food, nutrients = None, None
    for f in candidates:
        result = _get_nutrients_by_number(f)
        if result is not None:
            chosen_food, nutrients = f, result
            break

    if chosen_food is None:
        return {"error": f"No usable nutrition data found for '{food_name}'"}

    scale = quantity_grams / 100
    carbs = max(nutrients.get(NUTRIENT_NUMBERS["carbs_g"], 0) * scale, 0)

    return {
        "food": chosen_food["description"],
        "quantity_grams": quantity_grams,
        "calories": round(nutrients.get(NUTRIENT_NUMBERS["calories"], 0) * scale, 1),
        "protein_g": round(nutrients.get(NUTRIENT_NUMBERS["protein_g"], 0) * scale, 1),
        "carbs_g": round(carbs, 1),
        "fat_g": round(nutrients.get(NUTRIENT_NUMBERS["fat_g"], 0) * scale, 1)
    }


# =========================
# TOOLS 3-5: Memory (SQLite)
# =========================
DB_PATH = "fitness_coach.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id TEXT PRIMARY KEY, weight_kg REAL, height_cm REAL, age INTEGER,
            sex TEXT, activity_level TEXT, goal TEXT, updated_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, date TEXT,
            weight_kg REAL, notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user_profile(user_id: str, weight_kg: float, height_cm: float, age: int, sex: str, activity_level: str, goal: str):
    """Save or update a user's profile information."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_profile (user_id, weight_kg, height_cm, age, sex, activity_level, goal, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            weight_kg=excluded.weight_kg, height_cm=excluded.height_cm, age=excluded.age,
            sex=excluded.sex, activity_level=excluded.activity_level, goal=excluded.goal,
            updated_at=excluded.updated_at
    """, (user_id, weight_kg, height_cm, age, sex, activity_level, goal, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "profile saved", "user_id": user_id}

def log_progress(user_id: str, weight_kg: float, notes: str = ""):
    """Log a new progress entry for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO progress_log (user_id, date, weight_kg, notes) VALUES (?, ?, ?, ?)
    """, (user_id, datetime.now().strftime("%Y-%m-%d"), weight_kg, notes))
    conn.commit()
    conn.close()
    return {"status": "progress logged", "date": datetime.now().strftime("%Y-%m-%d"), "weight_kg": weight_kg}

def get_user_history(user_id: str):
    """Retrieve a user's saved profile and full progress log history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
    profile_row = cursor.fetchone()
    profile = None
    if profile_row:
        profile = {
            "weight_kg": profile_row[1], "height_cm": profile_row[2], "age": profile_row[3],
            "sex": profile_row[4], "activity_level": profile_row[5], "goal": profile_row[6],
            "updated_at": profile_row[7]
        }
    cursor.execute("SELECT date, weight_kg, notes FROM progress_log WHERE user_id = ? ORDER BY date", (user_id,))
    history_rows = cursor.fetchall()
    history = [{"date": r[0], "weight_kg": r[1], "notes": r[2]} for r in history_rows]
    conn.close()

    if not profile and not history:
        return {"message": "No history found for this user yet."}
    return {"profile": profile, "progress_history": history}


# =========================
# TOOL 6: RAG - Fitness Guidelines
# =========================
FITNESS_GUIDELINES = [
    "Beginners should aim for at least 150 minutes of moderate-intensity aerobic activity per week, such as brisk walking, spread across the week rather than done all at once.",
    "Strength training for all major muscle groups should be done at least 2 days per week, allowing at least 48 hours of rest between sessions targeting the same muscle group.",
    "A safe rate of weight loss is generally 0.5 to 1 kg (1 to 2 lbs) per week, achieved through a moderate calorie deficit rather than extreme restriction.",
    "Protein intake for muscle building is generally recommended at 1.6 to 2.2 grams per kilogram of body weight per day, spread across multiple meals.",
    "Proper warm-up before exercise (5-10 minutes of light cardio and dynamic stretching) reduces injury risk and improves performance.",
    "Hydration matters: a general guideline is to drink water before, during, and after exercise, and more in hot conditions or during intense/long sessions.",
    "Rest and recovery are essential -- overtraining without adequate rest can lead to fatigue, decreased performance, and increased injury risk.",
    "Progressive overload -- gradually increasing weight, reps, or intensity over time -- is the key principle behind building strength and muscle.",
    "Sleep of 7-9 hours per night supports muscle recovery, hormone regulation, and overall fitness progress.",
    "Consulting a doctor before starting a new exercise program is recommended for individuals with existing health conditions, injuries, or who have been sedentary for a long time.",
]

_embedder = None
_guideline_embeddings = None

def _get_embedder():
    global _embedder, _guideline_embeddings
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        _guideline_embeddings = _embedder.encode(FITNESS_GUIDELINES)
    return _embedder, _guideline_embeddings

def retrieve_relevant_guidelines(query: str, top_k: int = 2):
    """Retrieve relevant fitness/nutrition guidelines using semantic similarity search."""
    embedder, guideline_embeddings = _get_embedder()
    query_embedding = embedder.encode([query])

    similarities = np.dot(guideline_embeddings, query_embedding.T).flatten() / (
        np.linalg.norm(guideline_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    top_indices = np.argsort(similarities)[::-1][:top_k]
    results = [FITNESS_GUIDELINES[i] for i in top_indices]
    return {"relevant_guidelines": results}
