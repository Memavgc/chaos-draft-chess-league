import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- CSS: DARK MODE ---
st.markdown("""
<style>
.stApp { background-color: #0e1117; color: #e0e0e0; }
.main-container {
    background-color: rgba(21, 25, 33, 0.95);
    padding: 20px; border: 2px solid #f1c40f;
    border-radius: 10px; margin-bottom: 20px;
}
.type-badge {
    padding: 4px 12px; border-radius: 6px; color: white; font-weight: bold;
    text-shadow: 2px 2px 3px rgba(0,0,0,0.8); display: inline-block; 
    margin: 3px; font-size: 0.85em; text-transform: uppercase;
}
.cat-badge {
    padding: 3px 10px; border-radius: 5px; color: black; font-weight: bold;
    display: inline-block; margin: 3px; font-size: 0.75em; background-color: #ffffff;
}
.move-card {
    margin-bottom: 10px; padding: 10px; border-radius: 5px; 
    background: rgba(255,255,255,0.05); border-left: 4px solid #f1c40f;
}
</style>
""", unsafe_allow_html=True)

TYPE_COLORS = {"Normal": "#A8A77A", "Fire": "#EE8130", "Water": "#6390F0", "Electric": "#F7D02C", "Grass": "#7AC74C", "Ice": "#96D9D2", "Fighting": "#C22E28", "Poison": "#A33EA1", "Ground": "#E2BF65", "Flying": "#A98FF3", "Psychic": "#F95587", "Bug": "#A6B91A", "Rock": "#B6A136", "Ghost": "#735797", "Dragon": "#6F35FC", "Steel": "#B7B7CE", "Fairy": "#D685AD", "Dark": "#705848"}

# --- FUNZIONI ---
def get_sprite(name):
    # Rimuove Mega, Gmax, e suffissi vari per caricare lo sprite base se quello specifico manca
    n = name.lower()
    # Se è una Mega, carichiamo il base per evitare l'errore 404
    base_name = n.split('-')[0].split(' ')[0]
    # Pulizia caratteri speciali
    clean = "".join(e for e in base_name if e.isalnum())
    return f"https://play.pokemonshowdown.com/sprites/ani/{clean}.gif"

@st.cache_data
def load_assets():
    pk_pool = []; mv_pool = {}
    # Banlist Leggendari Copertina
    pk_banned = ["ZACIAN", "ZAMAZENTA", "ETERNATUS", "MEWTWO", "RAYQUAZA", "KYOGRE", "GROUDON", "ARCEUS", "DIALGA", "PALKIA", "GIRATINA", "XERNEAS", "YVELTAL", "SOLGALEO", "LUNALA", "CALYREX", "KORAIDON", "MIRAIDON", "DEOXYS", "DARKRAI"]
    
    # BANLIST MOSSE DEFINITIVA (PULIZIA TOTALE)
    mv_banned_exact = [
        "pound", "mudsport", "watersport", "snore", "constrict", "bide", "refresh", 
        "splash", "celebrate", "holdhands", "tailslap", "barrage", "foresight", 
        "odorsleuth", "miracleeye", "hiddenpower", "hiddenpowerground", "hiddenpowerfire",
        "hiddenpowerwater", "hiddenpowergrass", "soak", "tailwhip", "leer", "growl",
        "tackle", "scratch", "sharpen", "meditate", "doubleteam", "minimize"
    ]

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "data", "pokemon_clean.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data.items() if isinstance(data, dict) else enumerate(data)
            for key, val in items:
                nm = val.get('name') if isinstance(val, dict) else str(val)
                nm_up = nm.upper()
                if "GMAX" in nm_up: continue
                if any(b in nm_up for b in pk_banned): continue
                pk_pool.append({'name': nm})

        with open(os.path.join(current_dir, "data", "moves.json"), "r", encoding="utf-8") as f:
            mv_data = json.load(f)
            for nm, m in mv_data.items():
                nm_up = nm.upper()
                clean_m = nm.lower().replace(" ", "").replace("-", "")
                # Filtro G-Max, Z-Moves e Lista Nera
                if any(x in nm_up for x in ["G-MAX", "GMAX", " Z-", "MAX "]): continue
                if clean_m in mv_banned_exact: continue
                
                if isinstance(m, dict):
                    cat = m.get("category") or m.get("Category") or "Status"
                    mv_pool[nm] = {
                        "type": m.get("type", "Normal"), 
                        "bp": m.get("basePower", 0), 
                        "cat": cat.replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato")
                    }
    except Exception as e: st.error(f"Errore caricamento: {e}")
    return pk_pool, mv_pool

pkmn_pool, moves_db = load_assets()

# --- DATABASE FISSI ---
NATURES_DB = {"Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA", "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA", "Naive": "+Spe, -SpD", "Hasty": "+Spe, -Def"}
ITEMS_DB = ["Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Eviolite", "Air Balloon", "Lum Berry", "White Herb", "Mental Herb", "Power Herb", "Flame Orb", "Toxic Orb", "Clear Amulet", "Mirror Herb", "Loaded Dice", "Covert Cloak"]
ABILITIES_DB = ["Huge Power", "Intrepid Sword", "Dauntless Shield", "Mold Breaker", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Supreme Overlord", "Good as Gold", "Unaware", "Poison Heal", "Guts", "Magic Bounce", "Drizzle", "Drought", "Sand Stream", "Snow Warning", "Libero", "Defiant", "Serene Grace", "Prankster", "Triage"]

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

if 'team' not in st.session_state:
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set()})

# --- INTERFACCIA ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")
col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.subheader("🏟️ TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**"):
            if p['moves']: st.caption(f"Mosse: {', '.join(p['moves'])}")
            if p['ability']: st.caption(f"**{p['ability']}** @ {p['item']}")
            if p['spread']: st.caption(f"EVs: {p['spread']}")
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    if st.session_state.step == "DRAFT_PKMN":
        available = [p for p in pkmn_pool if p['name'] not in st.session_state.used_pkmn]
        if not st.session_state.options: st.session_state.options = random.sample(available, 3)
        cols = st.columns(3)
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                st.image(get_sprite(p['name']), width=150)
                if st.button(f"SCEGLI {p['name']}", key=f"pk_{i}"):
                    st.session_state.team.append({"name": p['name'], "moves": [], "ability": "", "item": "", "nature": "", "spread": ""})
                    st.session_state.used_pkmn.add(p['name']); st.session_state.options = []
                    if len(st.session_state.team) == 6: st.session_state.step = "MOVES"
                    st.rerun()

    elif st.session_state.step == "MOVES":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Mosse per {p['name']} ({len(p['moves'])+1}/4)")
        if not st.session_state.options: st.session_state.options = random.sample(list(moves_db.keys()), 4)
        for m in st.session_state.options:
            info = moves_db.get(m, {"type": "Normal", "bp": 0, "cat": "Stato"})
            st.markdown(f"""
            <div class="move-card">
                <strong>{m}</strong> | <span class="type-badge" style="background:{TYPE_COLORS.get(info['type'], '#666')}">{info['type']}</span> 
                <span class="cat-badge">{info['cat']}</span> | BP: {info['bp'] if info['bp'] > 0 else '--'}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Scegli {m}", key=f"mv_{m}"):
                p['moves'].append(m); st.session_state.options = []
                if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                st.rerun()

    elif st.session_state.step == "ABILITY":
        if not st.session_state.options: st.session_state.options = random.sample(ABILITIES_DB, 4)
        st.header("Scegli l'Abilità")
        for a in st.session_state.options:
            if st.button(a): 
                st.session_state.team[st.session_state.current_pkmn_idx]['ability'] = a
                st.session_state.options = []; st.session_state.step = "ITEM"; st.rerun()

    elif st.session_state.step == "ITEM":
        if not st.session_state.options: st.session_state.options = random.sample(ITEMS_DB, 4)
        st.header("Scegli lo Strumento")
        for i in st.session_state.options:
            if st.button(i): 
                st.session_state.team[st.session_state.current_pkmn_idx]['item'] = i
                st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

    elif st.session_state.step == "NATURE":
        if not st.session_state.options: st.session_state.options = random.sample(list(NATURES_DB.keys()), 4)
        st.header("Scegli la Natura")
        for n in st.session_state.options:
            if st.button(f"{n} ({NATURES_DB[n]})"): 
                st.session_state.team[st.session_state.current_pkmn_idx]['nature'] = n
                st.session_state.options = []; st.session_state.step = "SPREAD"; st.rerun()

    elif st.session_state.step == "SPREAD":
        if not st.session_state.options: st.session_state.options = [gen_chaos_spread() for _ in range(4)]
        st.header("Scegli lo Spread EV")
        for s in st.session_state.options:
            if st.button(s):
                st.session_state.team[st.session_state.current_pkmn_idx]['spread'] = s
                st.session_state.options = []
                if st.session_state.current_pkmn_idx < 5:
                    st.session_state.current_pkmn_idx += 1; st.session_state.step = "MOVES"
                else: st.session_state.step = "FINISHED"
                st.rerun()

    elif st.session_state.step == "FINISHED":
        st.success("Draft Completato!")
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("🔄 RESET"): st.session_state.clear(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)