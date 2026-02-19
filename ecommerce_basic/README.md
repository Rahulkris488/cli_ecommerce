# BCA Final Year Project: Natural Language Interface for E-commerce

This project is a CLI-based chatbot designed to simulate a customer support assistant for an e-commerce platform.

## 🎯 Project Objective
To build a **Natural Language Interface** that provides instant responses to common user queries without human intervention.

## 🏗️ System Overview
The chatbot follows a modular architecture:
1.  **`app.py`**: The View Layer (CLI Interface using `Click`).
2.  **`services.py`**: The Logic Layer (Regex & Keyword Matching).
3.  **`database.json`**: The Data Layer (JSON Storage).

## 🛠️ Implementation Logic
This project prioritizes simplicity and explainability over complex ML models.

### 1. Intent Detection
We use **Keyword Matching** to determine what the user wants.
- If the user says "Track", we look for tracking logic.
- If the user names a "Product", we fetch price/stock.

### 2. Regex for Order Extraction
We use Python's `re` module to extract Order IDs.
- **Pattern**: `\b\d{4}\b`
- **Explanation**:
  - `\b`: Word boundary (ensure it's a distinct word).
  - `\d{4}`: Exactly 4 digits (e.g., 1001, 2024).
  - This allows commands like "Track **1001**" or "Status of **1234**" to work dynamically.

## 🚀 How to Run
1.  Open Terminal.
2.  Navigate to the `ecommerce_basic` folder.
3.  Run:
    ```bash
    python app.py
    ```

## 🧪 Testing Results
We use `pytest` to verify logic.
- **Test 1**: Extracts Order ID correctly? -> **PASS**
- **Test 2**: Identifies valid Order vs Invalid? -> **PASS**
- **Test 3**: Returns correct Product Price? -> **PASS**

## ⚠️ Limitations
- Only understands hardcoded keywords.
- Cannot handle complex sentences without those keywords.
- Single-turn conversation (context is limited).

## 🔮 Future Scope
- Add NLP (Natural Language Processing) for better understanding.
- Add Context Memory to remember previous questions.
- Integrate with a real database (SQL/MongoDB).
