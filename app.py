import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- 1. CSS: RISOLVE IL DECENTRAMENTO ---
st.markdown("""
<style>
    /* Centra tutto il contenuto delle colonne verticali */
    [data-testid="stVerticalBlock"] { align-items: center; text-align: center; }
    
    /* Centra i bottoni e imposta larghezza massima */
    .stButton > button { width: 100%; max-width: 280px; margin: 0 auto; display: block; }
    
    /* Badge Mosse e Tipi */
    .type-badge { padding: 4px 10px; border-radius: 6px; color: white; font-weight: bold; font-size: 0.75em; text-transform: uppercase; margin-right: 5px; }
    .cat-badge { padding: 4px 8px; border-radius: 6px; color: white; font-weight: bold; font-size: 0.75em; display: inline-block; margin-right: 10px; }
    .phys { background-color: #C22E28; } .spec { background-color: #6390F0; } .stat { background-color: #705746; }
    .normal { background-color: #A8A77A; } .fire { background-color: #EE8130; } .water { background-color: #6390F0; }
    .electric { background-color: #F7D02C; } .grass { background-color: #7AC74C; } .ice { background-color: #96D9D6; }
    .fighting { background-color: #C22E28; } .poison { background-color: #A33EA1; } .ground { background-color: #E2BF65; }
    .flying { background-color: #A98FF3; } .psychic { background-color: #F95587; } .bug { background-color: #A6B91A; }
    .rock { background-color: #B6A136; } .ghost { background-color: #735797; } .dragon { background-color: #6F35FC; }
    .dark { background-color: #705746; } .steel { background-color: #B7B7CE; } .fairy { background-color: #D685AD; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGICA SPRITE: FIX IMMAGINI ROTTE ---
def display_sprite(name):
    n = name.lower().strip()
    # Pulisce i nomi per Showdown (es. "Ogerpon-Teal" -> "ogerponteal")
    clean_name = n.replace("-", "").replace(" ", "").replace("'", "")
    
    if "mega" in n:
        base = n.split("-")[0].replace("mega", "").strip()
        url_attempt = f"https://play.pokemonshowdown.com/sprites/ani/{base}-mega.gif"
    else:
        url_attempt = f"https://play.pokemonshowdown.com/sprites/ani/{clean_name}.gif"
    
    # Fallback alla forma base (es. "Rotom-Fan" -> "rotom")
    base_only = n.split("-")[0].strip()
    url_fallback = f"https://play.pokemonshowdown.com/sprites/ani/{base_only}.gif"
    
    st.markdown(f"""
        <div style="height:170px; display:flex; justify-content:center; align-items:center; width:100%;">
            <img src="{url_attempt}" onerror="this.onerror=null; this.src='{url_fallback}';" style="max-height:150px; object-fit:contain;">
        </div>
    """, unsafe_allow_html=True)

# --- 3. CARICAMENTO ASSETS: NO MOSSE Z / PARADOX OK ---
@st.cache_data
def load_assets():
    pk_pool = []; mv_db = {}
    # BAN UBER (I Paradox come Flutter Mane sono ammessi)
    pk_banned = ["ZACIAN", "ZAMAZENTA", "ETERNATUS", "MEWTWO", "RAYQUAZA", "KYOGRE", "GROUDON", "ARCEUS", "DIALGA", "PALKIA", "GIRATINA", "XERNEAS", "YVELTAL", "SOLGALEO", "LUNALA", "CALYREX", "KORAIDON", "MIRAIDON", "DEOXYS", "DARKRAI", "TERAPAGOS", "MAGEARNA", "CHI-YU", "CHIEN-PAO", "TING-LU", "WO-CHIEN"]
    mv_trash = ["happyhour", "celebrate", "growl", "tailwhip", "leer", "splash", "confide", "camouflage", "bide", "refresh", "soak", "mudsport", "watersport", "snore", "present", "struggle"]

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "data", "pokemon_clean.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            for _, val in (data.items() if isinstance(data, dict) else enumerate(data)):
                nm = val.get('name') if isinstance(val, dict) else str(val)
                if nm and "GMAX" not in nm.upper() and not any(b == nm.upper() for b in pk_banned):
                    pk_pool.append({'name': nm})

        with open(os.path.join(current_dir, "data", "moves.json"), "r", encoding="utf-8") as f:
            mv_data = json.load(f)
            for nm, m in mv_data.items():
                if not isinstance(m, dict): continue
                # RIMRIMOZIONE MOSSE Z E G-MAX
                if any(x in nm.upper() for x in ["G-MAX", "GMAX", " Z-", "MAX ", " Z "]) or m.get("isZ"): continue
                
                bp = m.get("basePower", 0)
                cat = m.get("category", "Status")
                mv_db[nm] = {
                    "type": m.get("type", "Normal"), "bp": bp,
                    "cat_class": "phys" if cat == "Physical" else "spec" if cat == "Special" else "stat",
                    "cat_label": "FISICA ⚔️" if cat == "Physical" else "SPECIALE 🔮" if cat == "Special" else "STATO 🛡️",
                    "desc": m.get("shortDesc", "")
                }
    except Exception as e: st.error(f"Errore caricamento: {e}")
    return pk_pool, mv_db

pk_pool, moves_db = load_assets()
ABILITIES = ["Huge Power", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Unaware", "Magic Guard", "Prankster"]
ITEMS = ["Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt"]
NATURES = {"Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA", "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk"}

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]; evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

if 'team' not in st.session_state: 
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set()})

# --- 4. LAYOUT PRINCIPALE ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")
col_main, col_side = st.columns([2.5, 1.5])

# RECAP LATERALE: INCLUDE LE MOSSE PICKATE
with col_side:
    st.subheader("🏟️ RECAP TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**", expanded=True):
            if p['ability']: st.write(f"🌟 **{p['ability']}** @ {p['item']}")
            if p['moves']: st.markdown("  \n".join([f"🔹 {m}" for m in p['moves']]))
            if p['spread']: st.caption(f"EVs: {p['spread']} ({p.get('nature', '')})")

with col_main:
    # STEP 1: DRAFT POKEMON
    if st.session_state.step == "DRAFT_PKMN":
        available = [p for p in pk_pool if p['name'] not in st.session_state.used_pkmn]
        if not st.session_state.options: st.session_state.options = random.sample(available, 3)
        cols = st.columns(3)
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                display_sprite(p['name'])
                if st.button(f"SCEGLI {p['name']}", key=f"pk_{i}"):
                    st.session_state.team.append({"name": p['name'], "moves": [], "ability": "", "item": "", "nature": "", "spread": ""})
                    st.session_state.used_pkmn.add(p['name']); st.session_state.options = []
                    if len(st.session_state.team) == 6: st.session_state.step = "MOVES"
                    st.rerun()

    # STEP 2: DRAFT MOSSE
    elif st.session_state.step == "MOVES":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Mosse per {p['name']} ({len(p['moves'])+1}/4)")
        if not st.session_state.options:
            pool = list(moves_db.keys())
            atk = random.choice([m for m in pool if moves_db[m]['bp'] > 0])
            st.session_state.options = [atk] + random.sample(pool, 3)
            random.shuffle(st.session_state.options)
        
        for m in st.session_state.options:
            info = moves_db[m]
            c1, c2 = st.columns([1, 2.5])
            with c1:
                if st.button(f"Scegli {m}", key=f"mv_{m}"):
                    p['moves'].append(m); st.session_state.options = []
                    if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                    st.rerun()
            with c2:
                st.markdown(f"""<div style="text-align: left; padding: 5px; border-left: 3px solid #444;">
                    <span class="type-badge {info['type'].lower()}">{info['type']}</span>
                    <span class="cat-badge {info['cat_class']}">{info['cat_label']}</span>
                    <b>BP: {info['bp'] if info['bp']>0 else '--'}</b><br><small>{info['desc']}</small></div>""", unsafe_allow_html=True)

    # STEP 3-6: LOGICA OTTIMIZZATA (Abilità, Item, Spread, Natura)
    elif st.session_state.step in ["ABILITY", "ITEM", "SPREAD", "NATURE"]:
        step = st.session_state.step
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"{step} per {p['name']}")
        
        if not st.session_state.options:
            if step == "ABILITY": st.session_state.options = random.sample(ABILITIES, 4)
            elif step == "ITEM": st.session_state.options = random.sample(ITEMS, 4)
            elif step == "SPREAD": st.session_state.options = [gen_chaos_spread() for _ in range(4)]
            elif step == "NATURE": st.session_state.options = random.sample(list(NATURES.keys()), 4)

        for opt in st.session_state.options:
            label = f"{opt} ({NATURES[opt]})" if step == "NATURE" else opt
            if st.button(label):
                if step == "ABILITY": p['ability'] = opt; next_s = "ITEM"
                elif step == "ITEM": p['item'] = opt; next_s = "SPREAD"
                elif step == "SPREAD": p['spread'] = opt; next_s = "NATURE"
                elif step == "NATURE":
                    p['nature'] = opt
                    if st.session_state.current_pkmn_idx < 5:
                        st.session_state.current_pkmn_idx += 1; next_s = "MOVES"
                    else: next_s = "FINISHED"
                st.session_state.options = []; st.session_state.step = next_s; st.rerun()

    elif st.session_state.step == "FINISHED":
        st.success("Draft Completato!")
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("🔄 RESET"): st.session_state.clear(); st.rerun()