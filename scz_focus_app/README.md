
# SCZ Focus App

Een simpele localhost-app voor dagelijkse focus, taken, feedback-wachttijd, toolbox-berichten en motivatie.

## Waarom deze app?

Deze app is niet bedoeld als vervanging van Notion.  
Notion blijft je centrale document- en projectomgeving.

Deze app is bedoeld als jouw persoonlijke werkstarter:

- Minder automatisch starten met YouTube
- Sneller focus kiezen
- Dagelijkse top taken zien
- Wachten op feedback zichtbaar maken
- Toolbox-berichten sneller opmaken
- Consistentie en wins bijhouden

## Installatie

Open Terminal in deze map en voer uit:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Daarna opent de app lokaal in je browser.

Meestal op:

```text
http://localhost:8501
```

## Bestanden

- `app.py` - de app
- `requirements.txt` - benodigde packages
- `focus_app.db` - wordt automatisch aangemaakt zodra je de app start

## Eerste gebruik

1. Ga naar Dagstart
2. Vul je energie, gevoel en hoofddoel in
3. Voeg maximaal 3 belangrijke taken toe
4. Zet alles waar je op wacht in Wachten op feedback
5. Gebruik Toolbox Generator voor terugkerende awareness/toolbox berichten

## Advies

Gebruik deze app elke ochtend 5 minuten voordat je YouTube, nieuws of losse berichten opent.
