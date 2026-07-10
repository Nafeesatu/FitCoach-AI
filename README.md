# 💪FitCoach AI — AI Fitness & Nutrition Coach

A single-agent AI application that acts as a personal fitness and nutrition coach. Chat naturally about your fitness goals, and the agent calculates your calorie/macro needs, looks up real nutrition data, tracks your progress over time, and gives evidence-based fitness guidance all through a conversational interface that remembers you across sessions.

Built as a capstone project demonstrating LLM integration, tool use, memory, and retrieval-augmented generation (RAG) in a deployed, single-agent architecture.

---

## 🔗 Live Application
**(https://fitcoach-ai-mwuepuzdey7ttevuz9sns6.streamlit.app/)**

## 🎥 Demo Video
(https://drive.google.com/file/d/1NbSfioeXX_bBhzDcvWZtsnUQlL-DN5H2/view?usp=drivesdk)

---

## 📌 The Problem

Personalized fitness and nutrition coaching is expensive, and free calculator apps are static, they don't remember you, can't answer follow-up questions, and can't hold a real conversation. Someone trying to lose weight, build muscle, or just eat better often has to juggle multiple separate apps: one for calorie calculations, another for food nutrition lookups, a notebook for tracking progress, and Google for general fitness questions.

**FitCoach AI** solves this by combining all of that into a single conversational AI agent that:
- Calculates personalized calorie and macro targets
- Looks up real nutrition data for any food
- Remembers your profile and logs your progress over time
- Answers general fitness/nutrition questions using evidence-based guidelines

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧮 Calorie & Macro Calculator | Computes BMI, BMR, TDEE, and daily calorie/macro targets using the Mifflin-St Jeor equation |
| 🍗 Real-Time Nutrition Lookup | Queries the USDA FoodData Central database for accurate calorie/protein/carb/fat info on any food |
| 💾 Persistent Memory | Saves user profiles and logs progress (weight, notes) to a SQLite database — remembered across sessions |
| 📚 RAG-Based Fitness Guidance | Retrieves relevant, evidence-based fitness/nutrition guidelines using semantic search over a curated knowledge base |
| 💬 Conversational Interface | Natural language chat — no forms, no menus, just ask |
| 🎨 Custom Styled UI | Dark-themed, modern Streamlit interface with clickable quick-start suggestions |

---

## 🏗️ Architecture

FitCoach AI uses a **single-agent architecture**: one LLM acts as the reasoning core, and it has access to a set of tools it can call on its own when a task requires specific computation, real data, or memory — rather than guessing or hallucinating numbers.

```
User message
     │
     ▼
┌─────────────────────────────┐
│   LLM (Llama 3.3 70B / Groq) │  ← decides which tool(s), if any, to use
└─────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│                 Tool Layer                    │
│  1. calculate_metrics        (calculator)     │
│  2. lookup_food_nutrition    (USDA API)       │
│  3. save_user_profile        (memory)         │
│  4. log_progress             (memory)         │
│  5. get_user_history         (memory)         │
│  6. retrieve_relevant_guidelines (RAG)        │
└─────────────────────────────────────────────┘
     │
     ▼
Tool result(s) fed back to LLM → natural language response
```

The agent runs a **tool-calling loop**: it sends the conversation to the LLM, checks whether the model wants to call a tool, executes it if so, feeds the result back, and repeats until the model produces a final answer. This allows the agent to chain multiple tools in a single turn (e.g., calculating calorie targets *and* checking safe weight-loss guidelines in one response).

---

## 🧰 Tools (6 total)

1. **`calculate_metrics`** — Calculates BMI, BMR, TDEE, and recommended daily calories/macros based on weight, height, age, sex, activity level, and goal.
2. **`lookup_food_nutrition`** — Looks up calories, protein, carbs, and fat for any food using the USDA FoodData Central API (SR Legacy dataset), scaled to a specified quantity.
3. **`save_user_profile`** — Saves or updates a user's profile (stats + goal) in a persistent SQLite database.
4. **`log_progress`** — Logs a dated progress entry (weight + notes) for a user.
5. **`get_user_history`** — Retrieves a user's saved profile and full progress history — used whenever the agent needs to recall past data.
6. **`retrieve_relevant_guidelines`** — A RAG tool that performs semantic similarity search over a curated set of evidence-based fitness/nutrition guidelines (safe weight-loss rates, protein needs, recovery, hydration, etc.) using sentence embeddings.

---

## 🧠 Memory & RAG

- **Memory:** A SQLite database (`fitness_coach.db`) with two tables — `user_profile` and `progress_log`. Each user is identified by a simple name/ID entered in the sidebar, allowing their data to persist and be recalled across conversations and sessions.
- **RAG:** A small curated knowledge base of fitness guidelines is embedded using `sentence-transformers` (`all-MiniLM-L6-v2`). When a general question is asked (e.g. "Is it safe to lose 5kg in 2 weeks?"), the agent retrieves the most semantically relevant guideline(s) via cosine similarity rather than relying purely on the LLM's own knowledge.

---

## 🛠️ Tech Stack

- **LLM:** [Groq](https://groq.com/) API running Llama 3.3 70B Versatile (function/tool calling)
- **Frontend:** [Streamlit](https://streamlit.io/)
- **Memory:** SQLite
- **Nutrition Data:** [USDA FoodData Central API](https://fdc.nal.usda.gov/)
- **RAG Embeddings:** `sentence-transformers`
- **Language:** Python

---

## 📁 Project Structure

```
├── app.py              # Streamlit UI — chat interface, sidebar, styling
├── agent.py             # Agent logic: tool schemas, system prompt, tool-calling loop
├── tools.py             # All 6 tool implementations (calculator, nutrition, memory, RAG)
├── requirements.txt     # Python dependencies
├── README.md            # This file
```

---

## 🧪 Example Interactions

> **"I'm 28, 70kg, 170cm, moderately active, want to maintain my weight. What are my calorie and macro targets?"**
→ Agent calls `calculate_metrics` and returns a personalized breakdown.

> **"How much protein is in 200g of salmon?"**
→ Agent calls `lookup_food_nutrition` and returns real USDA data.

> **"Log today's weight as 69.5kg and save my profile."**
→ Agent calls `save_user_profile` and `log_progress` to persist data.

> **"What's my progress been like, and is it safe to lose weight this fast?"**
→ Agent calls `get_user_history` to recall saved data **and** `retrieve_relevant_guidelines` to check safe weight-loss guidance — combining memory and RAG in a single response.

---

## 🚀 Future Improvements

- User authentication instead of a simple name/ID field
- Larger, more diverse RAG knowledge base (e.g. exercise-specific guidance, injury-safe modifications)
- Weight/progress visualization (charts) within the app
- Support for logging meals directly, with running daily totals
- Multi-turn workout plan generation

---
