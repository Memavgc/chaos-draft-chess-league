import streamlit as st
import json, random, os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# CSS per UI scura e professionale
st.markdown("""
<style>
.stApp { background-color: #0b0e14; color: #e0e0e0; }
.main-container {
    background-color: #151921;
    padding: 20px;
    border: 2px solid #f1c40f;
    border-radius: 10px;
}
.stButton>button { width: 100%; border-radius: 5px; border: 1px solid #444; transition: 0.3s; }
.stButton>button:hover { border-color: #f1c40f; color: #f1c40f; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE INTEGRALI ---
NATURES_DB = {
    "Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA",
    "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA",
    "Quiet": "+SpA, -Spe", "Brave": "+Atk, -Spe", "Relaxed": "+Def, -Spe", "Sassy": "+SpD, -Spe",
    "Hardy": "Neutrale", "Serious": "Neutrale", "Quirky": "Neutrale", "Bashful": "Neutrale"
}

# Database Abilità (Precedente versione espansa)
ABILITIES_DB = [
    "Huge Power", "Magic Guard", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", 
    "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Supreme Overlord", 
    "Good as Gold", "Unaware", "Poison Heal", "Guts", "Magic Bounce", "Drizzle", "Drought", 
    "Sand Stream", "Snow Warning", "Libero", "Defiant", "Serene Grace", "Prankster", "Triage",
    "Beast Boost", "Soul-Heart", "Armor Tail", "Purifying Salt", "Well-Baked Flaw", "Thermal Exchange",
    "Wonder Guard", "Ice Scales", "Fur Coat", "Simple", "Toxic Debris", "Hadron Engine", "Orichalcum Pulse"
]

# --- POOL OGGETTI ESPANSO (60+ Strumenti) ---
ITEMS_DB = [
    # Competitivi Standard
    "Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", 
    "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Eviolite", "Air Balloon",
    # Bacche
    "Lum Berry", "Sitrus Berry", "Berry Juice", "Enigma Berry", "Custap Berry", "Liechi Berry", 
    "Ganlon Berry", "Salac Berry", "Petaya Berry", "Apicot Berry", "Kee Berry", "Maranga Berry",
    # Utility & Strategia
    "White Herb", "Mental Herb", "Power Herb", "Flame Orb", "Toxic Orb", "Eject Button", 
    "Eject Pack", "Red Card", "Blunder Policy", "Weakness Policy", "Room Service", "Iron Ball",
    "Lagging Tail", "Full Incense", "Clear Amulet", "Covert Cloak", "Loaded Dice", "Punching Glove",
    # Weather & Terrain
    "Light Clay", "Terrain Extender", "Damp Rock", "Heat Rock", "Smooth Rock", "Icy Rock",
    # Recupero e Danni
    "Black Sludge", "Big Root", "Binding Band", "Metronome", "Scope Lens", "Razor Claw",
    # Potenziamento Tipi
    "Black Belt", "Black Glasses", "Charcoal", "Dragon Fang", "Hard Stone", "Magnet", 
    "Miracle Seed", "Mystic Water", "Never-Melt Ice", "Poison Barb", "Sharp Beak", "Silk Scarf", 
    "Silver Powder", "Soft Sand", "Spell Tag", "Twisted Spoon"
]

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

# --- CARICAMENTO ASSETS (Versione Robusta) ---
@st.cache_data
def load_assets():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pkmn_path = os.path.join(current_dir, "data", "pokemon_clean.json")
        moves_path = os.path.join(current_dir, "data", "moves.json")
        
        with open(pkmn_path, "r", encoding="utf-8") as f:
            pkmn_data = json.load(f)
        with open(moves_path, "r", encoding="utf-8") as f:
            moves_data = json.load(f)

        # Pulizia: assicuriamoci che ogni pkmn sia un dizionario con la chiave 'name'
        clean_pool = []
        for p in pkmn_data:
            if isinstance(p, dict) and 'name' in p:
                clean_pool.append(p)
            elif isinstance(p, str):
                clean_pool.append({'name': p}) # Se è solo una stringa, la trasformiamo
        
        m_data = {nm: {
            "type": m.get("type", "Normal"), 
            "bp": m.get("basePower", 0), 
            "cat": m.get("category", "Status").replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato"),
            "desc": m.get("shortDesc", "Nessuna descrizione.")
        } for nm, m in moves_data.items() if m.get("num", 0) > 0 and not m.get("isZ")}
        
        return clean_pool, m_data
    except Exception as e:
        st.error(f"Errore nei dati: {e}")
        return [], {}

pkmn_pool, moves_db = load_assets()

# --- STATO SESSIONE ---
if 'team' not in st.session_state:
    st.session_state.team = []
    st.session_state.step = "DRAFT_PKMN"
    st.session_state.temp_pkmn = None
    st.session_state.options = []

# --- UI ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")

col_main, col_side = st.columns([2.5, 1.5])

# --- RIEPILOGO TEAM A DESTRA ---
with col_side:
    st.subheader("🏟️ ROSTER ATTUALE (6 MAX)")
    if not st.session_state.team:
        st.info("Nessun Pokémon draftato.")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**", expanded=True):
            st.markdown(f"**Item:** {p['item']} | **Ability:** {p['ability']}")
            st.markdown(f"**Nature:** {p['nature']} | **EVs:** {p['spread']}")
            st.markdown(f"**Moves:** {', '.join(p['moves'])}")

# --- AREA DI DRAFT PRINCIPALE ---
with col_main:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    if st.session_state.step == "DRAFT_PKMN":
        st.header(f"Seleziona Pokémon {len(st.session_state.team)+1}/6")
        if not st.session_state.options: 
            st.session_state.options = random.sample(pkmn_pool, 3)
        
        cols = st.columns(3)
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                # Recupero sicuro del nome
                name = p.get('name', 'Unknown') if isinstance(p, dict) else str(p)
                clean = name.lower().replace(" ", "").replace("-", "")
                
                st.image(f"https://play.pokemonshowdown.com/sprites/ani/{clean}.gif", width=120)
                if st.button(f"Scegli {name.upper()}", key=f"pk_{i}"):
                    st.session_state.temp_pkmn = {"name": name, "moves": []}
                    st.session_state.options = []
                    st.session_state.step = "MOVES"
                    st.rerun()

    elif st.session_state.step in ["MOVES", "ABILITY", "ITEM", "NATURE", "SPREAD"]:
        p = st.session_state.temp_pkmn
        
        # Sotto-fase: MOSSE (1 alla volta per 4 volte)
        if st.session_state.step == "MOVES":
            st.subheader(f"Mossa {len(p['moves'])+1}/4 per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = random.sample(list(moves_db.keys()), 4)
            for m in st.session_state.options:
                m_i = moves_db[m]
                with st.container():
                    st.markdown(f"**{m}** | {m_i['type']} | BP: {m_i['bp']} | {m_i['cat']}")
                    st.caption(f"*IT:* {m_i['desc']}")
                    if st.button(f"Scegli {m}", key=f"m_{m}"):
                        p['moves'].append(m); st.session_state.options = []
                        if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                        st.rerun()

        elif st.session_state.step == "ABILITY":
            st.subheader(f"Abilità per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = random.sample(ABILITIES_DB, 4)
            for a in st.session_state.options:
                if st.button(a): st.session_state.temp_pkmn['ability'] = a; st.session_state.options = []; st.session_state.step = "ITEM"; st.rerun()
        
        elif st.session_state.step == "ITEM":
            st.subheader(f"Oggetto per {p['name'].upper()}")
            # Qui usiamo il nuovo pool espanso
            if not st.session_state.options: st.session_state.options = random.sample(ITEMS_DB, 4)
            for i in st.session_state.options:
                if st.button(i): st.session_state.temp_pkmn['item'] = i; st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

        elif st.session_state.step == "NATURE":
            st.subheader(f"Natura per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = random.sample(list(NATURES_DB.keys()), 4)
            for n in st.session_state.options:
                if st.button(f"{n} ({NATURES_DB[n]})"): st.session_state.temp_pkmn['nature'] = n; st.session_state.options = []; st.session_state.step = "SPREAD"; st.rerun()

        elif st.session_state.step == "SPREAD":
            st.subheader(f"EV Spread Chaos per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = [gen_chaos_spread() for _ in range(4)]
            for s in st.session_state.options:
                if st.button(s): 
                    st.session_state.temp_pkmn['spread'] = s; st.session_state.team.append(st.session_state.temp_pkmn)
                    st.session_state.options = []; st.session_state.step = "DRAFT_PKMN" if len(st.session_state.team) < 6 else "FINISHED"
                    st.rerun()

        # --- RIEPILOGO IN BASSO (Mentre costruisci) ---
        st.divider()
        st.markdown(f"**🛠️ STAI CONFIGURANDO:** {p['name'].upper()}")
        st.caption(f"Mosse caricate: {', '.join(p['moves']) if p['moves'] else 'In attesa...'}")

    elif st.session_state.step == "FINISHED":
        st.header("🏁 ROSTER COMPLETO!")
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n"
            for m in p['moves']: res += f"- {m}\n"
            res += "\n"
        st.code(res, language="text")
        if st.button("RICOMINCIA DRAFT"): st.session_state.clear(); st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)