import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- LOGICA SPRITE DEFINITIVA ---
def get_sprite(name):
    n = name.lower()
    if any(reg in n for reg in ["hisui", "galar", "alola", "paldea", "therian", "mega", "primal"]):
        img_name = n.replace(" ", "") 
    else:
        img_name = n.replace(" ", "").replace("-", "").replace("'", "")
    return f"https://play.pokemonshowdown.com/sprites/ani/{img_name}.gif"

# --- CARICAMENTO ASSET E FILTRI RIGOROSI ---
@st.cache_data
def load_assets():
    pk_pool = []; mv_db = {}
    # LISTA UBER DA BANNARE
    pk_banned = ["ZACIAN", "ZAMAZENTA", "ETERNATUS", "MEWTWO", "RAYQUAZA", "KYOGRE", "GROUDON", "ARCEUS", "DIALGA", "PALKIA", "GIRATINA", "XERNEAS", "YVELTAL", "SOLGALEO", "LUNALA", "CALYREX", "KORAIDON", "MIRAIDON", "DEOXYS", "DARKRAI", "HO-OH", "LUGIA", "RESHIRAM", "ZEKROM", "KYUREM", "COSMOG", "COSMOEM", "NECROZMA", "MAGEARNA", "MARSHADOW", "ZERAORA", "MELTAN", "MELMETAL", "ZARUDE", "REGIELEKI", "REGIDRAGO", "GLASTRIER", "SPECTRIER", "ENAMORUS"]
    
    # BLACKLIST MOSSE TRASH (No Hidden Power)
    mv_trash = [
        "happyhour", "celebrate", "holdhands", "growl", "tailwhip", "leer", 
        "confide", "camouflage", "bide", "refresh", "splash", "soak", 
        "mudsport", "watersport", "snore", "present", "struggle", "darkvoid", 
        "pound", "confusion", "powdersnow", "tackle", "constrict", "flash", 
        "howl", "sandattack", "smokescreen", "kinesis", "stringshot", 
        "sharpen", "meditate", "harden", "withdraw", "defensecurl", "barrier", 
        "minimize", "doubleteam", "focusenergy", "defendorder", "hypnosis"
    ]

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Pokémon con FILTRO UBER ATTIVO
        with open(os.path.join(current_dir, "data", "pokemon_clean.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data.items() if isinstance(data, dict) else enumerate(data)
            for _, val in items:
                nm = val.get('name') if isinstance(val, dict) else str(val)
                # IL FIX: Controllo che il nome non sia nella lista ban e non sia GMAX
                if nm and "GMAX" not in nm.upper() and not any(b == nm.upper() for b in pk_banned):
                    pk_pool.append({'name': nm})

        # Moves Database con FILTRO POTENZA E TRASH
        with open(os.path.join(current_dir, "data", "moves.json"), "r", encoding="utf-8") as f:
            mv_data = json.load(f)
            for nm, m in mv_data.items():
                if not isinstance(m, dict): continue
                clean_m = nm.lower().replace(" ", "").replace("-", "")
                bp = m.get("basePower", 0)
                
                if any(x in nm.upper() for x in ["G-MAX", "GMAX", " Z-", "MAX "]): continue
                # Salva Hidden Power dal filtro 55 BP
                if (0 < bp < 55 and clean_m != "hiddenpower") or clean_m in mv_trash or bp > 165: continue
                
                mv_db[nm] = {
                    "type": m.get("type", "Normal"), "bp": bp, 
                    "cat": m.get("category", "Status")
                }
    except Exception as e: st.error(f"Errore: {e}")
    return pk_pool, mv_db

pk_pool, moves_db = load_assets()

# --- DATABASE COSTANTI ---
ABILITIES = ["Huge Power", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Unaware", "Magic Guard", "Prankster", "Libero", "Protean"]
ITEMS = ["Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Air Balloon", "Eviolite"]
NATURES = {"Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA", "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA"}

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

# --- INTERFACCIA ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")

col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.subheader("🏟️ IL TUO TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**"):
            if p['ability']: st.write(f"🌟 **{p['ability']}** @ {p['item']}")
            if p['nature']: st.caption(f"Natura: {p['nature']} | EVs: {p['spread']}")
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
        st.header(f"Mossa {len(p['moves'])+1}/4 per {p['name']}")
        if not st.session_state.options:
            pool = [m for m in moves_db.keys() if m not in p['moves']]
            atk_pool = [m for m in pool if moves_db[m]['bp'] > 0]
            mandatory = random.choice(atk_pool)
            others = random.sample([m for m in pool if m != mandatory], 3)
            st.session_state.options = [mandatory] + others
            random.shuffle(st.session_state.options)
        for m in st.session_state.options:
            info = moves_db[m]
            if st.button(f"{m} ({info['type']} | BP: {info['bp'] if info['bp']>0 else '--'})", key=f"mv_{m}"):
                p['moves'].append(m); st.session_state.options = []
                if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                st.rerun()

    elif st.session_state.step == "ABILITY":
        if not st.session_state.options: st.session_state.options = random.sample(ABILITIES, 4)
        st.header(f"Abilità per {st.session_state.team[st.session_state.current_pkmn_idx]['name']}")
        for a in st.session_state.options:
            if st.button(a, key=f"ab_{a}"):
                st.session_state.team[st.session_state.current_pkmn_idx]['ability'] = a
                st.session_state.options = []; st.session_state.step = "ITEM"; st.rerun()

    elif st.session_state.step == "ITEM":
        if not st.session_state.options: st.session_state.options = random.sample(ITEMS, 4)
        st.header("Strumento")
        for i in st.session_state.options:
            if st.button(i, key=f"it_{i}"):
                st.session_state.team[st.session_state.current_pkmn_idx]['item'] = i
                st.session_state.options = []; st.session_state.step = "NATURE"; st.rerun()

    elif st.session_state.step == "NATURE":
        if not st.session_state.options: st.session_state.options = random.sample(list(NATURES.keys()), 4)
        st.header("Natura")
        for n in st.session_state.options:
            if st.button(f"{n} ({NATURES[n]})", key=f"na_{n}"):
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