import streamlit as st
import pandas as pd
import sqlite3

# Connect to DB
conn = sqlite3.connect("database.db", check_same_thread=False)

st.set_page_config(page_title="🍲 Local Food Wastage Management System", layout="wide")

st.title("🍲 Local Food Wastage Management System")
st.markdown("A platform to connect food providers with receivers to reduce wastage and support communities.")

# -------------------------------
# Tabs Layout
# -------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📦 Food Listings", "📞 Contact Info", "🛠️ CRUD Operations", "📊 Analysis & Queries"])

# -------------------------------
# Tab 1: Food Listings with Filters
# -------------------------------
with tab1:
    st.subheader("📦 Available Food Listings with Filters")

    # Dropdown filter options
    cities = pd.read_sql("SELECT DISTINCT location FROM food_listings;", conn)["location"].dropna().tolist()
    provider_types = pd.read_sql("SELECT DISTINCT provider_type FROM food_listings;", conn)["provider_type"].dropna().tolist()
    food_types = pd.read_sql("SELECT DISTINCT food_type FROM food_listings;", conn)["food_type"].dropna().tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        city_filter = st.selectbox("Filter by City", ["All"] + sorted(cities))
    with col2:
        provider_filter = st.selectbox("Filter by Provider Type", ["All"] + sorted(provider_types))
    with col3:
        food_type_filter = st.selectbox("Filter by Food Type", ["All"] + sorted(food_types))

    df_food = pd.read_sql("SELECT * FROM food_listings;", conn)
    if city_filter != "All":
        df_food = df_food[df_food["location"] == city_filter]
    if provider_filter != "All":
        df_food = df_food[df_food["provider_type"] == provider_filter]
    if food_type_filter != "All":
        df_food = df_food[df_food["food_type"] == food_type_filter]

    st.dataframe(df_food, use_container_width=True)

# -------------------------------
# Tab 2: Contact Info
# -------------------------------
with tab2:
    st.subheader("📞 Contact Information")
    contact_choice = st.radio("View contacts for:", ["Providers", "Receivers"], horizontal=True)
    if contact_choice == "Providers":
        df_contact = pd.read_sql("SELECT name, city, contact FROM providers;", conn)
    else:
        df_contact = pd.read_sql("SELECT name, city, contact FROM receivers;", conn)
    st.dataframe(df_contact, use_container_width=True)

# -------------------------------
# Tab 3: CRUD Operations
# -------------------------------
with tab3:
    st.subheader("🛠️ Manage Food Listings")

    crud_action = st.selectbox("Choose Action", ["Add Food", "Update Food", "Delete Food"])

    df_all_food = pd.read_sql("SELECT food_id, food_name FROM food_listings;", conn)
    food_options = [f"{row['food_id']} - {row['food_name']}" for _, row in df_all_food.iterrows()]

    if crud_action == "Add Food":
        with st.form("add_food"):
            food_name = st.text_input("Food Name")
            qty = st.number_input("Quantity", min_value=1)
            expiry = st.date_input("Expiry Date")
            provider_id = st.number_input("Provider ID", min_value=1)
            provider_type = st.selectbox("Provider Type", sorted(provider_types))
            location = st.selectbox("Location", sorted(cities))
            food_type = st.selectbox("Food Type", sorted(food_types))
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            submitted = st.form_submit_button("Add")
            if submitted:
                conn.execute("""
                    INSERT INTO food_listings (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (food_name, qty, expiry, provider_id, provider_type, location, food_type, meal_type))
                conn.commit()
                st.success("✅ New food listing added!")

    elif crud_action == "Update Food":
        if food_options:
            selected_food = st.selectbox("Select Food to Update", food_options)
            food_id = int(selected_food.split(" - ")[0])
            new_qty = st.number_input("New Quantity", min_value=1)
            if st.button("Update"):
                conn.execute("UPDATE food_listings SET quantity = ? WHERE food_id = ?", (new_qty, food_id))
                conn.commit()
                st.success(f"✅ Food listing (ID {food_id}) updated!")
        else:
            st.info("No food listings available.")

    elif crud_action == "Delete Food":
        if food_options:
            selected_food = st.selectbox("Select Food to Delete", food_options)
            food_id = int(selected_food.split(" - ")[0])
            if st.button("Delete"):
                conn.execute("DELETE FROM food_listings WHERE food_id = ?", (food_id,))
                conn.commit()
                st.success(f"✅ Food listing (ID {food_id}) deleted!")
        else:
            st.info("No food listings available.")

# -------------------------------
# Tab 4: Queries
# -------------------------------
with tab4:
    st.subheader("📊 SQL Analysis & Insights")

    queries = {
        "Q1: Providers per City": "SELECT city, COUNT(*) AS provider_count FROM providers GROUP BY city;",
        "Q2: Provider Type Contributions": "SELECT provider_type, SUM(quantity) AS total_food FROM food_listings GROUP BY provider_type ORDER BY total_food DESC;",
        "Q3: Providers in Chennai": "SELECT name, contact FROM providers WHERE city = 'Chennai';",
        "Q4: Top Receivers by Claims": """SELECT r.name, COUNT(c.claim_id) AS total_claims
                                        FROM claims c JOIN receivers r ON c.receiver_id = r.receiver_id
                                        GROUP BY r.name ORDER BY total_claims DESC LIMIT 10;""",
        "Q5: Total Food Available": "SELECT SUM(quantity) AS total_food_available FROM food_listings;",
        "Q6: Top City by Listings": """SELECT location, COUNT(*) AS listing_count FROM food_listings
                                    GROUP BY location ORDER BY listing_count DESC LIMIT 10;""",
        "Q7: Food Type Availability": """SELECT food_type, COUNT(*) AS count_food
                                        FROM food_listings GROUP BY food_type ORDER BY count_food DESC;""",
        "Q8: Claims per Food Item": """SELECT food_id, COUNT(*) AS claims_count FROM claims
                                    GROUP BY food_id ORDER BY claims_count DESC LIMIT 10;""",
        "Q9: Top Providers by Successful Claims": """SELECT p.name, COUNT(c.claim_id) AS successful_claims
                                                    FROM claims c JOIN food_listings f ON c.food_id = f.food_id
                                                    JOIN providers p ON f.provider_id = p.provider_id
                                                    WHERE c.status = 'Completed'
                                                    GROUP BY p.name ORDER BY successful_claims DESC LIMIT 10;""",
        "Q10: Claim Status Distribution": """SELECT status, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims),2) AS percentage
                                            FROM claims GROUP BY status;""",
        "Q11: Avg Food Claimed per Receiver": """SELECT r.name, ROUND(AVG(f.quantity),2) AS avg_claimed
                                                FROM claims c JOIN receivers r ON c.receiver_id = r.receiver_id
                                                JOIN food_listings f ON c.food_id = f.food_id
                                                GROUP BY r.name ORDER BY avg_claimed DESC LIMIT 10;""",
        "Q12: Claims by Meal Type": """SELECT f.meal_type, COUNT(c.claim_id) AS total_claims
                                    FROM claims c JOIN food_listings f ON c.food_id = f.food_id
                                    GROUP BY f.meal_type ORDER BY total_claims DESC;""",
        "Q13: Total Donations by Provider": """SELECT p.name, SUM(f.quantity) AS total_donated
                                            FROM food_listings f JOIN providers p ON f.provider_id = p.provider_id
                                            GROUP BY p.name ORDER BY total_donated DESC LIMIT 10;""",
        "Q14: Top 5 Receivers by Claims": """SELECT r.name, COUNT(c.claim_id) AS total_claims
                                            FROM claims c JOIN receivers r ON c.receiver_id = r.receiver_id
                                            GROUP BY r.name ORDER BY total_claims DESC LIMIT 5;""",
        "Q15: City-wise Food Demand": """SELECT r.city, COUNT(c.claim_id) AS total_claims
                                        FROM claims c JOIN receivers r ON c.receiver_id = r.receiver_id
                                        GROUP BY r.city ORDER BY total_claims DESC LIMIT 10;"""
    }

    selected_query = st.selectbox("Select Query", list(queries.keys()))
    df_result = pd.read_sql(queries[selected_query], conn)
    st.dataframe(df_result, use_container_width=True)

    # Show chart if applicable
    if df_result.shape[1] == 2:
        st.bar_chart(df_result.set_index(df_result.columns[0]))
