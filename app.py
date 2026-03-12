import streamlit as st
import json, random, os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# CSS per UI, Sfondo Ufficiale, Colori Tipi e Recap
st.markdown("""
<style>
.stApp { 
    background-image: url("data/background.png");
    background-size: cover;
    background-attachment: fixed;
    color: #e0e0e0; 
}
.main-container {
    background-color: rgba(21, 25, 33, 0.95);
    padding: 20px;
    border: 2px solid #f1c40f;
    border-radius: 10px;
}
.stButton>button { width: 100%; border-radius: 5px; border: 1px solid #444; transition: 0.3s; background-color: #1f2530; color: white; }
.stButton>button:hover { border-color: #f1c40f; color: #f1c40f; }
.type-badge {
    padding: 3px 10px;
    border-radius: 5px;
    color: white;
    font-weight: bold;
    text-shadow: 1px 1px 2px black;
    display: inline-block;
    margin-bottom: 5px;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE COLORI E TIPI ---
TYPE_COLORS = {
    "Normal": "#A8A77A", "Fire": "#EE8130", "Water": "#6390F0", "Electric": "#F7D02C",
    "Grass": "#7AC74C", "Ice": "#96D9D2", "Fighting": "#C22E28", "Poison": "#A33EA1",
    "Ground": "#E2BF65", "Flying": "#A98FF3", "Psychic": "#F95587", "Bug": "#A6B91A",
    "Rock": "#B6A136", "Ghost": "#735797", "Dragon": "#6F35FC", "Steel": "#B7B7CE", 
    "Fairy": "#D685AD", "Dark": "#705848"
}

def get_type_badge(t):
    color = TYPE_COLORS.get(t, "#68A090")
    return f'<span class="type-badge" style="background-color:{color};">{t}</span>'

import streamlit as st
import json, random, os
import requests  # <--- AGGIUNGI QUESTO IMPORT

# ... (CSS e TYPE_COLORS rimangono uguali) ...

# --- HELPERS ---
@st.cache_data(show_spinner=False)
def get_sprite(name):
    # 1. Prova il nome completo (es: Charizard-Mega -> charizardmega)
    clean_full = "".join(e for e in name.lower() if e.isalnum())
    url_full = f"https://play.pokemonshowdown.com/sprites/ani/{clean_full}.gif"
    
    try:
        # Fai un check rapido per vedere se l'immagine esiste sul server
        response = requests.head(url_full, timeout=2)
        if response.status_code == 200:
            return url_full
    except:
        pass
        
    # 2. Se non esiste (es: Starmie-Mega o Genesect-Shock), usa il Pokémon base
    base_name = name.split("-")[0]
    clean_base = "".join(e for e in base_name.lower() if e.isalnum())
    return f"https://play.pokemonshowdown.com/sprites/ani/{clean_base}.gif"

# ... (Il resto del codice rimane uguale) ...
def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

# --- DATABASE INTEGRALI ---
NATURES_DB = {
    "Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA",
    "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA",
    "Quiet": "+SpA, -Spe", "Brave": "+Atk, -Spe", "Relaxed": "+Def, -Spe", "Sassy": "+SpD, -Spe",
    "Hardy": "Neutrale", "Serious": "Neutrale", "Quirky": "Neutrale", "Bashful": "Neutrale"
}

ABILITIES_DB = [
    "Huge Power", "Magic Guard", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", 
    "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Supreme Overlord", 
    "Good as Gold", "Unaware", "Poison Heal", "Guts", "Magic Bounce", "Drizzle", "Drought", 
    "Sand Stream", "Snow Warning", "Libero", "Defiant", "Serene Grace", "Prankster", "Triage",
    "Beast Boost", "Soul-Heart", "Armor Tail", "Purifying Salt", "Well-Baked Flaw", "Thermal Exchange",
    "Wonder Guard", "Ice Scales", "Fur Coat", "Simple", "Toxic Debris", "Hadron Engine", "Orichalcum Pulse"
]

ITEMS_DB = [
    "Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", 
    "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Eviolite", "Air Balloon",
    "Lum Berry", "Sitrus Berry", "Berry Juice", "Enigma Berry", "Custap Berry", "Liechi Berry", 
    "White Herb", "Mental Herb", "Power Herb", "Flame Orb", "Toxic Orb", "Eject Button", 
    "Eject Pack", "Red Card", "Blunder Policy", "Weakness Policy", "Room Service", "Iron Ball",
    "Light Clay", "Terrain Extender", "Damp Rock", "Heat Rock", "Smooth Rock", "Icy Rock",
    "Black Sludge", "Big Root", "Binding Band", "Metronome", "Scope Lens", "Razor Claw",
    "Black Belt", "Black Glasses", "Charcoal", "Dragon Fang", "Hard Stone", "Magnet", 
    "Miracle Seed", "Mystic Water", "Never-Melt Ice", "Poison Barb", "Sharp Beak", "Silk Scarf"
]

# Lista di backup per bloccare gli Uber se il JSON non ha la voce "tier"
UBERS_FALLBACK = [
    "mewtwo", "lugia", "ho-oh", "kyogre", "groudon", "rayquaza", "dialga", "palkia", 
    "giratina", "arceus", "reshiram", "zekrom", "kyurem", "xerneas", "yveltal", "zygarde", 
    "cosmog", "cosmoem", "solgaleo", "lunala", "necrozma", "zacian", "zamazenta", "eternatus", 
    "calyrex", "koraidon", "miraidon", "terapagos"
]

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

        # 1. Filtro Pokémon (Rimuove G-Max, Tera e UBERS)
        clean_pool = []
        for p in pkmn_data:
            name = p.get('name', p) if isinstance(p, dict) else str(p)
            n_lower = name.lower()
            tier = str(p.get('tier', '')).upper() if isinstance(p, dict) else ""
            
            # Filtro forme non standard
            if "gmax" in n_lower or "gigantamax" in n_lower or "tera" in n_lower:
                continue
            
            # Filtro Uber (tramite tier o lista fallback)
            if tier in ["UBER", "AG"] or any(uber in n_lower for uber in UBERS_FALLBACK):
                continue
                
            clean_pool.append({'name': name})
        
        # 2. Filtro Mosse
        m_data = {}
        for nm, m in moves_data.items():
            nm_lower = nm.lower()
            if m.get("num", 0) > 0 and not m.get("isZ") and not m.get("isMax"):
                if "g-max" in nm_lower or "max " in nm_lower or "tera " in nm_lower:
                    continue
                m_data[nm] = {
                    "type": m.get("type", "Normal"), 
                    "bp": m.get("basePower", 0), 
                    "cat": m.get("category", "Status").replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato"),
                    "desc": m.get("shortDesc", "Nessuna descrizione.")
                }
        return clean_pool, m_data
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return [], {}

pkmn_pool, moves_db = load_assets()

# --- STATO SESSIONE ---
if 'team' not in st.session_state:
    st.session_state.team = [] 
    st.session_state.step = "DRAFT_PKMN"
    st.session_state.current_pkmn_idx = 0 
    st.session_state.options = []

# --- UI ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")

col_main, col_side = st.columns([2.5, 1.5])

# --- RIEPILOGO LATERALE ---
with col_side:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.subheader("🏟️ ROSTER ATTUALE")
    if not st.session_state.team:
        st.info("Inizia a draftare i tuoi 6 Pokémon!")
    else:
        for i, p in enumerate(st.session_state.team):
            with st.expander(f"**{i+1}. {p['name'].upper()}**", expanded=True):
                st.markdown(f"**Item:** {p.get('item', '---')} | **Ability:** {p.get('ability', '---')}")
                st.markdown(f"**Nature:** {p.get('nature', '---')} | **EVs:** {p.get('spread', '---')}")
                st.markdown(f"**Moves:** {', '.join(p.get('moves', []))}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- AREA DI DRAFT PRINCIPALE ---
with col_main:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    if st.session_state.step == "DRAFT_PKMN":
        num_draftati = len(st.session_state.team)
        st.header(f"Seleziona Pokémon {num_draftati+1}/6")
        
        if not st.session_state.options: 
            # Assicurati che ci siano abbastanza Pokémon nel pool, altrimenti non crasha
            sample_size = min(3, len(pkmn_pool))
            st.session_state.options = random.sample(pkmn_pool, sample_size)
            
        cols = st.columns(3)
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                name = p['name']
                st.image(get_sprite(name), width=120)
                if st.button(f"Scegli {name.upper()}", key=f"pk_{i}"):
                    st.session_state.team.append({"name": name, "moves": [], "ability": "", "item": "", "nature": "", "spread": ""})
                    st.session_state.options = []
                    if len(st.session_state.team) == 6:
                        st.session_state.step = "MOVES"
                        st.session_state.current_pkmn_idx = 0
                    st.rerun()

    elif st.session_state.step in ["MOVES", "ABILITY", "ITEM", "NATURE", "SPREAD"]:
        curr_idx = st.session_state.current_pkmn_idx
        p = st.session_state.team[curr_idx]
        
        if st.session_state.step == "MOVES":
            st.subheader(f"Mossa {len(p['moves'])+1}/4 per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = random.sample(list(moves_db.keys()), 4)
            for m in st.session_state.options:
                m_i = moves_db[m]
                with st.container():
                    st.markdown(f"**{m}** | {get_type_badge(m_i['type'])} | BP: {m_i['bp']} | {m_i['cat']}", unsafe_allow_html=True)
                    st.caption(f"*IT:* {m_i['desc']}")
                    if st.button(f"Scegli {m}", key=f"m_{m}"):
                        p['moves'].append(m); st.session_state.options = []
                        if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                        st.rerun()

        elif st.session_state.step == "ABILITY":
            st.subheader(f"Abilità per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = random.sample(ABILITIES_DB, 4)
            for a in st.session_state.options:
                if st.button(a): p['ability'] = a; st.session_state.options = []; st.session_state.step = "ITEM"; st.rerun()
        
        elif st.session_state.step == "ITEM":
            st.subheader(f"Oggetto per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = random.sample(ITEMS_DB, 4)
            for i in st.session_state.options:
                if st.button(i): p['item'] = i; st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

        elif st.session_state.step == "NATURE":
            st.subheader(f"Natura per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = random.sample(list(NATURES_DB.keys()), 4)
            for n in st.session_state.options:
                if st.button(f"{n} ({NATURES_DB[n]})"): p['nature'] = n; st.session_state.options = []; st.session_state.step = "SPREAD"; st.rerun()

        elif st.session_state.step == "SPREAD":
            st.subheader(f"EV Spread Chaos per {p['name'].upper()}")
            if not st.session_state.options: st.session_state.options = [gen_chaos_spread() for _ in range(4)]
            for s in st.session_state.options:
                if st.button(s): 
                    p['spread'] = s
                    st.session_state.options = []
                    if curr_idx < 5:
                        st.session_state.current_pkmn_idx += 1
                        st.session_state.step = "MOVES"
                    else:
                        st.session_state.step = "FINISHED"
                    st.rerun()

        st.divider()
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(get_sprite(p['name']), width=80)
        with col2:
            st.markdown(f"**🛠️ STAI CONFIGURANDO:** {p['name'].upper()} (Pokémon {curr_idx+1}/6)")
            st.caption(f"Mosse: {', '.join(p['moves']) if p['moves'] else 'In attesa...'}")

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