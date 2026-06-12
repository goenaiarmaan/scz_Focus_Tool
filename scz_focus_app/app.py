
import sqlite3
from datetime import date, datetime
from pathlib import Path
import streamlit as st

DB_PATH = Path("focus_app.db")

st.set_page_config(
    page_title="SCZ Focus App",
    page_icon="🎯",
    layout="wide"
)

# -----------------------------
# Database
# -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_focus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        focus_date TEXT UNIQUE,
        energy_level INTEGER,
        mood TEXT,
        main_goal TEXT,
        start_trigger TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT,
        priority TEXT,
        status TEXT,
        stakeholder TEXT,
        due_date TEXT,
        next_action TEXT,
        blocker TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback_waiting (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL,
        waiting_on TEXT,
        sent_date TEXT,
        follow_up_date TEXT,
        status TEXT,
        note TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS toolbox_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        audience TEXT,
        message TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS wins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        win_date TEXT,
        description TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def fetch_all(query, params=()):
    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def execute(query, params=()):
    conn = get_conn()
    conn.execute(query, params)
    conn.commit()
    conn.close()

def get_today_focus():
    rows = fetch_all("SELECT * FROM daily_focus WHERE focus_date = ?", (str(date.today()),))
    return rows[0] if rows else None

def upsert_today_focus(energy_level, mood, main_goal, start_trigger):
    existing = get_today_focus()
    now = datetime.now().isoformat(timespec="seconds")
    if existing:
        execute("""
        UPDATE daily_focus
        SET energy_level=?, mood=?, main_goal=?, start_trigger=?
        WHERE focus_date=?
        """, (energy_level, mood, main_goal, start_trigger, str(date.today())))
    else:
        execute("""
        INSERT INTO daily_focus (focus_date, energy_level, mood, main_goal, start_trigger, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (str(date.today()), energy_level, mood, main_goal, start_trigger, now))

init_db()

# -----------------------------
# Helper UI
# -----------------------------
def status_badge(status):
    return {
        "Nieuw": "🆕 Nieuw",
        "Bezig": "🔄 Bezig",
        "Wachten op feedback": "⏳ Wachten op feedback",
        "Geblokkeerd": "🚧 Geblokkeerd",
        "Afgerond": "✅ Afgerond",
    }.get(status, status)

def priority_score(priority):
    return {"Hoog": 1, "Middel": 2, "Laag": 3}.get(priority, 9)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🎯 SCZ Focus App")
page = st.sidebar.radio(
    "Ga naar",
    [
        "Dagstart",
        "Focus Dashboard",
        "Taken",
        "Wachten op feedback",
        "Toolbox Generator",
        "Wins & Consistentie"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Lokaal draaiend. Data wordt opgeslagen in SQLite.")

# -----------------------------
# Page: Dagstart
# -----------------------------
if page == "Dagstart":
    st.title("☕ Dagstart")
    st.write("Deze pagina vervangt je automatische YouTube/news-start met een korte focus-check.")

    today_focus = get_today_focus()

    with st.form("daily_focus_form"):
        energy = st.slider(
            "Hoeveel energie heb je nu?",
            min_value=1,
            max_value=10,
            value=int(today_focus["energy_level"]) if today_focus else 6
        )
        mood = st.selectbox(
            "Hoe voel je je?",
            ["Rustig", "Gemotiveerd", "Loom", "Gestrest", "Ongefocust", "Sterk"],
            index=0
        )
        main_goal = st.text_input(
            "Wat is vandaag je belangrijkste resultaat?",
            value=today_focus["main_goal"] if today_focus else ""
        )
        start_trigger = st.selectbox(
            "Startregel voor vandaag",
            [
                "Eerst 25 minuten werken voordat ik YouTube open",
                "Eerst top 3 taken kiezen",
                "Eerst één pending feedback opvolgen",
                "Eerst één document afronden",
                "Eerst toolbox voorbereiden"
            ]
        )
        submitted = st.form_submit_button("Dagstart opslaan")

    if submitted:
        upsert_today_focus(energy, mood, main_goal, start_trigger)
        st.success("Dagstart opgeslagen. Start klein, maar start wel.")

    st.markdown("### Vandaagregel")
    st.info("Niet wachten tot je motivatie krijgt. Begin met 25 minuten focus en laat motivatie daarna komen.")

# -----------------------------
# Page: Focus Dashboard
# -----------------------------
elif page == "Focus Dashboard":
    st.title("📌 Focus Dashboard")

    today_focus = get_today_focus()

    col1, col2, col3 = st.columns(3)
    open_tasks = fetch_all("SELECT * FROM tasks WHERE status != 'Afgerond'")
    waiting = fetch_all("SELECT * FROM feedback_waiting WHERE status != 'Afgerond'")
    wins_today = fetch_all("SELECT * FROM wins WHERE win_date = ?", (str(date.today()),))

    col1.metric("Open taken", len(open_tasks))
    col2.metric("Wachten op feedback", len(waiting))
    col3.metric("Wins vandaag", len(wins_today))

    if today_focus:
        st.markdown("### Jouw focus vandaag")
        st.write(f"**Hoofddoel:** {today_focus['main_goal'] or 'Nog niet ingevuld'}")
        st.write(f"**Startregel:** {today_focus['start_trigger']}")
        st.progress(today_focus["energy_level"] / 10)
    else:
        st.warning("Je hebt je dagstart nog niet ingevuld.")

    st.markdown("### Top taken")
    top_tasks = sorted(open_tasks, key=lambda r: (priority_score(r["priority"]), r["due_date"] or "9999-99-99"))[:5]

    if top_tasks:
        for task in top_tasks:
            with st.container(border=True):
                st.write(f"**{task['title']}**")
                st.caption(f"{task['priority']} | {status_badge(task['status'])} | Stakeholder: {task['stakeholder'] or '-'}")
                st.write(f"Volgende actie: {task['next_action'] or '-'}")
    else:
        st.success("Geen open taken. Mooi moment om proactief werk te kiezen.")

    st.markdown("### Feedback die je werk blokkeert")
    if waiting:
        for item in waiting[:5]:
            with st.container(border=True):
                st.write(f"**{item['item']}**")
                st.caption(f"Wachten op: {item['waiting_on'] or '-'} | Follow-up: {item['follow_up_date'] or '-'}")
                st.write(item["note"] or "")
    else:
        st.success("Geen feedback-blokkades geregistreerd.")

# -----------------------------
# Page: Taken
# -----------------------------
elif page == "Taken":
    st.title("✅ Taken")

    with st.expander("Nieuwe taak toevoegen", expanded=True):
        with st.form("task_form"):
            title = st.text_input("Taak")
            category = st.selectbox("Categorie", ["Focus", "Document", "Meeting", "Toolbox", "Stakeholder", "Roadmap", "Implementatie", "Overig"])
            priority = st.selectbox("Prioriteit", ["Hoog", "Middel", "Laag"])
            status = st.selectbox("Status", ["Nieuw", "Bezig", "Wachten op feedback", "Geblokkeerd", "Afgerond"])
            stakeholder = st.text_input("Stakeholder")
            due_date = st.date_input("Deadline", value=None)
            next_action = st.text_area("Volgende actie")
            blocker = st.text_area("Blokkade")
            submit_task = st.form_submit_button("Taak opslaan")

        if submit_task and title:
            now = datetime.now().isoformat(timespec="seconds")
            execute("""
            INSERT INTO tasks (title, category, priority, status, stakeholder, due_date, next_action, blocker, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, category, priority, status, stakeholder, str(due_date) if due_date else "", next_action, blocker, now, now))
            st.success("Taak toegevoegd.")

    st.markdown("### Open taken")
    tasks = fetch_all("SELECT * FROM tasks ORDER BY created_at DESC")

    for task in tasks:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{task['title']}**")
            c2.write(task["priority"])
            c3.write(status_badge(task["status"]))
            st.caption(f"Categorie: {task['category']} | Stakeholder: {task['stakeholder'] or '-'} | Deadline: {task['due_date'] or '-'}")
            st.write(f"Volgende actie: {task['next_action'] or '-'}")
            if task["blocker"]:
                st.warning(f"Blokkade: {task['blocker']}")

            new_status = st.selectbox(
                "Status aanpassen",
                ["Nieuw", "Bezig", "Wachten op feedback", "Geblokkeerd", "Afgerond"],
                index=["Nieuw", "Bezig", "Wachten op feedback", "Geblokkeerd", "Afgerond"].index(task["status"]),
                key=f"status_{task['id']}"
            )
            if st.button("Update status", key=f"update_{task['id']}"):
                execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?", (new_status, datetime.now().isoformat(timespec="seconds"), task["id"]))
                st.success("Status bijgewerkt.")
                st.rerun()

# -----------------------------
# Page: Wachten op feedback
# -----------------------------
elif page == "Wachten op feedback":
    st.title("⏳ Wachten op feedback")
    st.write("Hier registreer je alles waar je niet verder mee kan omdat iemand anders moet reageren.")

    with st.form("feedback_form"):
        item = st.text_input("Waar wacht je op?")
        waiting_on = st.text_input("Van wie?")
        sent_date = st.date_input("Verstuurd op", value=date.today())
        follow_up_date = st.date_input("Follow-up datum", value=date.today())
        status = st.selectbox("Status", ["Open", "Opgevolgd", "Afgerond"])
        note = st.text_area("Notitie")
        submit_feedback = st.form_submit_button("Opslaan")

    if submit_feedback and item:
        execute("""
        INSERT INTO feedback_waiting (item, waiting_on, sent_date, follow_up_date, status, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item, waiting_on, str(sent_date), str(follow_up_date), status, note, datetime.now().isoformat(timespec="seconds")))
        st.success("Feedback-item opgeslagen.")

    rows = fetch_all("SELECT * FROM feedback_waiting ORDER BY follow_up_date ASC")
    for row in rows:
        with st.container(border=True):
            st.write(f"**{row['item']}**")
            st.caption(f"Wachten op: {row['waiting_on'] or '-'} | Verstuurd: {row['sent_date']} | Follow-up: {row['follow_up_date']} | Status: {row['status']}")
            st.write(row["note"] or "")

# -----------------------------
# Page: Toolbox Generator
# -----------------------------
elif page == "Toolbox Generator":
    st.title("🧰 Toolbox Generator")
    st.write("Omdat je aangaf dat toolbox maken vaak dubbel werk is, kun je hier standaardberichten opbouwen.")

    topic = st.text_input("Onderwerp", placeholder="Bijvoorbeeld: Scherm vergrendelen")
    audience = st.selectbox("Doelgroep", ["TWC groep", "IT groep", "HR", "Alle medewerkers", "Afdelingshoofden"])
    key_message = st.text_area("Kernboodschap", placeholder="Wat wil je dat medewerkers begrijpen of doen?")
    action = st.text_input("Concrete actie", placeholder="Bijvoorbeeld: Druk Windows + L wanneer je wegloopt.")
    tone = st.selectbox("Tone of voice", ["Professioneel", "Luchtig", "Motiverend", "Kort en direct"])

    if st.button("Genereer toolbox bericht"):
        intro = "IT Awareness Tip"
        if tone == "Luchtig":
            intro = "IT Tip van de Week"
        elif tone == "Motiverend":
            intro = "Slimmer en veiliger werken"
        elif tone == "Kort en direct":
            intro = "IT Reminder"

        generated = f"""
**{intro} – {topic}**

{key_message}

**Wat kun je doen?**  
{action}

Een kleine gewoonte kan een groot verschil maken in veiligheid, continuïteit en professioneel werken.
""".strip()

        st.markdown("### Conceptbericht")
        st.text_area("Kopieerbaar bericht", generated, height=220)

        if st.button("Sla template op"):
            execute("""
            INSERT INTO toolbox_templates (topic, audience, message, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (topic, audience, generated, "Concept", datetime.now().isoformat(timespec="seconds")))
            st.success("Toolbox-template opgeslagen.")

    st.markdown("### Opgeslagen toolbox templates")
    templates = fetch_all("SELECT * FROM toolbox_templates ORDER BY created_at DESC")
    for t in templates:
        with st.container(border=True):
            st.write(f"**{t['topic']}**")
            st.caption(f"Doelgroep: {t['audience']} | Status: {t['status']}")
            st.text_area("Bericht", t["message"], height=160, key=f"template_{t['id']}")

# -----------------------------
# Page: Wins & Consistentie
# -----------------------------
elif page == "Wins & Consistentie":
    st.title("🏆 Wins & Consistentie")
    st.write("Gebruik dit om jezelf te motiveren. Niet alleen taken tellen, maar ook vooruitgang zichtbaar maken.")

    with st.form("wins_form"):
        win_date = st.date_input("Datum", value=date.today())
        description = st.text_area("Wat heb je vandaag goed gedaan?")
        submit_win = st.form_submit_button("Win opslaan")

    if submit_win and description:
        execute("""
        INSERT INTO wins (win_date, description, created_at)
        VALUES (?, ?, ?)
        """, (str(win_date), description, datetime.now().isoformat(timespec="seconds")))
        st.success("Win opgeslagen. Dit bouwt bewijs dat je groeit.")

    wins = fetch_all("SELECT * FROM wins ORDER BY win_date DESC, created_at DESC")
    for win in wins:
        with st.container(border=True):
            st.write(f"**{win['win_date']}**")
            st.write(win["description"])
