import json, random, os
import urllib.request
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- CSS: CENTRATURA ASSOLUTA ---
st.markdown("""
<style>
    [data-testid="column"] { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; text-align: center; }
    div.stButton { display: flex; justify-content: center; width: 100%; }
    div.stButton > button { width: 100% !important; max-width: 220px !important; margin-bottom: 5px !important; }
    .type-badge { padding: 4px 10px; border-radius: 6px; color: white; font-weight: bold; font-size: 0.75em; text-transform: uppercase; margin-right: 5px; }
    .cat-badge { padding: 4px 8px; border-radius: 6px; color: white; font-weight: bold; font-size: 0.75em; display: inline-block; margin-right: 10px; }
    .phys { background-color: #C22E28; } .spec { background-color: #6390F0; } .stat { background-color: #705746; }
</style>
""", unsafe_allow_html=True)

# --- MOTORE SPRITE: CONTROLLO PYTHON ---
@st.cache_data(show_spinner=False)
def get_valid_sprite_url(name):
    n_raw = name.lower().replace("'", "").replace(" ", "").strip()
    n_clean = n_raw.replace("-", "")
    base_name = n_raw.split("-")[0].replace("mega", "").replace("primal", "")
    
    urls_to_try = [
        f"https://play.pokemonshowdown.com/sprites/ani/{n_clean}.gif",        
        f"https://play.pokemonshowdown.com/sprites/ani/{n_raw}.gif",          
        f"https://play.pokemonshowdown.com/sprites/custom/{n_clean}.png",     
        f"https://play.pokemonshowdown.com/sprites/gen5/{n_clean}.png",       
        f"https://play.pokemonshowdown.com/sprites/ani/{base_name}.gif",      
        f"https://play.pokemonshowdown.com/sprites/gen5/{base_name}.png",     
        "https://play.pokemonshowdown.com/sprites/items/poke-doll.png"        
    ]
    
    for url in urls_to_try:
        try:
            req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=1.5)
            if resp.status == 200:
                return url
        except Exception:
            continue
    return urls_to_try[-1]

def display_sprite(name):
    valid_url = get_valid_sprite_url(name)
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; width: 100%; height: 160px; margin-bottom: 10px;">
            <img src="{valid_url}" style="max-height: 150px; max-width: 100%; object-fit: contain;">
        </div>
    """, unsafe_allow_html=True)

# --- DATABASE MASSIVI ---
ABILITIES = {
    "Huge Power": "Raddoppia la statistica Attacco del Pokémon.",
    "Intimidate": "Abbassa l'Attacco degli avversari di 1 livello al suo ingresso in campo.",
    "Regenerator": "Recupera 1/3 dei PS massimi quando viene sostituito.",
    "Levitate": "Rende immuni alle mosse di tipo Terra e alle Punte.",
    "Technician": "Potenzia del 50% le mosse con potenza base di 60 o inferiore.",
    "Moxie": "Aumenta l'Attacco di 1 livello quando manda KO un avversario.",
    "Speed Boost": "Aumenta la Velocità di 1 livello alla fine di ogni turno.",
    "Contrary": "Inverte i cambiamenti delle statistiche.",
    "Adaptability": "Aumenta il moltiplicatore STAB da 1.5x a 2.0x.",
    "Sheer Force": "Aumenta la potenza del 30% ma annulla gli effetti secondari.",
    "Unaware": "Ignora le modifiche alle statistiche dell'avversario.",
    "Magic Guard": "Previene qualsiasi danno indiretto.",
    "Prankster": "Dà priorità +1 alle mosse di stato.",
    "Sword of Ruin": "Riduce la Difesa degli altri Pokémon in campo del 25%.",
    "Beads of Ruin": "Riduce la Difesa Speciale degli altri Pokémon in campo del 25%.",
    "Orichalcum Pulse": "Evoca il sole. L'Attacco aumenta del 33%.",
    "Hadron Engine": "Evoca il Campo Elettrico. L'Att. Speciale aumenta del 33%.",
    "Libero": "Cambia il tipo del Pokémon in quello della mossa usata.",
    "Protean": "Cambia il tipo del Pokémon in quello della mossa usata.",
    "Tough Claws": "Aumenta la potenza delle mosse da contatto del 30%.",
    "Serene Grace": "Raddoppia la probabilità degli effetti secondari.",
    "Magic Bounce": "Riflette le mosse di stato e hazards.",
    "Drizzle": "Evoca la Pioggia per 5 turni.",
    "Drought": "Evoca la Luce Solare Intensa per 5 turni.",
    "Sand Stream": "Evoca la Terrempesta per 5 turni.",
    "Snow Warning": "Evoca la Neve per 5 turni.",
    "Multiscale": "Dimezza i danni subiti a PS massimi.",
    "Shadow Tag": "Impedisce agli avversari di fuggire.",
    "Guts": "Aumenta l'Attacco del 50% se con alterazione di stato.",
    "No Guard": "Nessuna mossa può fallire.",
    "Compound Eyes": "Aumenta la precisione del 30%.",
    "Simple": "Raddoppia le modifiche alle statistiche.",
    "Tinted Lens": "Raddoppia i danni 'non molto efficaci'.",
    "Moody": "Aumenta una statistica di 2 e ne riduce un'altra di 1 ogni turno.",
    "Sturdy": "Sopravvive con 1 PS a mosse letali da PS massimi.",
    "Water Absorb": "Annulla mosse Acqua e recupera 1/4 PS.",
    "Flash Fire": "Immunità mosse Fuoco; aumenta danni Fuoco.",
    "Volt Absorb": "Annulla mosse Elettro e recupera 1/4 PS.",
    "Defiant": "Aumenta l'Attacco di 2 se una statistica cala.",
    "Competitive": "Aumenta l'Att. Speciale di 2 se una statistica cala."
}

ITEMS = {
    "Life Orb": "Danni +30%, perde 10% PS ad attacco.",
    "Choice Band": "Attacco +50%, blocca su una mossa.",
    "Choice Specs": "Att. Speciale +50%, blocca su una mossa.",
    "Choice Scarf": "Velocità +50%, blocca su una mossa.",
    "Assault Vest": "Dif. Speciale +50%, vieta mosse di stato.",
    "Focus Sash": "Sopravvive a KO con 1 PS (se a PS max).",
    "Leftovers": "Ripristina 1/16 dei PS ogni turno.",
    "Heavy-Duty Boots": "Immunità alle entry hazards.",
    "Rocky Helmet": "Danno 1/6 PS se subisce mossa da contatto.",
    "Expert Belt": "Mosse superefficaci +20% danno.",
    "Sitrus Berry": "Ripristina 25% PS sotto la metà.",
    "Lum Berry": "Cura qualsiasi alterazione di stato una volta.",
    "White Herb": "Ripristina statistiche calate una volta.",
    "Power Herb": "Mosse a due turni colpiscono subito.",
    "Eviolite": "Dif e Dif.Sp +50% se si può evolvere.",
    "Black Sludge": "Cura i Veleno, danneggia gli altri.",
    "Flame Orb": "Scotta il possessore a fine turno.",
    "Toxic Orb": "Iperavvelena il possessore a fine turno.",
    "Air Balloon": "Immunità mosse Terra finché non colpito.",
    "Weakness Policy": "Att e Att.Sp +2 se colpito superefficace.",
    "Eject Button": "Sostituisce il Pokémon se colpito.",
    "Red Card": "Forza l'avversario a cambiare Pokémon se colpisce.",
    "Scope Lens": "Probabilità brutto colpo +1.",
    "Wide Lens": "Precisione +10%.",
    "Covert Cloak": "Ignora effetti secondari degli attacchi.",
    "Loaded Dice": "Mosse multi-colpo colpiscono 4-5 volte."
}

NATURES = {
    "Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA",
    "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA",
    "Naive": "+Spe, -SpD", "Hasty": "+Spe, -Def", "Lonely": "+Atk, -Def", "Brave": "+Atk, -Spe",
    "Naughty": "+Atk, -SpD", "Mild": "+SpA, -Def", "Quiet": "+SpA, -Spe", "Rash": "+SpA, -SpD",
    "Relaxed": "+Def, -Spe", "Sassy": "+SpD, -Spe", "Lax": "+Def, -SpD", "Gentle": "+SpD, -Def",
    "Hardy": "Neutrale", "Docile": "Neutrale", "Serious": "Neutrale", "Bashful": "Neutrale", "Quirky": "Neutrale"
}

# --- FILTRO SPECIES CLAUSE ---
# Raggruppa i Pokémon con trattini nella loro forma base, ma preserva le eccezioni storiche.
DASHED_BASES = ["ho-oh", "porygon-z", "jangmo-o", "hakamo-o", "kommo-o"]
def get_species_group(name):
    low = name.lower()
    for d in DASHED_BASES:
        if low.startswith(d): return d
    return low.split('-')[0]

# --- CARICAMENTO ASSET E FILTRI MOSSE ---
@st.cache_data(show_spinner=False)
def load_assets():
    pk_pool = []; mv_db = {}
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
                
                if any(x in nm.upper() for x in ["G-MAX", "GMAX", " Z-", "MAX ", " Z "]) or m.get("isZ") or m.get("isMax"):
                    continue
                if clean_m in mv_trash: continue
                if 0 < bp < 55 and clean_m != "hiddenpower": continue

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

def gen_chaos_spread():
    stats = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]; evs = [0]*6; rem = 508
    while rem > 0:
        i = random.randint(0,5); add = min(random.choice([4, 40, 100, 252]), rem, 252-evs[i])
        evs[i]+=add; rem-=add
    return " / ".join([f"{evs[i]} {stats[i]}" for i in range(6) if evs[i]>0])

if 'team' not in st.session_state: 
    st.session_state.update({'team': [], 'step': "DRAFT_PKMN", 'current_pkmn_idx': 0, 'options': [], 'used_pkmn': set()})

# --- UI PRINCIPALE ---
st.title("♟️ CHAOS DRAFT CHESS LEAGUE")
col_main, col_side = st.columns([2.5, 1.5])

with col_side:
    st.subheader("🏟️ RECAP TEAM")
    for i, p in enumerate(st.session_state.team):
        with st.expander(f"**{i+1}. {p['name'].upper()}**", expanded=True):
            if p['ability']: st.write(f"🌟 **{p['ability']}** @ {p['item']}")
            if p['moves']: st.markdown("  \n".join([f"🔹 {m}" for m in p['moves']]))
            if p['spread']: st.caption(f"EVs: {p['spread']} ({p.get('nature', '')})")

with col_main:
    # 1. DRAFT POKEMON (CON SPECIES CLAUSE)
    if st.session_state.step == "DRAFT_PKMN":
        # Trova tutte le "famiglie base" già pescate (es. "zarude")
        used_groups = {get_species_group(name) for name in st.session_state.used_pkmn}
        
        if not st.session_state.options:
            # Crea un pool valido escludendo TUTTE le forme di chi è già stato pescato
            valid_pool = [p for p in pk_pool if get_species_group(p['name']) not in used_groups]
            random.shuffle(valid_pool)
            
            opts = []
            temp_groups = set(used_groups)
            # Pesca 3 Pokémon assicurandosi che non siano due forme dello stesso (es. niente Zarude + Zarude-Dada insieme)
            for p in valid_pool:
                grp = get_species_group(p['name'])
                if grp not in temp_groups:
                    opts.append(p)
                    temp_groups.add(grp)
                if len(opts) == 3: break
            
            st.session_state.options = opts

        cols = st.columns(3)
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                display_sprite(p['name'])
                if st.button(f"SCEGLI {p['name']}", key=f"pk_{i}", use_container_width=True):
                    st.session_state.team.append({"name": p['name'], "moves": [], "ability": "", "item": "", "nature": "", "spread": ""})
                    st.session_state.used_pkmn.add(p['name']); st.session_state.options = []
                    if len(st.session_state.team) == 6: st.session_state.step = "MOVES"
                    st.rerun()

    # 2. DRAFT MOSSE (CON FIX ANTI-DOPPIONI)
    elif st.session_state.step == "MOVES":
        p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"Mosse per {p['name']} ({len(p['moves'])+1}/4)")
        
        if not st.session_state.options:
            # Pool che esclude esplicitamente le mosse GIA' SCELTE da questo Pokémon
            available_moves = [m for m in moves_db.keys() if m not in p['moves']]
            atk_moves = [m for m in available_moves if moves_db[m]['bp'] > 0]
            
            if atk_moves:
                # 1. Scegli l'attacco garantito
                atk = random.choice(atk_moves)
                # 2. RIMUOVI l'attacco garantito dal pool restante prima di pescare le altre 3
                remaining_moves = [m for m in available_moves if m != atk]
                st.session_state.options = [atk] + random.sample(remaining_moves, 3)
            else:
                # Fallback di sicurezza se non ci sono più attacchi
                st.session_state.options = random.sample(available_moves, 4)
                
            random.shuffle(st.session_state.options)
        
        for m in st.session_state.options:
            info = moves_db[m]
            c1, c2 = st.columns([1, 2.5])
            with c1:
                if st.button(f"Scegli {m}", key=f"mv_{m}", use_container_width=True):
                    p['moves'].append(m); st.session_state.options = []
                    if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                    st.rerun()
            with c2:
                st.markdown(f"""<div style="text-align: left; padding: 5px; border-left: 3px solid #444;">
                    <span class="type-badge {info['type'].lower()}">{info['type']}</span>
                    <span class="cat-badge {info['cat_class']}">{info['cat_label']}</span>
                    <b>BP: {info['bp'] if info['bp']>0 else '--'}</b><br><small>{info['desc']}</small></div>""", unsafe_allow_html=True)

    # 3-6. FASI CON DESCRIZIONI
    elif st.session_state.step in ["ABILITY", "ITEM", "SPREAD", "NATURE"]:
        step = st.session_state.step; p = st.session_state.team[st.session_state.current_pkmn_idx]
        st.header(f"{step} per {p['name']}")
        
        if not st.session_state.options:
            if step == "ABILITY": st.session_state.options = random.sample(list(ABILITIES.keys()), 4)
            elif step == "ITEM": st.session_state.options = random.sample(list(ITEMS.keys()), 4)
            elif step == "SPREAD": st.session_state.options = [gen_chaos_spread() for _ in range(4)]
            elif step == "NATURE": st.session_state.options = random.sample(list(NATURES.keys()), 4)

        for opt in st.session_state.options:
            c1, c2 = st.columns([1, 2.5])
            with c1:
                label = f"{opt} ({NATURES[opt]})" if step == "NATURE" else opt
                if st.button(label, use_container_width=True):
                    if step == "ABILITY": p['ability'] = opt; next_s = "ITEM"
                    elif step == "ITEM": p['item'] = opt; next_s = "SPREAD"
                    elif step == "SPREAD": p['spread'] = opt; next_s = "NATURE"
                    elif step == "NATURE":
                        p['nature'] = opt
                        if st.session_state.current_pkmn_idx < 5: st.session_state.current_pkmn_idx += 1; next_s = "MOVES"
                        else: next_s = "FINISHED"
                    st.session_state.options = []; st.session_state.step = next_s; st.rerun()
            with c2:
                desc = ""
                if step == "ABILITY": desc = ABILITIES.get(opt, "")
                elif step == "ITEM": desc = ITEMS.get(opt, "")
                if desc:
                    st.markdown(f"<div style='text-align: left; padding: 5px;'><small>{desc}</small></div>", unsafe_allow_html=True)

    elif st.session_state.step == "FINISHED":
        st.success("Draft Completato!")
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("🔄 RESET", use_container_width=True): st.session_state.clear(); st.rerun()