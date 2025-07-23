# fuel_api.py
from flask import Blueprint, jsonify, request

fuel_api = Blueprint('fuel_api', __name__)

# Mocked data for states
MOCK_STATES = [
    {"stateId": "MH", "stateName": "Maharashtra"},
    {"stateId": "DL", "stateName": "Delhi"},
    {"stateId": "KA", "stateName": "Karnataka"},
    {"stateId": "TN", "stateName": "Tamil Nadu"}
]

# Mocked districts per state
MOCK_DISTRICTS = {
    "MH": [{"district": "Mumbai"}, {"district": "Pune"}],
    "DL": [{"district": "New Delhi"}],
    "KA": [{"district": "Bangalore"}, {"district": "Mysore"}],
    "TN": [{"district": "Chennai"}, {"district": "Coimbatore"}],
}

# Mocked fuel prices
MOCK_PRICES = {
    ("MH", "Mumbai"): [
        {"productName": "Petrol", "productPrice": "108.19", "priceChangeSign": "+", "priceChange": "0.10"},
        {"productName": "Diesel", "productPrice": "94.15", "priceChangeSign": "-", "priceChange": "0.05"},
    ],
    ("DL", "New Delhi"): [
        {"productName": "Petrol", "productPrice": "96.72", "priceChangeSign": "0", "priceChange": "0.00"},
        {"productName": "Diesel", "productPrice": "89.62", "priceChangeSign": "+", "priceChange": "0.20"},
    ],
    ("KA", "Bangalore"): [
        {"productName": "Petrol", "productPrice": "102.91", "priceChangeSign": "-", "priceChange": "0.10"},
        {"productName": "Diesel", "productPrice": "88.87", "priceChangeSign": "0", "priceChange": "0.00"},
    ],
}


@fuel_api.route('/api/fuel/states')
def get_states():
    return jsonify(states=MOCK_STATES)


@fuel_api.route('/api/fuel/districts')
def get_districts():
    state = request.args.get('state')
    if not state:
        return jsonify(error="Missing state"), 400
    return jsonify(districts=MOCK_DISTRICTS.get(state, []))


@fuel_api.route('/api/fuel/price')
def get_price():
    state = request.args.get('state')
    district = request.args.get('district')
    if not state or not district:
        return jsonify(error="Missing state or district"), 400

    key = (state, district)
    return jsonify(products=MOCK_PRICES.get(key, []))
