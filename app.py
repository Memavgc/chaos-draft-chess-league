import streamlit as st
import json, random, os
import requests

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# CSS: Interfaccia Dark Mode, bordi gialli e stile scacchi
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
.stButton>button { width: 100%; border-radius: 5px; background-color: #1f2530; color: white; border: 1px solid #444; transition: 0.3s; font-weight: bold; }
.stButton>button:hover { border-color: #f1c40f; color: #f1c40f; transform: scale(1.02); }
.type-badge {
    padding: 2px 10px; border-radius: 4px; color: white; font-weight: bold;
    text-shadow: 1px 1px 2px black; display: inline-block; margin: 2px; font-size: 0.8em;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE STATICI ---
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

# Magic Guard rimossa, aggiunte Dauntless Shield, Mold Breaker e altre top-tier
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

# Solar Beam e Solar Blade sono state rimosse dalla blacklist (ora sono pescabili)
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

# --- FUNZIONI DI SUPPORTO ---
def get_type_badge(t):
    color = TYPE_COLORS.get(t, "#68A090")
    return f'<span class="type-badge" style="background-color:{color};">{t}</span>'

@st.cache_data(show_spinner=False)
def get_sprite(name):
    clean = "".join(e for e in name.lower() if e.isalnum())
    # Fallback su sprite statico se l'animato fallisce (Showdown URL)
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
            st.error("⚠️ File JSON non trovati nella cartella /data!")
            return [], {}

        with open(pk_path, "r", encoding="utf-8") as f: pkmn_data = json.load(f)
        with open(mv_path, "r", encoding="utf-8") as f: moves_data = json.load(f)
        
        # Pulizia Pokémon: Case-insensitive per le chiavi e filtri tier
        clean_pkmn = []
        for p in pkmn_data:
            name = p.get('name') or p.get('Name')
            tier = str(p.get('tier') or p.get('Tier') or "").upper()
            if name and "GMAX" not in name.upper() and "TERA" not in name.upper() and tier not in ["UBER", "AG"]:
                clean_pkmn.append({'name': name, 'tier': tier})
        
        # Pulizia Mosse
        clean_moves = {}
        for nm, m in moves_data.items():
            nm_clean = nm.lower().replace(" ","").replace("-","")
            if nm_clean not in BLACKLIST_MOSSE and not m.get("isZ") and not m.get("isMax"):
                cat = m.get("category") or m.get("Category") or "Status"
                clean_moves[nm] = {
                    "type": m.get("type") or m.get("Type") or "Normal", 
                    "bp": m.get("basePower") or m.get("BasePower") or 0,
                    "cat": cat.replace("Physical", "Fisico").replace("Special", "Speciale").replace("Status", "Stato")
                }
        return clean_pkmn, clean_moves
    except Exception as e:
        st.error(f"Errore caricamento asset: {e}")
        return [], {}

# Inizializzazione dati
pkmn_pool, moves_db = load_assets()

# --- LOGICA DI SESSIONE ---
if 'team' not in st.session_state:
    st.session_state.update({
        'team': [], 
        'step': "DRAFT_PKMN", 
        'current_pkmn_idx': 0, 
        'options': [], 
        'used_pkmn': set(), 
        'used_moves': set()
    })

# --- UI PRINCIPALE ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")

if not pkmn_pool:
    st.error("Il database Pokémon è vuoto. Verifica il file pokemon_clean.json.")
    st.stop()

col_main, col_side = st.columns([2.5, 1.5])

# RIEPILOGO ROSTER (Sidebar destra)
with col_side:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.subheader("🏟️ ROSTER ATTUALE")
    if not st.session_state.team:
        st.info("Inizia il draft per vedere i tuoi Pokémon qui.")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**"):
            if p['moves']: st.markdown(f"**Mosse:** {', '.join(p['moves'])}")
            if p['ability']: st.markdown(f"**Abilità:** {p['ability']} | **Item:** {p['item']}")
            if p['spread']: st.caption(f"EVs: {p['spread']} ({p['nature']})")
    st.markdown('</div>', unsafe_allow_html=True)

# GESTIONE FASI (Area principale)
with col_main:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # FASE 1: DRAFT POKEMON
    if st.session_state.step == "DRAFT_PKMN":
        st.header(f"Seleziona Pokémon {len(st.session_state.team)+1}/6")
        available = [p for p in pkmn_pool if p['name'] not in st.session_state.used_pkmn]
        
        if not st.session_state.options:
            sample_count = min(3, len(available))
            if sample_count > 0:
                st.session_state.options = random.sample(available, sample_count)
                for opt in st.session_state.options: st.session_state.used_pkmn.add(opt['name'])
            else:
                st.error("Fine dei Pokémon disponibili!")

        cols = st.columns(len(st.session_state.options))
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                st.image(get_sprite(p['name']), width=150)
                if st.button(f"SCEGLI {p['name'].upper()}", key=f"pkbtn_{i}"):
                    st.session_state.team.append({
                        "name": p['name'], "moves": [], "ability": "", 
                        "item": "", "nature": "", "spread": ""
                    })
                    st.session_state.options = []
                    if len(st.session_state.team) == 6: st.session_state.step = "MOVES"
                    st.rerun()

    # FASE 2: DRAFT MOSSE
    elif st.session_state.step == "MOVES":
        idx = st.session_state.current_pkmn_idx
        p = st.session_state.team[idx]
        st.header(f"Abilità per {p['name'].upper()} ({len(p['moves'])+1}/4)")
        
        if not st.session_state.options:
            avail_m = [m for m in moves_db.keys() if m not in st.session_state.used_moves]
            # Garantiamo almeno una mossa d'attacco (BP > 0)
            pool_atk = [m for m in avail_m if moves_db[m]['bp'] > 0]
            m_dmg = random.choice(pool_atk) if pool_atk else random.choice(avail_m)
            others = random.sample([m for m in avail_m if m != m_dmg], min(3, len(avail_m)-1))
            st.session_state.options = others + [m_dmg]
            random.shuffle(st.session_state.options)
            
        for m in st.session_state.options:
            m_info = moves_db[m]
            btn_label = f"{m} ({m_info['type']} | BP: {m_info['bp']} | {m_info['cat']})"
            if st.button(btn_label, key=f"mv_{m}"):
                p['moves'].append(m)
                st.session_state.used_moves.add(m)
                st.session_state.options = []
                if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                st.rerun()

    # FASE 3: ABILITÀ
    elif st.session_state.step == "ABILITY":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Seleziona Abilità: {p['name'].upper()}")
        if not st.session_state.options:
            st.session_state.options = random.sample(ABILITIES_DB, 4)
        for a in st.session_state.options:
            if st.button(a, key=f"ab_{a}"):
                p['ability'] = a
                st.session_state.options = []
                st.session_state.step = "ITEM"
                st.rerun()

    # FASE 4: STRUMENTO
    elif st.session_state.step == "ITEM":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Seleziona Strumento: {p['name'].upper()}")
        if not st.session_state.options:
            st.session_state.options = random.sample(ITEMS_DB, 4)
        for i in st.session_state.options:
            if st.button(i, key=f"it_{i}"):
                p['item'] = i
                st.session_state.options = []
                st.session_state.step = "NATURE"
                st.rerun()

    # FASE 5: NATURA
    elif st.session_state.step == "NATURE":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Seleziona Natura: {p['name'].upper()}")
        if not st.session_state.options:
            st.session_state.options = random.sample(list(NATURES_DB.keys()), 4)
        for n in st.session_state.options:
            if st.button(f"{n} ({NATURES_DB[n]})", key=f"nt_{n}"):
                p['nature'] = n
                st.session_state.options = []
                st.session_state.step = "SPREAD"
                st.rerun()

    # FASE 6: EV SPREAD (CHAOS)
    elif st.session_state.step == "SPREAD":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Seleziona EV Spread: {p['name'].upper()}")
        if not st.session_state.options:
            st.session_state.options = [gen_chaos_spread() for _ in range(4)]
        for s in st.session_state.options:
            if st.button(s, key=f"sp_{s}"):
                p['spread'] = s
                st.session_state.options = []
                st.session_state.used_moves = set() # Reset pool mosse per il prossimo Pokémon
                if st.session_state.current_pkmn_idx < 5:
                    st.session_state.current_pkmn_idx += 1
                    st.session_state.step = "MOVES"
                else:
                    st.session_state.step = "FINISHED"
                st.rerun()

    # CONCLUSIONE: EXPORT
    elif st.session_state.step == "FINISHED":
        st.header("🏁 DRAFT COMPLETATO!")
        output = ""
        for p in st.session_state.team:
            output += f"{p['name']} @ {p['item']}\n"
            output += f"Ability: {p['ability']}\n"
            output += f"EVs: {p['spread']}\n"
            output += f"{p['nature']} Nature\n"
            for m in p['moves']:
                output += f"- {m}\n"
            output += "\n"
        
        st.subheader("Copia e incolla su Pokémon Showdown:")
        st.code(output, language="text")
        
        if st.button("🔄 NUOVO DRAFT"):
            st.session_state.clear()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)