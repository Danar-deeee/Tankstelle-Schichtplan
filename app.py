import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Tankstelle Schichtplan", layout="centered")
st.title("⛽ Tankstelle Schichtplan")

mitarbeiter = ["Frei/offen", "Marcus", "Anschi", "Armin Seidl", "Ecaterina Murzacova", "Sabine Fischer", "zicke", "Christina", "Blbas Danar"]
shifts = ["Frühschicht", "Spätschicht"]

# 1. SMART DATABASE SWITCH: Use cloud online, or local memory if offline
if "local_fallback_db" not in st.session_state:
    st.session_state.local_fallback_db = {}

db_online = None
try:
    # Try connecting to the internet database
    db_online = st.connection("kv")
except Exception:
    # If offline/local, this prevents the "SecretsNotFoundError" crash
    pass

# 2. Week Selection (Allows looking at different weeks)
today = datetime.date.today()
current_monday = today - datetime.timedelta(days=today.weekday())

st.write("### 📅 Woche auswählen")
selected_monday = st.date_input("Wähle den Montag der Schichtwoche:", current_monday)
selected_monday = selected_monday - datetime.timedelta(days=selected_monday.weekday())

# Generate dates for that specific week
days_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
date_strings = []
for i in range(7):
    day_date = selected_monday + datetime.timedelta(days=i)
    date_strings.append(f"{days_de[i]} ({day_date.strftime('%d.%m.%Y')})")

week_key = f"week_{selected_monday.strftime('%Y_%m_%d')}"

# 3. Fetch data based on whether we are online or offline
saved_data = None
if db_online is not None:
    try:
        saved_data = db_online.get(week_key)
    except Exception:
        saved_data = st.session_state.local_fallback_db.get(week_key)
else:
    saved_data = st.session_state.local_fallback_db.get(week_key)

if saved_data is None:
    blank_plan = {shift: ["Frei/offen"] * 7 for shift in shifts}
    df = pd.DataFrame(blank_plan, index=date_strings)
else:
    df = pd.DataFrame.from_dict(saved_data, orient="index", columns=shifts)
    df.index = date_strings

# 4. Access Control Sidebar
with st.sidebar:
    st.header("🔑 Admin Login")
    user_role = st.selectbox("Wer bist du?", ["Mitarbeiter (Nur Anschauen)", "Marcus (Manager)", "Blbas Danar"])
    password = st.text_input("Passwort eingeben", type="password")

has_access = False
if user_role == "Marcus (Manager)" and password == "marcus2026":
    has_access = True
elif user_role == "Blbas Danar" and password == "danar2026":
    has_access = True

# 5. Editing View
if has_access:
    st.info(f"Du bearbeitest gerade die Woche vom {selected_monday.strftime('%d.%m.%Y')}")
    with st.form("schicht_form"):
        updated_data = {}
        for day in date_strings:
            st.write(f"### {day}")
            col1, col2 = st.columns(2)

            current_f = df.loc[day, "Frühschicht"] if day in df.index else "Frei/offen"
            current_s = df.loc[day, "Spätschicht"] if day in df.index else "Frei/offen"

            with col1:
                f_select = st.selectbox(f"Früh", mitarbeiter, index=mitarbeiter.index(current_f) if current_f in mitarbeiter else 0, key=f"{day}_f")
            with col2:
                s_select = st.selectbox(f"Spät", mitarbeiter, index=mitarbeiter.index(current_s) if current_s in mitarbeiter else 0, key=f"{day}_s")

            updated_data[day] = [f_select, s_select]

        submit = st.form_submit_button("Plan für diese Woche online speichern")
        if submit:
            # Save to internet database if available, otherwise save to temporary local memory
            if db_online is not None:
                try:
                    db_online.set(week_key, updated_data)
                except Exception:
                    st.session_state.local_fallback_db[week_key] = updated_data
            else:
                st.session_state.local_fallback_db[week_key] = updated_data

            st.toast("Erfolgreich gespeichert! 💾")
            st.rerun()

# 6. Public Screen for Everyone
st.write(f"## 📋 Schichtplan für die Woche vom {selected_monday.strftime('%d.%m.%Y')}")
st.dataframe(df, use_container_width=True)
