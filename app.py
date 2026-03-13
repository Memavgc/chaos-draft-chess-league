import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- CSS PER COLORI MOSSE E BADGE (Senza Background) ---
st.markdown("""
<style>
    .type-badge {
        padding: 5px 12px; border-radius: 8px; color: white; font-weight: bold;
        text-shadow: 1px 1px 2px black; display: inline-block; margin-right: 10px;
        font-size: 0.8em; text-transform: uppercase;
    }
    .cat-badge {
        padding: 5px 10px; border-radius: 8px; color: white; font-weight: bold;
        background-color: #444; font-size: 0.8em; display: inline-block;
    }
    /* Colori Tipi Showdown */
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

# --- LOGICA SPRITE (Fix Alphanumeric) ---
def get_sprite(name):
    clean_name = "".join(filter(str.isalnum, name.lower()))
    if "hisui" in clean_name: clean_name = clean_name.replace("hisui", "-hisui")
    elif "galar" in clean_name: clean_name = clean_name.replace("galar", "-galar")
    elif "alola" in clean_name: clean_name = clean_name.replace("alola", "-alola")
    elif "paldea" in clean_name: clean_name = clean_name.replace("paldea", "-paldea")
    return f"https://play.pokemonshowdown.com/sprites/ani/{clean_name}.gif"

# --- CARICAMENTO ASSET E FILTRI ---
@st.cache_data
def load_assets():
    pk_pool = []; mv_db = {}
    pk_banned = ["ZACIAN", "ZAMAZENTA", "ETERNATUS", "MEWTWO", "RAYQUAZA", "KYOGRE", "GROUDON", "ARCEUS", "DIALGA", "PALKIA", "GIRATINA", "XERNEAS", "YVELTAL", "SOLGALEO", "LUNALA", "CALYREX", "KORAIDON", "MIRAIDON", "DEOXYS", "DARKRAI", "CHI-YU", "CHIEN-PAO", "MAGEARNA", "FLUTTER MANE", "PALAFIN", "IRON BUNDLE"]
    
    mv_trash = ["happyhour", "celebrate", "holdhands", "growl", "tailwhip", "leer", "confide", "camouflage", "bide", "refresh", "splash", "soak", "mudsport", "watersport", "snore", "present", "struggle", "darkvoid", "pound", "confusion", "powdersnow", "tackle", "constrict", "flash", "howl", "sandattack", "smokescreen", "kinesis", "stringshot", "sharpen", "meditate", "harden", "withdraw", "defensecurl", "barrier", "minimize", "doubleteam", "focusenergy", "defendorder", "hypnosis", "transform", "featherdance"]

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, "data", "pokemon_clean.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data.items() if isinstance(data, dict) else enumerate(data)
            for _, val in items:
                nm = val.get('name') if isinstance(val, dict) else str(val)
                if nm and "GMAX" not in nm.upper() and not any(b == nm.upper() for b in pk_banned):
                    pk_pool.append({'name': nm})

        with open(os.path.join(current_dir, "data", "moves.json"), "r", encoding="utf-8") as f:
            mv_data = json.load(f)
            for nm, m in mv_data.items():
                if not isinstance(m, dict): continue
                clean_m = nm.lower().replace(" ", "").replace("-", "")
                bp = m.get("basePower", 0)
                if any(x in nm.upper() for x in ["G-MAX", "GMAX", " Z-", "MAX "]): continue
                if (0 < bp < 55 and clean_m != "hiddenpower") or clean_m in mv_trash or bp > 165: continue
                
                mv_db[nm] = {
                    "type": m.get("type", "Normal"), 
                    "bp": bp, 
                    "cat": m.get("category", "Status"),
                    "desc": m.get("shortDesc", "Nessuna descrizione.")
                }
    except Exception as e: st.error(f"Errore: {e}")
    return pk_pool, mv_db

pk_pool, moves_db = load_assets()

# --- DATABASE COSTANTI ---
ABILITIES = ["Huge Power", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Unaware", "Magic Guard", "Prankster"]
ITEMS = ["Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt"]
NATURES = {"Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA", "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk"}

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

# --- STATO SESSIONE ---
if 'team' not in st.session_state:
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set()})

# --- UI ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")

col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.subheader("🏟️ IL TUO TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**"):
            if p['ability']: st.write(f"🌟 **{p['ability']}** @ {p['item']}")
            if p['moves']: st.caption(f"Mosse: {', '.join(p['moves'])}")

with col_main:
    if st.session_state.step == "DRAFT_PKMN":
        available = [p for p in pk_pool if p['name'] not in st.session_state.used_pkmn]
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
        if not st.session_state.options:
            pool = [m for m in moves_db.keys() if m not in p['moves']]
            atk_pool = [m for m in pool if moves_db[m]['bp'] > 0]
            mandatory = random.choice(atk_pool)
            others = random.sample([m for m in pool if m != mandatory], 3)
            st.session_state.options = [mandatory] + others
            random.shuffle(st.session_state.options)

        for m in st.session_state.options:
            info = moves_db[m]
            t_low = info['type'].lower()
            st.markdown(f"""
            <div style="border-left: 5px solid #f1c40f; padding: 10px; margin-bottom: 5px; background: rgba(255,255,255,0.05);">
                <span class="type-badge {t_low}">{info['type']}</span>
                <span class="cat-badge">{info['cat']}</span>
                <b style="font-size: 1.1em; margin-left: 10px;">{m}</b> | BP: {info['bp'] if info['bp']>0 else '--'}
                <p style="font-size: 0.9em; color: #bbb; margin: 5px 0;">{info['desc']}</p>
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
                st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

    elif st.session_state.step == "NATURE":
        if not st.session_state.options: st.session_state.options = random.sample(list(NATURES.keys()), 4)
        st.header("Natura")
        for n in st.session_state.options:
            if st.button(f"{n} ({NATURES[n]})"):
                curr = st.session_state.team[st.session_state.current_pkmn_idx]
                curr['nature'] = n; curr['spread'] = gen_chaos_spread(); st.session_state.options = []
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