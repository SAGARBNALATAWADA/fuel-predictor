# dashboard.py

import streamlit as st

def show_dashboard():
    st.markdown("<h2 style='text-align:center;'>📊 Dashboard</h2>", unsafe_allow_html=True)

    # Define 3 containers
    container1, container2, container3 = st.columns(3)

    with container1:
        st.markdown("""
        <div style='background-color:#f0f8ff;padding:20px;border-radius:10px;'>
            <h4 style='color:blue;'>🔍 Insights</h4>
            <p>Total Predictions: 120</p>
            <p>Avg. Fuel Cost: ₹450</p>
        </div>
        """, unsafe_allow_html=True)

    with container2:
        st.markdown("""
        <div style='background-color:#fff0f5;padding:20px;border-radius:10px;'>
            <h4 style='color:green;'>⛽ Usage Stats</h4>
            <p>Top Fuel Type: Petrol (X)</p>
            <p>Top Vehicle Class: Mid-size</p>
        </div>
        """, unsafe_allow_html=True)

    with container3:
        st.markdown("""
        <div style='background-color:#f5fffa;padding:20px;border-radius:10px;'>
            <h4 style='color:darkred;'>📈 Recent Trends</h4>
            <p>Highest CO₂ Rating: 9</p>
            <p>Most Efficient: 4.6 L/100km</p>
        </div>
        """, unsafe_allow_html=True)
