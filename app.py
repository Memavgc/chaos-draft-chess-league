import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- CSS PER COLORI, CATEGORIE E CENTRATURA TOTALE ---
st.markdown("""
<style>
    .type-badge {
        padding: 5px 12px; border-radius: 8px; color: white; font-weight: bold;
        text-shadow: 1px 1px 2px black; display: inline-block; margin-right: 10px;
        font-size: 0.8em; text-transform: uppercase;
    }
    .cat-badge {
        padding: 5px 10px; border-radius: 8px; color: white; font-weight: bold;
        font-size: 0.8em; display: inline-block; margin-right: 5px;
    }
    .phys { background-color: #C22E28; }
    .spec { background-color: #6390F0; }
    .stat { background-color: #705746; }
    
    /* Forza la centratura di ogni elemento dentro le colonne dei Pokémon */
    [data-testid="stVerticalBlock"] > div {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .normal { background-color: #A8A77A; } .fire { background-color: #EE8130; }
    .water { background-color: #6390F0; } .electric { background-color: #F7D02C; }
    .grass { background-color: #7AC74C; } .ice { background-color: #96D9D6; }
    .fighting { background-color: #C22E28; } .poison { background-color: #A33EA1; }
    .ground { background-color: #E2BF65; } .flying { background-color: #A98FF3; }
    .psychic { background-color: #F95587; } .bug { background-color: #A6B91A; }
    .rock { background-color: #B6A136; } .ghost { background-color: #735797; }
    .dragon { background-color: #6F35FC; } .dark { background-color: #705746; }
    .steel { background-color: #B7B7CE; } .fairy { background-color: #D685AD; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE SPRITE FIXATA (LOGICA E CENTRATURA) ---
def display_sprite(name):
    n = name.lower()
    
    # 1. Pulizia aggressiva per gli URL di Showdown
    # Esempio: "Magearna-Original" -> "magearnaoriginal"
    clean_name = n.replace("-", "").replace(" ", "").replace("'", "")
    
    # Gestione specifica Mega
    if "mega" in n:
        base_part = n.replace("mega", "").strip("- ")
        clean_base = base_part.replace("-", "").replace(" ", "")
        url_attempt = f"https://play.pokemonshowdown.com/sprites/ani/{clean_base}-mega.gif"
    else:
        url_attempt = f"https://play.pokemonshowdown.com/sprites/ani/{clean_name}.gif"
    
    # Fallback alla forma base (es. Rotom-Fan -> rotom)
    base_name_only = n.split("-")[0].replace("mega", "").strip().replace(" ", "")
    url_fallback = f"https://play.pokemonshowdown.com/sprites/ani/{base_name_only}.gif"
    
    # HTML con box flessibile centrato
    st.markdown(f"""
        <div style="width: 100%; display: flex; justify-content: center; align-items: center; min-height: 160px; margin-bottom: 10px;">
            <img src="{url_attempt}" 
                 onerror="this.onerror=null; this.src='{url_fallback}';" 
                 style="max-height: 150px; width: auto; display: block; margin: 0 auto;">
        </div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_assets():
    pk_pool = []; mv_db = {}
    # BAN UBER (Paradox OK)
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
                clean_m = nm.lower().replace(" ", "").replace("-", "")
                bp = m.get("basePower", 0)
                
                # NO MOSSE Z, NO G-MAX
                if any(x in nm.upper() for x in ["G-MAX", "GMAX", " Z-", "MAX "]) or m.get("isZ") or clean_m in mv_trash:
                    continue
                if 0 < bp < 55 and clean_m != "hiddenpower":
                    continue
                
                cat = m.get("category", "Status")
                mv_db[nm] = {
                    "type": m.get("type", "Normal"), 
                    "bp": bp, 
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

st.title("♟️ CHAOS DRAFT CHESS LEAGUE")
col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.subheader("🏟️ RECAP TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**", expanded=True):
            if p['ability']: st.write(f"🌟 **{p['ability']}** @ {p['item']}")
            if p['moves']:
                st.markdown("  \n".join([f"🔹 {m}" for m in p['moves']]))
            if p['spread']: st.caption(f"EVs: {p['spread']} ({p.get('nature', '')})")

with col_main:
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
            st.markdown(f"""
            <div style="padding:10px; border-bottom:1px solid #333;">
                <span class="type-badge {info['type'].lower()}">{info['type']}</span>
                <span class="cat-badge {info['cat_class']}">{info['cat_label']}</span>
                <b style="font-size:1.1em;">{m}</b> (BP: {info['bp'] if info['bp']>0 else '--'})
                <p style="font-size:0.85em; color:#aaa; margin:5px 0;">{info['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Scegli {m}", key=f"mv_{m}"):
                p['moves'].append(m); st.session_state.options = []
                if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                st.rerun()

    elif st.session_state.step == "ABILITY":
        if not st.session_state.options: st.session_state.options = random.sample(ABILITIES, 4)
        st.header(f"Abilità per {st.session_state.team[st.session_state.current_pkmn_idx]['name']}")
        for a in st.session_state.options:
            if st.button(a):
                st.session_state.team[st.session_state.current_pkmn_idx]['ability'] = a
                st.session_state.options = []; st.session_state.step = "ITEM"; st.rerun()

    elif st.session_state.step == "ITEM":
        if not st.session_state.options: st.session_state.options = random.sample(ITEMS, 4)
        st.header("Strumento")
        for i in st.session_state.options:
            if st.button(i):
                st.session_state.team[st.session_state.current_pkmn_idx]['item'] = i
                st.session_state.options = []; st.session_state.step = "SPREAD"; st.rerun()

    elif st.session_state.step == "SPREAD":
        if not st.session_state.options: st.session_state.options = [gen_chaos_spread() for _ in range(4)]
        st.header("Scegli la Spread di EV")
        for s in st.session_state.options:
            if st.button(s):
                st.session_state.team[st.session_state.current_pkmn_idx]['spread'] = s
                st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

    elif st.session_state.step == "NATURE":
        if not st.session_state.options: st.session_state.options = random.sample(list(NATURES.keys()), 4)
        st.header("Natura")
        for n in st.session_state.options:
            if st.button(f"{n} ({NATURES[n]})"):
                st.session_state.team[st.session_state.current_pkmn_idx]['nature'] = n
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