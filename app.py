import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Tankstelle Schichtplan", layout="centered")
st.title("⛽ Tankstelle Schichtplan")

# REMOVED YOUR NAME FROM THE TEAM LIST
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

# 1. DATABASE & LOGIN SYSTEM SETUP
if "local_fallback_db" not in st.session_state:
    st.session_state.local_fallback_db = {}

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

db_online = None
try:
    db_online = st.connection("kv")
except Exception:
    pass

# 2. FETCH DAILY ANNOUNCEMENT
announcement_key = "daily_announcement"
current_announcement = ""

if db_online is not None:
    try:
        current_announcement = db_online.get(announcement_key) or ""
    except Exception:
        current_announcement = st.session_state.local_fallback_db.get(announcement_key, "")
else:
    current_announcement = st.session_state.local_fallback_db.get(announcement_key, "")

# Display announcement with red German header
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

# 3. WEEK SELECTION
today = datetime.date.today()
current_monday = today - datetime.timedelta(days=today.weekday())

st.write("### 📅 Woche auswählen")
selected_monday = st.date_input("Wähle den Montag der Schichtwoche:", current_monday)
selected_monday = selected_monday - datetime.timedelta(days=selected_monday.weekday())

days_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
date_strings = []
for i in range(7):
    day_date = selected_monday + datetime.timedelta(days=i)
    date_strings.append(f"{days_de[i]} ({day_date.strftime('%d.%m.%Y')})")

week_key = f"week_{selected_monday.strftime('%Y_%m_%d')}"

# 4. FETCH SHIFT DATA
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

# 5. ACCESS CONTROL SIDEBAR (Only Marcus and Mitarbeiter)
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

        # ONLY MARCUS CAN LOG IN NOW
        if user_role == "Marcus (Manager)" and password == "Tiger2026":
            st.session_state.is_logged_in = True
            st.rerun()

# 6. ADMIN EDITING VIEW
if st.session_state.is_logged_in:
    st.markdown("---")
    st.subheader("🛠️ Admin-Optionen")

    new_announcement = st.text_area("📢 Ankündigung für das Team bearbeiten (Deutsch):", value=current_announcement)

    with st.form("schicht_form"):
        st.write(f"### Schichten bearbeiten für: {selected_monday.strftime('%d.%m.%Y')}")
        updated_data = {}
        for day in date_strings:
            st.write(f"**{day}**")
            col1, col2 = st.columns(2)

            current_f = df.loc[day, "Frühschicht"] if day in df.index else "Frei/offen"
            current_s = df.loc[day, "Spätschicht"] if day in df.index else "Frei/offen"

            with col1:
                f_select = st.selectbox(f"Früh", mitarbeiter, index=mitarbeiter.index(current_f) if current_f in mitarbeiter else 0, key=f"{day}_f")
            with col2:
                s_select = st.selectbox(f"Spät", mitarbeiter, index=mitarbeiter.index(current_s) if current_s in mitarbeiter else 0, key=f"{day}_s")

            updated_data[day] = [f_select, s_select]

        submit = st.form_submit_button("Änderungen (Plan & Ankündigung) online speichern")
        if submit:
            if db_online is not None:
                try:
                    db_online.set(week_key, updated_data)
                    db_online.set(announcement_key, new_announcement)
                except Exception:
                    st.session_state.local_fallback_db[week_key] = updated_data
                    st.session_state.local_fallback_db[announcement_key] = new_announcement
            else:
                st.session_state.local_fallback_db[week_key] = updated_data
                st.session_state.local_fallback_db[announcement_key] = new_announcement

            st.toast("Alles erfolgreich gespeichert! 💾")
            st.rerun()

# 7. PUBLIC SCREEN FOR EVERYONE
st.write(f"## 📋 Schichtplan für die Woche vom {selected_monday.strftime('%d.%m.%Y')}")
st.dataframe(df, use_container_width=True)
