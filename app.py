import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0e1117; color: #e0e0e0; }
.main-container {
    background-color: rgba(21, 25, 33, 0.95);
    padding: 20px; border: 2px solid #f1c40f;
    border-radius: 10px; margin-bottom: 20px;
}
.stButton>button { width: 100%; border-radius: 5px; background-color: #1f2530; color: white; border: 1px solid #444; transition: 0.2s; }
.stButton>button:hover { border-color: #f1c40f; color: #f1c40f; }
.type-badge {
    padding: 2px 10px; border-radius: 4px; color: white; font-weight: bold;
    text-shadow: 1px 1px 2px black; display: inline-block; margin: 2px; font-size: 0.8em;
}
.cat-badge {
    padding: 2px 8px; border-radius: 4px; color: black; font-weight: bold;
    display: inline-block; margin: 2px; font-size: 0.7em; background-color: #fff;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE ---
TYPE_COLORS = {
    "Normal": "#A8A77A", "Fire": "#EE8130", "Water": "#6390F0", "Electric": "#F7D02C",
    "Grass": "#7AC74C", "Ice": "#96D9D2", "Fighting": "#C22E28", "Poison": "#A33EA1",
    "Ground": "#E2BF65", "Flying": "#A98FF3", "Psychic": "#F95587", "Bug": "#A6B91A",
    "Rock": "#B6A136", "Ghost": "#735797", "Dragon": "#6F35FC", "Steel": "#B7B7CE", 
    "Fairy": "#D685AD", "Dark": "#705848"
}

NATURES_DB = {
    "Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA",
    "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA",
    "Quiet": "+SpA, -Spe", "Brave": "+Atk, -Spe", "Relaxed": "+Def, -Spe", "Sassy": "+SpD, -Spe",
    "Hardy": "Neutrale", "Serious": "Neutrale", "Quirky": "Neutrale", "Bashful": "Neutrale",
    "Naive": "+Spe, -SpD", "Hasty": "+Spe, -Def", "Lonely": "+Atk, -Def", "Mild": "+SpA, -Def",
    "Rash": "+SpA, -SpD", "Naughty": "+Atk, -SpD", "Lax": "+Def, -SpD"
}

# ESPANSIONE ITEM DB
ITEMS_DB = [
    "Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", 
    "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Eviolite", "Air Balloon",
    "Lum Berry", "Sitrus Berry", "White Herb", "Mental Herb", "Power Herb", "Flame Orb", 
    "Toxic Orb", "Eject Button", "Eject Pack", "Red Card", "Blunder Policy", "Weakness Policy", 
    "Light Clay", "Terrain Extender", "Damp Rock", "Heat Rock", "Smooth Rock", "Icy Rock",
    "Black Sludge", "Metronome", "Scope Lens", "Razor Claw", "Covert Cloak", "Loaded Dice",
    "Punching Glove", "Big Root", "Binding Band", "Clear Amulet", "Mirror Herb", "Amulet Coin",
    "Shell Bell", "Wise Glasses", "Muscle Band", "Leppa Berry", "Custap Berry", "Kee Berry",
    "Maranga Berry", "Adrenaline Orb", "Utility Umbrella", "Protective Pads", "Safety Goggles"
]

# RIMOZIONE "AS ONE"
ABILITIES_DB = [
    "Huge Power", "Intrepid Sword", "Dauntless Shield", "Mold Breaker", "Intimidate", 
    "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", 
    "Adaptability", "Sheer Force", "Sharpness", "Supreme Overlord", "Good as Gold", 
    "Unaware", "Poison Heal", "Guts", "Magic Bounce", "Drizzle", "Drought", 
    "Sand Stream", "Snow Warning", "Libero", "Defiant", "Serene Grace", "Prankster", 
    "Triage", "Beast Boost", "Soul-Heart", "Armor Tail", "Purifying Salt", 
    "Well-Baked Flaw", "Thermal Exchange", "Wonder Guard", "Ice Scales", "Fur Coat", 
    "Simple", "Toxic Debris", "Hadron Engine", "Orichalcum Pulse", "Desolate Land", 
    "Primordial Sea", "Delta Stream", "Shadow Tag", "Parental Bond", "Gale Wings", 
    "Stamina", "Gooey", "Iron Barbs"
]

@st.cache_data
def get_sprite(name):
    clean = "".join(e for e in name.lower() if e.isalnum())
    return f"https://play.pokemonshowdown.com/sprites/ani/{clean}.gif"

@st.cache_data
def load_assets():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pk_path = os.path.join(current_dir, "data", "pokemon_clean.json")
        mv_path = os.path.join(current_dir, "data", "moves.json")
        with open(pk_path, "r", encoding="utf-8") as f: pk_raw = json.load(f)
        with open(mv_path, "r", encoding="utf-8") as f: mv_raw = json.load(f)

        clean_pkmn = []
        pk_list = pk_raw.values() if isinstance(pk_raw, dict) else pk_raw
        for p in pk_list:
            if isinstance(p, dict):
                name = p.get('name') or p.get('Name')
                tier = str(p.get('tier') or p.get('Tier') or "").upper()
                if name and tier not in ["UBER", "AG"]: clean_pkmn.append({'name': name, 'tier': tier})
            elif isinstance(p, str): clean_pkmn.append({'name': p, 'tier': 'N/A'})

        clean_moves = {}
        for nm, m in mv_raw.items():
            if isinstance(m, dict):
                cat = m.get("category") or m.get("Category") or "Status"
                clean_moves[nm] = {
                    "type": m.get("type") or m.get("Type") or "Normal", 
                    "bp": m.get("basePower") or m.get("BasePower") or 0,
                    "cat": cat.replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato")
                }
        return clean_pkmn, clean_moves
    except: return [], {}

pkmn_pool, moves_db = load_assets()

# --- LOGICA ---
if 'team' not in st.session_state:
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set(), 'used_moves': set()})

st.title("♟️ CHAOS DRAFT CHESS LEAGUE")

if not pkmn_pool:
    st.error("Database non trovato.")
    st.stop()

col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.subheader("🏟️ ROSTER")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"{i+1}. {p['name'].upper()}"):
            if p['moves']: st.write(f"Mosse: {', '.join(p['moves'])}")
            if p['ability']: st.caption(f"{p['ability']} @ {p['item']}")
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    if st.session_state.step == "DRAFT_PKMN":
        st.header(f"Pokémon {len(st.session_state.team)+1}/6")
        available = [p for p in pkmn_pool if p['name'] not in st.session_state.used_pkmn]
        if not st.session_state.options:
            st.session_state.options = random.sample(available, min(3, len(available)))
        
        cols = st.columns(len(st.session_state.options))
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                st.image(get_sprite(p['name']), width=150)
                if st.button(f"SCEGLI {p['name']}", key=f"pk_{i}"):
                    st.session_state.team.append({"name": p['name'], "moves": [], "ability": "", "item": "", "nature": "", "spread": ""})
                    st.session_state.options = []; st.session_state.used_pkmn.add(p['name'])
                    if len(st.session_state.team) == 6: st.session_state.step = "MOVES"
                    st.rerun()

    elif st.session_state.step == "MOVES":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Mosse per {p['name']} ({len(p['moves'])+1}/4)")
        if not st.session_state.options:
            avail = [m for m in moves_db.keys() if m not in st.session_state.used_moves]
            st.session_state.options = random.sample(avail, 4)
        
        for m in st.session_state.options:
            info = moves_db[m]
            st.markdown(f"**{m}** <span class='type-badge' style='background:{TYPE_COLORS.get(info['type'], '#666')}'>{info['type']}</span> <span class='cat-badge'>{info['cat']}</span> | Potenza: {info['bp']}", unsafe_allow_html=True)
            if st.button(f"Scegli {m}", key=f"mv_{m}"):
                p['moves'].append(m); st.session_state.used_moves.add(m); st.session_state.options = []
                if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                st.rerun()

    elif st.session_state.step == "ABILITY":
        if not st.session_state.options: st.session_state.options = random.sample(ABILITIES_DB, 4)
        for a in st.session_state.options:
            if st.button(a): 
                st.session_state.team[st.session_state.current_pkmn_idx]['ability'] = a
                st.session_state.options = []; st.session_state.step = "ITEM"; st.rerun()

    elif st.session_state.step == "ITEM":
        if not st.session_state.options: st.session_state.options = random.sample(ITEMS_DB, 4)
        for i in st.session_state.options:
            if st.button(i): 
                st.session_state.team[st.session_state.current_pkmn_idx]['item'] = i
                st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

    elif st.session_state.step == "NATURE":
        if not st.session_state.options: st.session_state.options = random.sample(list(NATURES_DB.keys()), 4)
        for n in st.session_state.options:
            if st.button(f"{n} ({NATURES_DB[n]})"): 
                st.session_state.team[st.session_state.current_pkmn_idx]['nature'] = n
                st.session_state.options = []; st.session_state.used_moves = set()
                if st.session_state.current_pkmn_idx < 5:
                    st.session_state.current_pkmn_idx += 1; st.session_state.step = "MOVES"
                else: st.session_state.step = "FINISHED"
                st.rerun()

    elif st.session_state.step == "FINISHED":
        st.header("Draft Completo!")
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("RESET"): st.session_state.clear(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)