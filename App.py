# app.py
import streamlit as st
import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456", 
    database="Food_Wastage"
)

print("Connection successful!")


st.set_page_config(page_title="Food Management Dashboard", layout="wide")

st.title("Food Management Dashboard")

cursor = conn.cursor()

cursor.execute("SELECT * FROM providers")
result = cursor.fetchall()
providers_df = pd.DataFrame(result, columns=["Provider_ID", "Name", "Type", "Address", "City", "Contact"])

# CREATE
st.subheader("➕ Add New Provider")
with st.form("add_provider"):
    provider_ID = st.text_input("Provider_ID")
    name = st.text_input("Name")
    type = st.selectbox("Type", ["Restaurant", "Grocery", "Bakery"])
    address = st.text_input("Address")
    city = st.text_input("City")
    contact = st.text_input("Contact")
    add_btn = st.form_submit_button("Add")
    if add_btn:
        cursor.execute("""
            INSERT INTO providers (Provider_ID, Name, Type, Address, City, Contact)
            VALUES (%s,%s, %s, %s, %s, %s)
        """, (provider_ID,name, type, address, city, contact))
conn.commit()
st.success("✅ Provider added!")

# UPDATE
st.subheader("✏️ Update Provider")
provider_ids = providers_df['Provider_ID'].tolist()
with st.form("update_provider"):
    pid = st.selectbox("Select Provider ID", provider_ids)
    new_name = st.text_input("New Name")
    new_contact = st.text_input("New Contact")
    update_btn = st.form_submit_button("Update")
    if update_btn:
        cursor.execute("UPDATE providers SET Name=%s, Contact=%s WHERE Provider_ID=%s",
                       (new_name, new_contact, pid))
        conn.commit()
        st.success("🔄 Provider updated!")

# DELETE
st.subheader("🗑️ Delete Provider")
with st.form("delete_provider"):
    del_pid = st.selectbox("Select Provider to Delete", provider_ids)
    del_btn = st.form_submit_button("Delete")
    if del_btn:
        cursor.execute("DELETE FROM providers WHERE Provider_ID=%s", (del_pid,))
        conn.commit()
        st.warning("❌ Provider deleted!")

st.markdown("---")

# Sidebar filters
st.sidebar.header("🔍 Filters")
city_filter = st.sidebar.text_input("City")
provider_type_filter = st.sidebar.text_input("Provider Type")
food_type_filter = st.sidebar.text_input("Food Type")

# 1. Providers and Receivers per city
if st.checkbox("📍 Providers and Receivers by City"):
    cursor.execute("SELECT City, COUNT(*) AS TotalProviders FROM providers GROUP BY City")
    df_providers = pd.DataFrame(cursor.fetchall(), columns=["City", "TotalProviders"])

    cursor.execute("SELECT City, COUNT(*) AS TotalReceivers FROM receivers GROUP BY City")
    df_receivers = pd.DataFrame(cursor.fetchall(), columns=["City", "TotalReceivers"])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Providers")
        st.dataframe(df_providers)
    with col2:
        st.subheader("Receivers")
        st.dataframe(df_receivers)

# 2. Provider type contributing most food
if st.checkbox("🍽️ Top Contributing Provider Type"):
    cursor.execute("""
        SELECT p.Type AS Provider_Type, SUM(f.Quantity) AS Total_Quantity
        FROM providers p
        JOIN food_listings f ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Type
        ORDER BY Total_Quantity DESC
        LIMIT 1
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Provider_Type", "Total_Quantity"])
    st.dataframe(df)

# 3. Contact info of providers in specific city
if st.checkbox("📱 Provider Contacts by City"):
    city = st.text_input("Enter city name")
    if city:
        cursor.execute("""
            SELECT Name, Type, Contact FROM providers WHERE City = %s
        """, (city,))
        df = pd.DataFrame(cursor.fetchall(), columns=["Name", "Type", "Contact"])
        st.dataframe(df)

# 4. Receivers with most food claimed
if st.checkbox("📊 Top Claiming Receivers"):
    cursor.execute("""
        SELECT r.Name, COUNT(*) AS Total_Claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name
        ORDER BY Total_Claims DESC
        LIMIT 5
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Receiver Name", "Total Claims"])
    st.dataframe(df)

# 5. Total quantity available
if st.checkbox("🍽️ Total Quantity Available"):
    cursor.execute("SELECT SUM(Quantity) AS Total_Available FROM food_listings")
    df = pd.DataFrame(cursor.fetchall(), columns=["Total_Available"])
    st.dataframe(df)

# 6. City with highest food listings
if st.checkbox("🌍 Top City by Listings"):
    cursor.execute("""
        SELECT Location, COUNT(*) AS Total_Listings
        FROM food_listings
        GROUP BY Location
        ORDER BY Total_Listings DESC
        LIMIT 1
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Location", "Total_Listings"])
    st.dataframe(df)

# 7. Most common food types
if st.checkbox("🍽️ Most Common Food Types"):
    cursor.execute("""
        SELECT Food_Type, COUNT(*) AS Count
        FROM food_listings
        GROUP BY Food_Type
        ORDER BY Count DESC
        LIMIT 5
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Food_Type", "Count"])
    st.dataframe(df)

# 8. Food claims per item
if st.checkbox("🔹 Claims per Food Item"):
    cursor.execute("""
        SELECT f.Food_Name, COUNT(*) AS Claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Food_Name
        ORDER BY Claims DESC
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Food_Name", "Claims"])
    st.dataframe(df)

# 9. Provider with highest successful claims
if st.checkbox("💪 Top Provider by Successful Claims"):
    cursor.execute("""
        SELECT p.Name, COUNT(*) AS Success_Claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        WHERE c.Status = 'Completed'
        GROUP BY p.Name
        ORDER BY Success_Claims DESC
        LIMIT 1
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Provider Name", "Success_Claims"])
    st.dataframe(df)

# 10. Claim status percentages
if st.checkbox("% Claim Status"):
    cursor.execute("""
        SELECT Status, COUNT(*) FROM claims GROUP BY Status
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Status", "Count"])
    total = df["Count"].sum()
    df["Percentage"] = round((df["Count"] / total) * 100, 2)
    st.dataframe(df)

# 11. Avg food claimed per receiver
if st.checkbox("📈 Avg Claimed per Receiver"):
    cursor.execute("""
        SELECT r.Name, AVG(f.Quantity) AS Avg_Quantity
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name
        ORDER BY Avg_Quantity DESC
        LIMIT 5
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Receiver", "Avg_Quantity"])
    st.dataframe(df)

# 12. Most claimed meal type
if st.checkbox("🍽️ Most Claimed Meal Type"):
    cursor.execute("""
        SELECT f.Meal_Type, COUNT(*) AS Total_Claims
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Meal_Type
        ORDER BY Total_Claims DESC
        LIMIT 1
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Meal_Type", "Total_Claims"])
    st.dataframe(df)

# 13. Total food donated per provider
if st.checkbox("🍽️ Total Donated by Providers"):
    cursor.execute("""
        SELECT p.Name, SUM(f.Quantity) AS Total_Donated
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
        ORDER BY Total_Donated DESC
    """)
    df = pd.DataFrame(cursor.fetchall(), columns=["Provider", "Total_Donated"])
    st.dataframe(df)

st.subheader("📊 Day of the Week with Highest Food Claims")

# Query 14: Day with highest food claims
if st.checkbox("Day with the Highest Food Claims"):
    query = """
    SELECT DAYNAME(Timestamp) AS Day, COUNT(*) AS Total_Claims
    FROM claims
    GROUP BY Day
    ORDER BY Total_Claims DESC;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Day", "Total_Claims"])
    st.dataframe(df)

# Query 15: Unclaimed expired items
if st.checkbox("How many expired food items are still unclaimed?"):
    query = """
    SELECT COUNT(*) AS Unclaimed_Expired_Items
    FROM food_listings fl
    LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
    WHERE c.Claim_ID IS NULL AND fl.Expiry_Date < NOW();
    """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Unclaimed_Expired_Items"])
    st.dataframe(df)

# Query 16: Highest average quantity per food type
if st.checkbox("Food type with highest average quantity per listing"):
    query = """
    SELECT Food_Type, ROUND(AVG(Quantity), 2) AS Avg_Quantity
    FROM food_listings
    GROUP BY Food_Type
    ORDER BY Avg_Quantity DESC;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Food_Type", "Avg_Quantity"])
    st.dataframe(df)

# Query 17: Provider type with most variety
if st.checkbox("Provider type with most variety of food types"):
    query = """
    SELECT Provider_Type, COUNT(DISTINCT Food_Type) AS Unique_Food_Types
    FROM food_listings
    GROUP BY Provider_Type
    ORDER BY Unique_Food_Types DESC;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Provider_Type", "Unique_Food_Types"])
    st.dataframe(df)

# Query 18: Total food listings available
if st.checkbox("Total number of food listings available"):
    query = "SELECT COUNT(*) AS Total_Food FROM food_listings"
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Total_Food"])
    st.dataframe(df)

# Query 19: Total claims made
if st.checkbox("Total number of claims made"):
    query = "SELECT COUNT(*) AS Total_Claim FROM claims"
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Total_Claim"])
    st.dataframe(df)

# Query 20: Unique cities with providers
if st.checkbox("List of all unique cities with providers"):
    query = "SELECT DISTINCT City FROM providers"
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["City"])
    st.dataframe(df)

# Query 21: Unique food types offered
if st.checkbox("List of all food types offered"):
    query = "SELECT DISTINCT Food_Type FROM food_listings"
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Food_Type"])
    st.dataframe(df)

# Query 22: Meal type count
if st.checkbox("Count of each meal type"):
    query = """
    SELECT Meal_Type, COUNT(*) AS Count FROM food_listings
    GROUP BY Meal_Type;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Meal_Type", "Count"])
    st.dataframe(df)

# Query 23: Provider count by type
if st.checkbox("How many providers are there of each type"):
    query = """
    SELECT Type AS Provider_Type, COUNT(*) AS Total
    FROM providers
    GROUP BY Type;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["Provider_Type", "Total"])
    st.dataframe(df)


st.success("App Loaded Successfully!")

st.caption("Made by Yashodhara Dhusia")

