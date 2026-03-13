import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- CSS ULTR-AGGRESSIVO: CENTRATURA E STILE (Senza Background) ---
st.markdown("""
<style>
    /* Centra tutti i blocchi verticali (colonne) */
    [data-testid="stVerticalBlock"] > div {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        text-align: center;
    }
    
    /* Forza la centratura totale dei bottoni e larghezza massima */
    .stButton > button {
        width: 100% !important;
        max-width: 280px !important;
        margin: 10px auto !important;
        display: block !important;
    }
    
    /* Centratura per i blocchi di scelta mosse/spread */
    .choice-block {
        display: block;
        width: 100%;
        max-width: 450px;
        margin: 0 auto 10px auto;
        text-align: left;
    }

    /* Badge Mosse e Tipi */
    .type-badge { padding: 4px 10px; border-radius: 6px; color: white; font-weight: bold; text-shadow: 1px 1px 2px black; display: inline-block; margin-right: 5px; font-size: 0.75em; text-transform: uppercase; }
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

# --- NUOVA LOGICA SPRITE: FIX MEGAE TRATTINI ---
def display_sprite(name):
    # Trasforma "Gyarados-Mega" -> "gyaradosmega"
    n = name.lower().strip()
    clean_all = n.replace("-", "").replace(" ", "")
    
    # 1. URL pulito totale (per Chi-Yu, Magearna, Weezing, Mega ufficiali)
    url_ani = f"https://play.pokemonshowdown.com/sprites/ani/{clean_all}.gif"
    
    # 2. URL con trattini (per forme regionali non standard o non pulite nel db Showdown)
    url_hybrid = f"https://play.pokemonshowdown.com/sprites/ani/{n}.gif"
    
    # 3. Fallback alla forma base assoluta (nome prima del primo trattino, es. tatsugiri)
    base_name = "".join(filter(str.isalnum, n.split("-")[0].replace("mega", "").strip().replace(" ", "")))
    url_fallback = f"https://play.pokemonshowdown.com/sprites/ani/{base_name}.gif"
    
    st.markdown(f"""
        <div style="height:170px; display:flex; justify-content:center; align-items:center; width:100%;">
            <img src="{url_ani}" 
                 onerror="this.onerror=null; this.src='{url_hybrid}'; this.onerror=function(){{this.onerror=null; this.src='{url_fallback}';}};" 
                 style="max-height:150px; object-fit:contain;">
        </div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_assets():
    pk_pool = []; mv_db = {}
    # BAN SOLO UBER (Paradox OK, Chi-Yu bannato per sicurezza)
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
                
                # PULIZIA TOTALE: NO MOSSE Z, NO GIGAMAX, NO DYNAMAX (Max Geyser, ecc.)
                if any(x in nm.upper() for x in ["G-MAX", "GMAX", " Z-", "MAX "]) or m.get("isZ") or m.get("isMax") or clean_m in mv_trash:
                    continue
                if 0 < m.get("basePower", 0) < 55 and clean_m != "hiddenpower": # BP basso OK solo per Hidden Power
                    continue
                
                cat = m.get("category", "Status")
                mv_db[nm] = {
                    "type": m.get("type", "Normal"), 
                    "bp": m.get("basePower", 0), 
                    "cat_class": "phys" if cat == "Physical" else "spec" if cat == "Special" else "stat",
                    "cat_label": "FISICA ⚔️" if cat == "Physical" else "SPECIALE 🔮" if cat == "Special" else "STATO 🛡️",
                    "desc": m.get("shortDesc", "")
                }
    except Exception as e: st.error(f"Errore caricamento: {e}")
    return pk_pool, mv_db

# --- DATABASE COMPLETI: ABILITÀ, OGGETTI, NATURE ---

ABILITIES = [
    "Huge Power", "Intimidate", "Regenerator", "Levitate", "Technician", "Moxie", "Speed Boost", "Contrary", 
    "Adaptability", "Sheer Force", "Sharpness", "Unaware", "Magic Guard", "Prankster", "Sword of Ruin", 
    "Beads of Ruin", "Orichalcum Pulse", "Hadron Engine", "Libero", "Protean", "Tough Claws", "Serene Grace", 
    "Magic Bounce", "Drizzle", "Drought", "Sand Stream", "Snow Warning", "Multiscale", 
    "Guts", "Quick Draw", "Pure Power", "No Guard", "Compound Eyes", "Simple", "Tinted Lens", "Moody", 
    "Sturdy", "Water Absorb", "Flash Fire", "Volt Absorb", "Sap Sipper", "Motor Drive", "Justified", 
    "Rattled", "Weak Armor", "Cursed Body", "Harvest", "Natural Cure", "Trace", "Download", "Analytic", 
    "Infiltrator", "Mummy", "Aerilate", "Pixilate", "Refrigerate", "Galvanize", "Liquid Voice", "Stakeout", 
    "Water Bubble", "Steelworker", "Berserk", "Slush Rush", "Surge Surfer", "Queenly Majesty", "Dazzling", 
    "Shields Down", "Comatose", "Disguise",  "Fluffy", "Triage", "Soul-Heart", "Beast Boost", 
    "Psychic Surge", "Misty Surge", "Grassy Surge", "Electric Surge", "Neuroforce", "Intrepid Sword", 
    "Dauntless Shield", "Mirror Armor", "Gulp Missile", "Stalwart", "Steam Engine", "Punk Rock", "Ice Scales", 
    "Ice Face",  "Transistor", "Dragon's Maw", "Chilling Neigh", 
     "Anger Shell", "Armor Tail", "Earth Eater", "Good as Gold", "Guard Dog", "Mycelium Might", 
    "Opportunist", "Protosynthesis", "Purifying Salt", "Quark Drive", "Rocky Payload", "Seed Sower", 
    "Supreme Overlord", "Thermal Exchange", "Toxic Debris", "Well-Baked Body", "Wind Power", "Wind Rider", 
    "Zero to Hero", "Defiant", "Competitive", "Inner Focus", "Oblivious", "Own Tempo", "Scrappy"
]

ITEMS = [
    "Life Orb", "Choice Band", "Choice Specs", "Choice Scarf", "Assault Vest", "Focus Sash", "Leftovers", 
    "Heavy-Duty Boots", "Rocky Helmet", "Expert Belt", "Sitrus Berry", "Lum Berry", "White Herb", 
    "Power Herb", "Mental Herb", "Eviolite", "Black Sludge", "Flame Orb", "Toxic Orb", "Air Balloon", 
    "Weakness Policy", "Eject Button", "Red Card", "Scope Lens", "Wide Lens", "Muscle Band", "Wise Glasses", 
    "Magnet", "Mystic Water", "Charcoal", "Miracle Seed", "Never-Melt Ice", "Black Belt", "Sharp Beak", 
    "Silk Scarf", "Dragon Fang", "Black Glasses", "Spell Tag", "Metal Coat", "Light Clay", "Big Root", 
    "Binding Band", "Damp Rock", "Heat Rock", "Smooth Rock", "Icy Rock", "Terrain Extender", "Room Service", 
    "Blunder Policy", "Throat Spray", "Utility Umbrella", "Punching Glove", "Covert Cloak", "Loaded Dice", 
    "Aguav Berry", "Figy Berry", "Iapapa Berry", "Mago Berry", "Wiki Berry", "Liechi Berry", "Ganlon Berry", 
    "Salac Berry", "Petaya Berry", "Apicot Berry", "Lansat Berry", "Starf Berry", "Enigma Berry", "Micle Berry", 
    "Custap Berry", "Jaboca Berry", "Rowap Berry", "Kee Berry", "Maranga Berry", "Roseli Berry", "Chople Berry", 
    "Kebia Berry", "Shuca Berry", "Coba Berry", "Payapa Berry", "Tanga Berry", "Charti Berry", "Kasib Berry", 
    "Haban Berry", "Colbur Berry", "Babiri Berry", "Chilan Berry", "Adrenaline Orb", "Leppa Berry", "Iron Ball"
]

NATURES = {
    "Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA",
    "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA",
    "Naive": "+Spe, -SpD", "Hasty": "+Spe, -Def", "Lonely": "+Atk, -Def", "Brave": "+Atk, -Spe",
    "Naughty": "+Atk, -SpD", "Mild": "+SpA, -Def", "Quiet": "+SpA, -Spe", "Rash": "+SpA, -SpD",
    "Relaxed": "+Def, -Spe", "Sassy": "+SpD, -Spe", "Lax": "+Def, -SpD", "Gentle": "+SpD, -Def",
    "Hardy": "Neutrale", "Docile": "Neutrale", "Serious": "Neutrale", "Bashful": "Neutrale", "Quirky": "Neutrale"
}
def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]; evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

if 'team' not in st.session_state: 
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set()})

# --- LAYOUT PRINCIPALE ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")
col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.subheader("🏟️ RECAP TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**", expanded=True):
            if p['ability']: st.write(f"🌟 **{p['ability']}** @ {p['item']}")
            if p['moves']: # RECAP MOSSE PICKATE
                st.markdown("  \n".join([f"🔹 {m}" for m in p['moves']]))
            if p['spread']: st.caption(f"EVs: {p['spread']} ({p.get('nature', '')})")

with col_main:
    # 1. PICK POKEMON (Layout Centrato)
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

    # 2. PICK MOVES (Layout Centrato)
    elif st.session_state.step == "MOVES":
        curr_idx = st.session_state.current_pkmn_idx
        p = st.session_state.team[curr_idx]
        st.header(f"Mosse per {p['name']} ({len(p['moves'])+1}/4)")
        if not st.session_state.options:
            pool = list(moves_db.keys())
            atk = random.choice([m for m in pool if moves_db[m]['bp'] > 0])
            st.session_state.options = [atk] + random.sample(pool, 3)
            random.shuffle(st.session_state.options)
        
        # Layout compatto in colonne per centrare
        for m in st.session_state.options:
            info = moves_db[m]
            st.markdown(f"""
            <div class="choice-block">
                <span class="type-badge {info['type'].lower()}">{info['type']}</span>
                <span class="cat-badge {info['cat_class']}">{info['cat_label']}</span>
                <b>BP: {info['bp'] if info['bp']>0 else '--'}</b><br>
                <small style="color: #aaa;">{info['desc']}</small>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Scegli {m}", key=f"mv_{m}"):
                p['moves'].append(m); st.session_state.options = []
                if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                st.rerun()

    # 3-6. LOGICA OTTIMIZZATA FASI (Abilità, Strumento, Spread, Natura)
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
                if step == "ABILITY": p['ability'] = opt; next_step = "ITEM"
                elif step == "ITEM": p['item'] = opt; next_step = "SPREAD"
                elif step == "SPREAD": p['spread'] = opt; next_step = "NATURE"
                elif step == "NATURE":
                    p['nature'] = opt; next_pk = st.session_state.current_pkmn_idx + 1
                    if next_pk < 6: st.session_state.current_pkmn_idx = next_pk; next_step = "MOVES"
                    else: next_step = "FINISHED"
                
                st.session_state.options = []; st.session_state.step = next_step; st.rerun()

    elif st.session_state.step == "FINISHED":
        st.success("Draft Completato!")
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("🔄 RESET"): st.session_state.clear(); st.rerun()