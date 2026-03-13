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
.stButton>button { width: 100%; border-radius: 5px; background-color: #1f2530; color: white; border: 1px solid #444; }
.stButton>button:hover { border-color: #f1c40f; color: #f1c40f; }
.type-badge {
    padding: 4px 12px; border-radius: 6px; color: white; font-weight: bold;
    text-shadow: 2px 2px 3px rgba(0,0,0,0.8); display: inline-block; 
    margin: 3px; font-size: 0.9em; text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# --- DB COLORI ---
TYPE_COLORS = {"Normal": "#A8A77A", "Fire": "#EE8130", "Water": "#6390F0", "Electric": "#F7D02C", "Grass": "#7AC74C", "Ice": "#96D9D2", "Fighting": "#C22E28", "Poison": "#A33EA1", "Ground": "#E2BF65", "Flying": "#A98FF3", "Psychic": "#F95587", "Bug": "#A6B91A", "Rock": "#B6A136", "Ghost": "#735797", "Dragon": "#6F35FC", "Steel": "#B7B7CE", "Fairy": "#D685AD", "Dark": "#705848"}

# --- DB INTEGRALI (Nature, Item, Abilità) ---
NATURES_DB = {"Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA", "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA", "Quiet": "+SpA, -Spe", "Brave": "+Atk, -Spe", "Relaxed": "+Def, -Spe", "Sassy": "+SpD, -Spe", "Hardy": "Neutrale", "Serious": "Neutrale", "Quirky": "Neutrale", "Bashful": "Neutrale", "Naive": "+Spe, -SpD", "Hasty": "+Spe, -Def", "Lonely": "+Atk, -Def", "Mild": "+SpA, -Def", "Rash": "+SpA, -SpD", "Naughty": "+Atk, -SpD", "Lax": "+Def, -SpD"}
ITEMS_DB = ["Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Eviolite", "Air Balloon", "Lum Berry", "Sitrus Berry", "White Herb", "Mental Herb", "Power Herb", "Flame Orb", "Toxic Orb", "Eject Button", "Eject Pack", "Red Card", "Blunder Policy", "Weakness Policy", "Light Clay", "Terrain Extender", "Damp Rock", "Heat Rock", "Smooth Rock", "Icy Rock", "Black Sludge", "Metronome", "Scope Lens", "Razor Claw", "Muscle Band", "Wise Glasses", "Covert Cloak", "Loaded Dice", "Punching Glove", "Big Root", "Binding Band", "Clear Amulet", "Mirror Herb", "Amulet Coin", "Shell Bell", "Leppa Berry", "Custap Berry", "Kee Berry", "Maranga Berry", "Adrenaline Orb", "Utility Umbrella", "Protective Pads", "Safety Goggles", "Bright Powder", "King's Rock", "Quick Claw", "Lagging Tail", "Iron Ball", "Full Incense"]
ABILITIES_DB = ["Huge Power", "Intrepid Sword", "Dauntless Shield", "Mold Breaker", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Supreme Overlord", "Good as Gold", "Unaware", "Poison Heal", "Guts", "Magic Bounce", "Drizzle", "Drought", "Sand Stream", "Snow Warning", "Libero", "Defiant", "Serene Grace", "Prankster", "Triage", "Beast Boost", "Soul-Heart", "Armor Tail", "Purifying Salt", "Well-Baked Flaw", "Thermal Exchange", "Wonder Guard", "Ice Scales", "Fur Coat", "Simple", "Toxic Debris", "Hadron Engine", "Orichalcum Pulse", "Desolate Land", "Primordial Sea", "Delta Stream", "Shadow Tag", "Parental Bond", "Stamina", "Gale Wings", "Gooey", "Iron Barbs", "Rough Skin", "Defeatist", "Slow Start", "Truant", "Berserk", "Infiltrator", "Magic Guard", "No Guard", "Overcoat", "Pure Power", "Rain Dish", "Swift Swim", "Chlorophyll", "Solar Power", "Sand Rush", "Slush Rush", "Surge Surfer", "Competitive", "Steadfast", "Justified", "Rattled", "Pressure"]

# --- FUNZIONI ---
def get_sprite(name):
    clean_name = "".join(e for e in name.lower() if e.isalnum())
    return f"https://play.pokemonshowdown.com/sprites/ani/{clean_name}.gif"

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

@st.cache_data
def load_assets():
    pk_pool = []
    mv_pool = {}
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "data", "pokemon_clean.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            # Gestione robusta della struttura JSON
            raw_list = data.values() if isinstance(data, dict) else data
            for p in raw_list:
                nm = p.get('name') or p.get('Name')
                tr = str(p.get('tier') or p.get('Tier') or "").upper()
                if nm and "GMAX" not in nm.upper() and tr not in ["UBER", "AG"]:
                    pk_pool.append({'name': nm, 'tier': tr})
        
        with open(os.path.join(current_dir, "data", "moves.json"), "r", encoding="utf-8") as f:
            mv_data = json.load(f)
            for nm, m in mv_data.items():
                cat = m.get("category") or m.get("Category") or "Status"
                mv_pool[nm] = {"type": m.get("type") or "Normal", "bp": m.get("basePower") or 0, "cat": cat.replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato")}
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
    
    # EMERGENZA: Se il pool è vuoto, usa dati di fallback per non crashare
    if not pk_pool:
        pk_pool = [{'name': 'Pikachu', 'tier': 'N/A'}, {'name': 'Charizard', 'tier': 'N/A'}, {'name': 'Lucario', 'tier': 'N/A'}]
    return pk_pool, mv_pool

pkmn_pool, moves_db = load_assets()

# --- SESSION STATE ---
if 'team' not in st.session_state:
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set()})

# --- UI ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")
col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.subheader("🏟️ TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**"):
            if p['moves']: st.caption(f"Mosse: {', '.join(p['moves'])}")
            if p['ability']: st.caption(f"{p['ability']} @ {p['item']}")
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    if st.session_state.step == "DRAFT_PKMN":
        # Filtra i pokemon non usati
        available = [p for p in pkmn_pool if p['name'] not in st.session_state.used_pkmn]
        
        # FIX DEFINITIVO: Se available < 3, ripopola o usa il pool totale
        if len(available) < 3:
            available = pkmn_pool
            
        if not st.session_state.options:
            # random.sample fallisce se il numero richiesto > lunghezza lista
            n_to_sample = min(len(available), 3)
            st.session_state.options = random.sample(available, n_to_sample)
        
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
            m_list = list(moves_db.keys())
            st.session_state.options = random.sample(m_list, min(len(m_list), 4))
        
        for m in st.session_state.options:
            info = moves_db.get(m, {"type": "Normal", "bp": 0, "cat": "Stato"})
            st.markdown(f"**{m}** <span class='type-badge' style='background:{TYPE_COLORS.get(info['type'], '#666')}'>{info['type']}</span> | BP: {info['bp']}", unsafe_allow_html=True)
            if st.button(f"Scegli {m}", key=f"mv_{m}"):
                p['moves'].append(m); st.session_state.options = []
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
                st.session_state.options = []; st.session_state.step = "SPREAD"; st.rerun()

    elif st.session_state.step == "SPREAD":
        if not st.session_state.options: st.session_state.options = [gen_chaos_spread() for _ in range(4)]
        for s in st.session_state.options:
            if st.button(s):
                st.session_state.team[st.session_state.current_pkmn_idx]['spread'] = s
                st.session_state.options = []
                if st.session_state.current_pkmn_idx < 5:
                    st.session_state.current_pkmn_idx += 1; st.session_state.step = "MOVES"
                else: st.session_state.step = "FINISHED"
                st.rerun()

    elif st.session_state.step == "FINISHED":
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("🔄 RESET"): st.session_state.clear(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)