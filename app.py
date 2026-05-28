import streamlit as st
import pandas as pd
import datetime
import json
import os

st.set_page_config(page_title="Tankstelle Schichtplan", layout="centered")
st.title("⛽ Tankstelle Schichtplan")

mitarbeiter = [
    "Frei/offen",
    "Marcus",
    "Anschi",
    "Armin Seidl",
    "Ecaterina Murzacova",
    "Sabine Fischer",
    "zicke",
    "Christina"
]
shifts = ["Frühschicht", "Spätschicht"]

# INTERNAL DATA STORAGE (Bypasses Streamlit's missing menus!)
DATA_FILE = "schichtplan_data.json"

def load_all_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"daily_announcement": "", "shifts": {}}

def save_all_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Initialize and load data
app_data = load_all_data()

# Display announcement banner
current_announcement = app_data.get("daily_announcement", "")
if current_announcement:
    st.markdown(
        f"""
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545; margin-bottom: 20px;">
            <p style="color: #dc3545; font-weight: bold; margin: 0 0 10px 0; font-size: 18px;">📢 WICHTIGE MITTEILUNG:</p>
            <p style="color: #111111; margin: 0; white-space: pre-wrap;">{current_announcement}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Week Selection
today = datetime.date.today()
current_monday = today - datetime.timedelta(days=today.weekday())

st.write("### 📅 Woche auswählen")
selected_monday = st.date_input("Wähle den Montag der Schichtwoche:", current_monday)
selected_monday = selected_monday - datetime.timedelta(days=selected_monday.weekday())

days_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
date_strings = [f"{days_de[i]} ({(selected_monday + datetime.timedelta(days=i)).strftime('%d.%m.%Y')})" for i in range(7)]
week_key = f"week_{selected_monday.strftime('%Y_%m_%d')}"

# Fetch specific week shift data
saved_shifts = app_data.get("shifts", {}).get(week_key, None)
if saved_shifts is None:
    df = pd.DataFrame({shift: ["Frei/offen"] * 7 for shift in shifts}, index=date_strings)
else:
    df = pd.DataFrame.from_dict(saved_shifts, orient="index", columns=shifts)
    df.index = date_strings

# Login System
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

with st.sidebar:
    st.header("🔑 Admin Area")
    if st.session_state.is_logged_in:
        st.success("Eingeloggt als Admin")
        if st.button("🔴 Logout / Sperren"):
            st.session_state.is_logged_in = False
            st.rerun()
    else:
        user_role = st.selectbox("Wer bist du?", ["Mitarbeiter (Nur Anschauen)", "Marcus (Manager)"])
        password = st.text_input("Passwort eingeben", type="password")
        if user_role == "Marcus (Manager)" and password == "Tiger2026":
            st.session_state.is_logged_in = True
            st.rerun()

# Admin Editing View
if st.session_state.is_logged_in:
    st.markdown("---")
    st.subheader("🛠️ Admin-Optionen")
    new_announcement = st.text_area("📢 Ankündigung für das Team bearbeiten (Deutsch):", value=current_announcement)

    with st.form("schicht_form"):
        st.write(f"### Schichten bearbeiten für: {selected_monday.strftime('%d.%m.%Y')}")
        updated_shifts = {}
        for day in date_strings:
            st.write(f"**{day}**")
            col1, col2 = st.columns(2)
            current_f = df.loc[day, "Frühschicht"] if day in df.index else "Frei/offen"
            current_s = df.loc[day, "Spätschicht"] if day in df.index else "Frei/offen"

            with col1:
                f_select = st.selectbox(f"Früh", mitarbeiter, index=mitarbeiter.index(current_f) if current_f in mitarbeiter else 0, key=f"{day}_f")
            with col2:
                s_select = st.selectbox(f"Spät", mitarbeiter, index=mitarbeiter.index(current_s) if current_s in mitarbeiter else 0, key=f"{day}_s")
            updated_shifts[day] = [f_select, s_select]

        if st.form_submit_button("Änderungen online speichern"):
            app_data["daily_announcement"] = new_announcement
            if "shifts" not in app_data:
                app_data["shifts"] = {}
            app_data["shifts"][week_key] = updated_shifts

            save_all_data(app_data)
            st.toast("Erfolgreich gespeichert! 💾")
            st.rerun()

# Public Display
st.write(f"## 📋 Schichtplan für die Woche vom {selected_monday.strftime('%d.%m.%Y')}")
st.dataframe(df, use_container_width=True)
