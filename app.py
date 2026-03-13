import streamlit as st
import json, random, os
import requests

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# CSS: Sfondo scuro standard, UI pulita
st.markdown("""
<style>
.stApp { background-color: #0e1117; color: #e0e0e0; }
.main-container {
    background-color: rgba(21, 25, 33, 0.95);
    padding: 20px;
    border: 2px solid #f1c40f;
    border-radius: 10px;
    margin-bottom: 20px;
}
.stButton>button { width: 100%; border-radius: 5px; background-color: #1f2530; color: white; border: 1px solid #444; transition: 0.3s; }
.stButton>button:hover { border-color: #f1c40f; color: #f1c40f; }
.type-badge {
    padding: 2px 10px; border-radius: 4px; color: white; font-weight: bold;
    text-shadow: 1px 1px 2px black; display: inline-block; margin: 2px;
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
    "Hardy": "Neutrale", "Serious": "Neutrale", "Quirky": "Neutrale", "Bashful": "Neutrale"
}

ABILITIES_DB = [
    "Huge Power", "Intrepid Sword", "Dauntless Shield", "Mold Breaker", "Intimidate", 
    "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", 
    "Adaptability", "Sheer Force", "Sharpness", "Supreme Overlord", "Good as Gold", 
    "Unaware", "Poison Heal", "Guts", "Magic Bounce", "Drizzle", "Drought", 
    "Sand Stream", "Snow Warning", "Libero", "Defiant", "Serene Grace", "Prankster", 
    "Triage", "Beast Boost", "Soul-Heart", "Armor Tail", "Purifying Salt", 
    "Well-Baked Flaw", "Thermal Exchange", "Wonder Guard", "Ice Scales", "Fur Coat", 
    "Simple", "Toxic Debris", "Hadron Engine", "Orichalcum Pulse", "As One (Glastrier)",
    "Desolate Land", "Primordial Sea", "Delta Stream", "Shadow Tag", "Parental Bond"
]

ITEMS_DB = [
    "Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", 
    "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Eviolite", "Air Balloon",
    "Lum Berry", "Sitrus Berry", "White Herb", "Mental Herb", "Power Herb", "Flame Orb", 
    "Toxic Orb", "Eject Button", "Eject Pack", "Red Card", "Blunder Policy", "Weakness Policy", 
    "Light Clay", "Terrain Extender", "Damp Rock", "Heat Rock", "Smooth Rock", "Icy Rock",
    "Black Sludge", "Metronome", "Scope Lens", "Razor Claw"
]

BLACKLIST_MOSSE = [
    "splash", "celebrate", "happyhour", "holdhands", "confide", "playnice", "growl", "tailwhip", 
    "leer", "sandattack", "smokescreen", "kinesis", "flash", "stringshot", "sweetscent", 
    "sharpen", "harden", "withdraw", "defensecurl", "burnup", "darkvoid", "doubleshock", 
    "hyperspacefury", "auroraveil", "naturepower", "mudsport", "watersport", "luckychant", 
    "memento", "razorwind", "skyattack", "skullbash", "furyswipes", "cometpunch", "barrage", 
    "doubleslap", "armthrust", "tackle", "poisonsting", "confusion", "scratch", "pound", 
    "gust", "ember", "watergun", "vinewhip", "thundershock", "peck", "absorb", "astonish",
    "bide", "constrict", "fairywind", "megadrain", "mudslap", "powdersnow", "smog", 
    "visegrip", "bubble", "twister", "payday", "snore"
]

# --- HELPERS ---
def get_type_badge(t):
    color = TYPE_COLORS.get(t, "#68A090")
    return f'<span class="type-badge" style="background-color:{color};">{t}</span>'

@st.cache_data(show_spinner=False)
def get_sprite(name):
    clean = "".join(e for e in name.lower() if e.isalnum())
    return f"https://play.pokemonshowdown.com/sprites/ani/{clean}.gif"

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

@st.cache_data
def load_assets():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pk_path = os.path.join(current_dir, "data", "pokemon_clean.json")
        mv_path = os.path.join(current_dir, "data", "moves.json")
        
        if not os.path.exists(pk_path) or not os.path.exists(mv_path):
            return [], {}

        with open(pk_path, "r", encoding="utf-8") as f: pkmn_data = json.load(f)
        with open(mv_path, "r", encoding="utf-8") as f: moves_data = json.load(f)
        
        clean_pkmn = [p for p in pkmn_data if "gmax" not in p.get('name','').lower() and 
                      "tera" not in p.get('name','').lower() and p.get('tier','') not in ["UBER", "AG"]]
        
        clean_moves = {}
        for nm, m in moves_data.items():
            nm_clean = nm.lower().replace(" ","").replace("-","")
            if nm_clean not in BLACKLIST_MOSSE and not m.get("isZ") and not m.get("isMax"):
                clean_moves[nm] = {
                    "type": m.get("type", "Normal"), 
                    "bp": m.get("basePower", 0),
                    "cat": m.get("category", "Status").replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato")
                }
        return clean_pkmn, clean_moves
    except: return [], {}

pkmn_pool, moves_db = load_assets()

# --- LOGICA ---
if 'team' not in st.session_state:
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set(), 'used_moves': set()})

st.title("♟️ CHAOS DRAFT CHESS LEAGUE")
col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.subheader("🏟️ ROSTER")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**"):
            if p['moves']: st.write(f"Moves: {', '.join(p['moves'])}")
            if p['ability']: st.write(f"Abilità: {p['ability']}")
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    if st.session_state.step == "DRAFT_PKMN":
        st.header(f"Scegli Pokémon {len(st.session_state.team)+1}/6")
        available = [p for p in pkmn_pool if p['name'] not in st.session_state.used_pkmn]
        
        if not available:
            st.error("Errore: Nessun Pokémon disponibile nel database! Controlla il file JSON.")
        else:
            if not st.session_state.options:
                # FIX: Prendi il minimo tra 3 e gli elementi rimasti
                sample_size = min(3, len(available))
                st.session_state.options = random.sample(available, sample_size)
                for opt in st.session_state.options: st.session_state.used_pkmn.add(opt['name'])
            
            cols = st.columns(len(st.session_state.options))
            for i, p in enumerate(st.session_state.options):
                with cols[i]:
                    st.image(get_sprite(p['name']), width=120)
                    if st.button(f"SCEGLI {p['name'].upper()}", key=f"pk_{i}"):
                        st.session_state.team.append({"name": p['name'], "moves": [], "ability": "", "item": "", "nature": "", "spread": ""})
                        st.session_state.options = []
                        if len(st.session_state.team) == 6: st.session_state.step = "MOVES"
                        st.rerun()

    elif st.session_state.step == "MOVES":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.subheader(f"Mosse per {p['name'].upper()} ({len(p['moves'])+1}/4)")
        if not st.session_state.options:
            avail = [m for m in moves_db.keys() if m not in st.session_state.used_moves]
            pool_atk = [m for m in avail if moves_db[m]['cat'] in ["Fisico", "Speciale"]]
            m_dmg = random.choice(pool_atk) if pool_atk else random.choice(avail)
            others = random.sample([m for m in avail if m != m_dmg], min(3, len(avail)-1))
            st.session_state.options = others + [m_dmg]
            random.shuffle(st.session_state.options)
        
        for m in st.session_state.options:
            if st.button(f"{m} ({moves_db[m]['type']} | BP: {moves_db[m]['bp']})", key=f"m_{m}"):
                p['moves'].append(m); st.session_state.used_moves.add(m); st.session_state.options = []
                if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                st.rerun()

    elif st.session_state.step == "ABILITY":
        if not st.session_state.options: st.session_state.options = random.sample(ABILITIES_DB, 4)
        for a in st.session_state.options:
            if st.button(a): st.session_state.team[st.session_state.current_pkmn_idx]['ability'] = a; st.session_state.options = []; st.session_state.step = "ITEM"; st.rerun()

    elif st.session_state.step == "ITEM":
        if not st.session_state.options: st.session_state.options = random.sample(ITEMS_DB, 4)
        for i in st.session_state.options:
            if st.button(i): st.session_state.team[st.session_state.current_pkmn_idx]['item'] = i; st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

    elif st.session_state.step == "NATURE":
        if not st.session_state.options: st.session_state.options = random.sample(list(NATURES_DB.keys()), 4)
        for n in st.session_state.options:
            if st.button(f"{n} ({NATURES_DB[n]})"): st.session_state.team[st.session_state.current_pkmn_idx]['nature'] = n; st.session_state.options = []; st.session_state.step = "SPREAD"; st.rerun()

    elif st.session_state.step == "SPREAD":
        if not st.session_state.options: st.session_state.options = [gen_chaos_spread() for _ in range(4)]
        for s in st.session_state.options:
            if st.button(s):
                st.session_state.team[st.session_state.current_pkmn_idx]['spread'] = s
                st.session_state.options = []; st.session_state.used_moves = set()
                if st.session_state.current_pkmn_idx < 5: st.session_state.current_pkmn_idx += 1; st.session_state.step = "MOVES"
                else: st.session_state.step = "FINISHED"
                st.rerun()

    elif st.session_state.step == "FINISHED":
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("RESET"): st.session_state.clear(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)