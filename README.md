# Shipping Cost Comparator (LogiRate API) 🚚

A high-performance, production-ready logistics engine built with **FastAPI**. It automates shipping cost comparisons across multiple carriers by resolving Indian 6-digit pincodes into specific shipping zones (A-E) using a localized Pincode Master database.



## 🌟 Core Features

- **Pincode Intelligence**: Resolves City, State, and District using an optimized CSV master database.
- **Smart Zone Resolution**: Implements a strict priority-based hierarchy:
    - **Zone A (Local)**: Intra-city shipments.
    - **Zone B (Regional)**: Intra-state shipments.
    - **Zone C (Metro)**: Hub-to-Hub shipments between major Tier-1 cities.
    - **Zone D (National)**: Standard cross-state shipments (Rest of India).
    - **Zone E (Special)**: **Highest Priority** override for North East states, J&K, and Ladakh.
- **Dynamic Pricing Engine**: Calculates costs based on:
    - Base weight slabs (e.g., 0.5kg).
    - Additional weight increments.
    - **COD Logic**: "Higher of" fixed fee vs. percentage of order value.
    - **Taxation**: Integrated 18% GST (configurable).
- **Industry Grade Performance**: Implements $O(1)$ dictionary-based lookups for microsecond response times.



## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Data Validation**: Pydantic V2 (Strict Type Checking)
- **Data Processing**: Pandas (Initial CSV indexing)
- **Frontend**: Tailwind CSS & Vanilla JS (Fetch API)
- **Configuration**: JSON-driven settings for easy updates to GST and Metro lists.

## 📁 Project Structure

```text
shipping-cost-comparator/
├── app/
│   ├── main.py            # API Routes & CORS Config
│   ├── engine.py          # Calculation Logic (GST, COD, Slabs)
│   ├── zones.py           # Pincode & Zone Resolution Logic
│   ├── schemas.py         # Pydantic V2 Models & Validators
│   ├── config/            # JSON Configuration Files
│   │   ├── settings.json
│   │   ├── metro_cities.json
│   │   └── special_states.json
│   └── data/              # Reference Data
│       └── pincode_master.csv
├── static/
│   └── index.html         # Frontend Form
└── rate_cards.json        # Carrier Rates Database

Getting Started
1. Clone the repository
git clone 
cd shipping-cost-comparator

2. Install Dependencies
pip install fastapi uvicorn pandas pydantic

3. Run the Server
uvicorn app.main:app --reload

4. Access the App
UI: Open static/index.html in your browser.

API Docs: Navigate to http://127.0.0.1:8000/docs (Swagger UI).

📊 API Usage Example
Request: POST /compare-rates

JSON

{
  "source_pincode": 400001,
  "dest_pincode": 110001,
  "weight": 0.8,
  "is_cod": true,
  "order_value": 1500,
  "mode": "Both"
}
Response Breakdown: The system automatically identifies Mumbai and Delhi as Metros, resolves to Zone C, calculates the 0.5kg base + 0.5kg additional unit, applies the higher COD fee, and adds 18% GST.

⚙️ Configuration
You can update carrier rates in rate_cards.json or modify the Metro city list in app/config/metro_cities.json without touching the core Python logic. This ensures the system is easily maintainable as courier contracts change.

Developed with ❤️ for Logistics Efficiency.
---

### Pro Tip for your GitHub:
I've added a section for **Project Structure**. This is very important because it shows anyone looking at your code that you know how to organize a professional Python application.