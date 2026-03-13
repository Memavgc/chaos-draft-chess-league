import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")


TYPE_COLORS = {"Normal": "#A8A77A", "Fire": "#EE8130", "Water": "#6390F0", "Electric": "#F7D02C", "Grass": "#7AC74C", "Ice": "#96D9D2", "Fighting": "#C22E28", "Poison": "#A33EA1", "Ground": "#E2BF65", "Flying": "#A98FF3", "Psychic": "#F95587", "Bug": "#A6B91A", "Rock": "#B6A136", "Ghost": "#735797", "Dragon": "#6F35FC", "Steel": "#B7B7CE", "Fairy": "#D685AD", "Dark": "#705848"}

def get_sprite(name):
    # 1. Pulizia totale per nomi come "Ting-Lu" o "Iron Jugulis"
    # Diventano "tinglu" e "ironjugulis"
    n = name.lower().replace(" ", "").replace("-", "").replace("'", "")
    
    # 2. Gestione Forme e Mega
    # Showdown usa spesso nomi piatti. Se il nome contiene "mega", 
    # cerchiamo di puntare allo sprite animato corretto.
    if "mega" in n:
        # Esempio: "glimmoramega" -> "glimmora-mega" (alcuni sprite vogliono il trattino)
        # Ma la maggior parte usa il nome piatto. 
        return f"https://play.pokemonshowdown.com/sprites/ani/{n}.gif"
        
    return f"https://play.pokemonshowdown.com/sprites/ani/{n}.gif"
@st.cache_data
def load_assets():
    pk_pool = []; mv_pool = {}
    pk_banned = ["ZACIAN", "ZAMAZENTA", "ETERNATUS", "MEWTWO", "RAYQUAZA", "KYOGRE", "GROUDON", "ARCEUS", "DIALGA", "PALKIA", "GIRATINA", "XERNEAS", "YVELTAL", "SOLGALEO", "LUNALA", "CALYREX", "KORAIDON", "MIRAIDON", "DEOXYS", "DARKRAI"]
    
    # Pulizia totale mosse inutili
    mv_manual_ban = ["constrict", "bide", "refresh", "splash", "soak", "mudsport", "watersport", "snore", "present", "struggle", "darkvoid", "pound", "confusion", "powdersnow"]

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Pokemon
        with open(os.path.join(current_dir, "data", "pokemon_clean.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data.items() if isinstance(data, dict) else enumerate(data)
            for key, val in items:
                nm = val.get('name') if isinstance(val, dict) else str(val)
                if nm and "GMAX" not in nm.upper() and not any(b in nm.upper() for b in pk_banned):
                    pk_pool.append({'name': nm})

        # Mosse
        with open(os.path.join(current_dir, "data", "moves.json"), "r", encoding="utf-8") as f:
            mv_data = json.load(f)
            for nm, m in mv_data.items():
                if not isinstance(m, dict): continue
                nm_up = nm.upper()
                clean_m = nm.lower().replace(" ", "").replace("-", "")
                bp = m.get("basePower", 0)
                cat = m.get("category") or m.get("Category") or "Status"

                # Filtro Z, G-Max, BP basso (<50) e Nomi Lunghi
                if any(x in nm_up for x in ["G-MAX", "GMAX", " Z-", "MAX ", "SMASH", "STARFALL", "SUNRAZE"]): continue
                if bp > 160 or (0 < bp < 50) or clean_m in mv_manual_ban: continue

                mv_pool[nm] = {
                    "type": m.get("type", "Normal"), 
                    "bp": bp, 
                    "cat": cat.replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato")
                }
    except Exception as e: st.error(f"Errore caricamento asset: {e}")
    return pk_pool, mv_pool

pkmn_pool, moves_db = load_assets()

# --- DATABASE FISSI ---
NATURES_DB = {"Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA", "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA", "Naive": "+Spe, -SpD", "Hasty": "+Spe, -Def"}
ITEMS_DB = ["Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", "Leftovers", "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Eviolite", "Air Balloon", "Lum Berry", "Clear Amulet", "Mirror Herb", "Loaded Dice", "Covert Cloak"]
ABILITIES_DB = ["Huge Power", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", "Adaptability", "Sheer Force", "Sharpness", "Supreme Overlord", "Good as Gold", "Unaware", "Magic Guard", "Prankster"]

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

if 'team' not in st.session_state:
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set()})

# --- UI ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")

col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.subheader("🏟️ TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**"):
            st.caption(f"**{p['ability']}** @ {p['item']}")
            if p['moves']: st.caption(f"Mosse: {', '.join(p['moves'])}")
            if p['spread']: st.caption(f"EVs: {p['spread']}")

with col_main:
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
        st.header(f"Mossa {len(p['moves'])+1}/4 per {p['name']}")
        
        if not st.session_state.options:
            # 1. Filtro unicità: togli mosse già nel set
            available_keys = [m for m in moves_db.keys() if m not in p['moves']]
            
            # 2. Suddividi in Offensive e Stato
            atk_pool = [m for m in available_keys if moves_db[m]['bp'] > 0]
            status_pool = [m for m in available_keys if moves_db[m]['bp'] == 0]
            
            # 3. GARANZIA: 1 d'attacco sicura + 3 random tra il resto
            mandatory_atk = random.choice(atk_pool)
            remaining_keys = [m for m in available_keys if m != mandatory_atk]
            others = random.sample(remaining_keys, 3)
            
            final_selection = [mandatory_atk] + others
            random.shuffle(final_selection) # Mischia l'ordine così l'attacco non è sempre il primo
            st.session_state.options = final_selection
            
        for m in st.session_state.options:
            info = moves_db.get(m, {"type": "Normal", "bp": 0, "cat": "Stato"})
            st.markdown(f"""<div style="margin-bottom: 10px; padding: 10px; border-radius: 5px; background: rgba(255,255,255,0.1); border-left: 4px solid #f1c40f;">
                <strong>{m}</strong> | <span class="type-badge" style="background:{TYPE_COLORS.get(info['type'], '#666')}">{info['type']}</span> 
                <span class="cat-badge">{info['cat']}</span> | BP: {info['bp'] if info['bp'] > 0 else '--'}</div>""", unsafe_allow_html=True)
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
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        p['spread'] = gen_chaos_spread()
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