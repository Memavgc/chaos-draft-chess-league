import json, random, os
import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Chaos Draft Chess League", layout="wide")

# --- CSS: CENTRATURA ASSOLUTA ---
st.markdown("""
<style>
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        text-align: center;
    }
    div.stButton {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    div.stButton > button {
        width: 100% !important;
        max-width: 220px !important;
        margin-bottom: 5px !important;
    }
    .type-badge { padding: 4px 10px; border-radius: 6px; color: white; font-weight: bold; font-size: 0.75em; text-transform: uppercase; margin-right: 5px; }
    .cat-badge { padding: 4px 8px; border-radius: 6px; color: white; font-weight: bold; font-size: 0.75em; display: inline-block; margin-right: 10px; }
    .phys { background-color: #C22E28; } .spec { background-color: #6390F0; } .stat { background-color: #705746; }
</style>
""", unsafe_allow_html=True)

# --- LOGICA SPRITE: AGGIUNTO SUPPORTO CUSTOM/Z-A ---
# --- LOGICA SPRITE: FALLBACK ANTIPROIETTILE ---
def display_sprite(name):
    # 1. Pulizia rigorosa del nome
    n_raw = name.lower().replace("'", "").replace(" ", "").strip()
    n_clean = n_raw.replace("-", "") # es. gyaradosmega, arcaninehisui
    base_name = n_raw.split("-")[0].replace("mega", "").replace("primal", "") # es. ogerpon, groudon
    
    # 2. Creiamo una lista di TUTTI gli URL possibili (dal più specifico al più generico)
    urls = [
        f"https://play.pokemonshowdown.com/sprites/ani/{n_clean}.gif",       # 1. Animato pulito (Mega e Hisui standard)
        f"https://play.pokemonshowdown.com/sprites/ani/{n_raw}.gif",         # 2. Animato con trattino (Ho-Oh, Porygon-Z)
        f"https://play.pokemonshowdown.com/sprites/dex/{n_clean}.png",       # 3. Statico pulito (Per Pokémon di Gen 9 senza GIF)
        f"https://play.pokemonshowdown.com/sprites/ani/{base_name}.gif",     # 4. Fallback: Forma Base Animata
        f"https://play.pokemonshowdown.com/sprites/dex/{base_name}.png",     # 5. Fallback: Forma Base Statica
        "https://play.pokemonshowdown.com/sprites/items/poke-doll.png"       # 6. Sostituto (Se fallisce tutto, mostra la bambola invece dell'errore!)
    ]
    
    primary_url = urls[0]
    # Uniamo gli URL di riserva separati da una "virgola"
    fallback_string = ",".join(urls[1:])
    
    # 3. Script JS che non usa virgolette annidate (non si rompe in Streamlit)
    js_script = """
        let fallbackList = this.getAttribute('data-urls').split(',');
        if (fallbackList.length > 0 && fallbackList[0] !== '') {
            this.src = fallbackList.shift();
            this.setAttribute('data-urls', fallbackList.join(','));
        } else {
            this.onerror = null;
        }
    """.replace('\n', ' ')

    # 4. Box HTML con centratura forzata al 100%
    st.markdown(f"""
        <div style="text-align: center; margin: 0 auto; width: 100%; height: 160px; display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
            <img src="{primary_url}" 
                 data-urls="{fallback_string}" 
                 onerror="{js_script}" 
                 style="max-height: 150px; max-width: 100%; object-fit: contain; display: block; margin: 0 auto;">
        </div>
    """, unsafe_allow_html=True)
# --- DATABASE DIZIONARI CON DESCRIZIONI ---
ABILITIES = {
    "Huge Power": "Raddoppia la statistica Attacco del Pokémon.",
    "Intimidate": "Abbassa l'Attacco degli avversari di 1 livello al suo ingresso in campo.",
    "Regenerator": "Recupera 1/3 dei PS massimi quando viene sostituito.",
    "Levitate": "Rende immuni alle mosse di tipo Terra e alle Punte.",
    "Technician": "Potenzia del 50% le mosse con potenza base di 60 o inferiore.",
    "Moxie": "Aumenta l'Attacco di 1 livello quando manda KO un avversario.",
    "Speed Boost": "Aumenta la Velocità di 1 livello alla fine di ogni turno.",
    "Contrary": "Inverte i cambiamenti delle statistiche (es. i cali diventano aumenti).",
    "Adaptability": "Aumenta il moltiplicatore STAB da 1.5x a 2.0x.",
    "Sheer Force": "Aumenta la potenza del 30% ma annulla gli effetti secondari delle mosse.",
    "Unaware": "Ignora le modifiche alle statistiche dell'avversario nel calcolo dei danni.",
    "Magic Guard": "Previene qualsiasi danno indiretto (tossina, scottatura, punte, ecc.).",
    "Prankster": "Dà priorità +1 alle mosse di stato.",
    "Sword of Ruin": "Riduce la Difesa degli altri Pokémon in campo del 25%.",
    "Beads of Ruin": "Riduce la Difesa Speciale degli altri Pokémon in campo del 25%.",
    "Orichalcum Pulse": "Evoca il sole. In presenza di sole, l'Attacco aumenta del 33%.",
    "Hadron Engine": "Evoca il Campo Elettrico. Su questo campo, l'Attacco Speciale aumenta del 33%.",
    "Libero": "Cambia il tipo del Pokémon in quello della mossa che sta per usare (una volta per switch).",
    "Protean": "Cambia il tipo del Pokémon in quello della mossa che sta per usare (una volta per switch).",
    "Tough Claws": "Aumenta la potenza delle mosse da contatto del 30%.",
    "Serene Grace": "Raddoppia la probabilità che si verifichino gli effetti secondari delle mosse.",
    "Magic Bounce": "Riflette le mosse di stato, le entry hazards e le alterazioni di stato.",
    "Drizzle": "Evoca la Pioggia per 5 turni al suo ingresso in campo.",
    "Drought": "Evoca la Luce Solare Intensa per 5 turni al suo ingresso in campo.",
    "Sand Stream": "Evoca la Terrempesta per 5 turni al suo ingresso in campo.",
    "Snow Warning": "Evoca la Neve per 5 turni al suo ingresso in campo.",
    "Multiscale": "Dimezza i danni subiti se il Pokémon ha i PS al massimo.",
    "Shadow Tag": "Impedisce agli avversari di essere sostituiti o fuggire.",
    "Guts": "Aumenta l'Attacco del 50% se affetto da alterazioni di stato; ignora il calo della scottatura.",
    "No Guard": "Tutte le mosse usate dal e contro il Pokémon non possono fallire.",
    "Compound Eyes": "Aumenta la precisione delle mosse del 30%.",
    "Simple": "Raddoppia l'effetto delle modifiche alle statistiche.",
    "Tinted Lens": "Raddoppia la potenza delle mosse 'non molto efficaci'.",
    "Moody": "Aumenta una statistica a caso di 2 livelli e ne riduce un'altra di 1 livello ogni turno.",
    "Sturdy": "Sopravvive con 1 PS se colpito da una mossa che lo manderebbe KO partendo da PS massimi.",
    "Water Absorb": "Annulla i danni delle mosse Acqua e recupera 1/4 dei PS massimi.",
    "Flash Fire": "Immunità alle mosse Fuoco; subirne una potenzia le proprie mosse Fuoco del 50%.",
    "Volt Absorb": "Annulla i danni delle mosse Elettro e recupera 1/4 dei PS massimi.",
    "Defiant": "Aumenta l'Attacco di 2 livelli se una statistica viene abbassata dall'avversario.",
    "Competitive": "Aumenta l'Att. Speciale di 2 livelli se una statistica viene abbassata dall'avversario."
}

ITEMS = {
    "Life Orb": "Aumenta la potenza delle mosse del 30%, ma toglie il 10% dei PS ad ogni attacco andato a segno.",
    "Choice Band": "Aumenta l'Attacco del 50%, ma permette di usare solo la prima mossa selezionata.",
    "Choice Specs": "Aumenta l'Att. Speciale del 50%, ma permette di usare solo la prima mossa selezionata.",
    "Choice Scarf": "Aumenta la Velocità del 50%, ma permette di usare solo la prima mossa selezionata.",
    "Assault Vest": "Aumenta la Difesa Speciale del 50%, ma impedisce l'uso di mosse di stato.",
    "Focus Sash": "Se il Pokémon ha PS massimi, sopravvive a un attacco letale con 1 PS. Si consuma dopo l'uso.",
    "Leftovers": "Ripristina 1/16 dei PS massimi alla fine di ogni turno.",
    "Heavy-Duty Boots": "Protegge il Pokémon dagli effetti delle trappole (Levitoroccia, Punte, ecc.) quando entra in campo.",
    "Rocky Helmet": "Infligge danni pari a 1/6 dei PS massimi all'avversario se si subisce una mossa da contatto.",
    "Expert Belt": "Aumenta del 20% la potenza delle mosse 'super efficaci'.",
    "Sitrus Berry": "Ripristina il 25% dei PS massimi quando i PS scendono sotto la metà.",
    "Lum Berry": "Cura qualsiasi alterazione di stato una volta.",
    "White Herb": "Ripristina le statistiche abbassate una volta.",
    "Power Herb": "Permette di eseguire istantaneamente mosse che richiedono un turno di caricamento (es. Solarraggio).",
    "Eviolite": "Aumenta Difesa e Dif. Speciale del 50% se il Pokémon può ancora evolversi.",
    "Black Sludge": "Cura 1/16 dei PS ogni turno ai Pokémon Veleno. Danneggia gli altri tipi.",
    "Flame Orb": "Scotta chi lo tiene alla fine del turno.",
    "Toxic Orb": "Iperavvelena chi lo tiene alla fine del turno.",
    "Air Balloon": "Rende immuni alle mosse di tipo Terra finché il Pokémon non viene colpito da un attacco diretto.",
    "Weakness Policy": "Se colpito da una mossa super efficace, Attacco e Att. Speciale aumentano di 2 livelli.",
    "Eject Button": "Se colpito da un attacco, il Pokémon viene sostituito immediatamente.",
    "Red Card": "Chi colpisce il possessore di questo strumento viene forzato allo switch con un alleato casuale.",
    "Scope Lens": "Aumenta la probabilità di brutto colpo di 1 livello.",
    "Wide Lens": "Aumenta la precisione delle mosse del 10%.",
    "Covert Cloak": "Protegge dagli effetti secondari degli attacchi avversari (es. tentennamento da Bruciapelo).",
    "Loaded Dice": "Le mosse multi-colpo colpiranno sempre per almeno 4 volte (o 2 su 2 per mosse come Doppio Colpo)."
}

NATURES = {
    "Adamant": "+Atk, -SpA", "Modest": "+SpA, -Atk", "Timid": "+Spe, -Atk", "Jolly": "+Spe, -SpA",
    "Bold": "+Def, -Atk", "Calm": "+SpD, -Atk", "Impish": "+Def, -SpA", "Careful": "+SpD, -SpA",
    "Naive": "+Spe, -SpD", "Hasty": "+Spe, -Def", "Lonely": "+Atk, -Def", "Brave": "+Atk, -Spe",
    "Naughty": "+Atk, -SpD", "Mild": "+SpA, -Def", "Quiet": "+SpA, -Spe", "Rash": "+SpA, -SpD",
    "Relaxed": "+Def, -Spe", "Sassy": "+SpD, -Spe", "Lax": "+Def, -SpD", "Gentle": "+SpD, -Def",
    "Hardy": "Neutrale", "Docile": "Neutrale", "Serious": "Neutrale", "Bashful": "Neutrale", "Quirky": "Neutrale"
}

# --- CARICAMENTO ASSET E FILTRI ---
@st.cache_data
def load_assets():
    pk_pool = []; mv_db = {}
    pk_banned = ["ZACIAN", "ZAMAZENTA", "ETERNATUS", "MEWTWO", "RAYQUAZA", "KYOGRE", "GROUDON", "ARCEUS", "DIALGA", "PALKIA", "GIRATINA", "XERNEAS", "YVELTAL", "SOLGALEO", "LUNALA", "CALYREX", "KORAIDON", "MIRAIDON", "DEOXYS", "DARKRAI", "TERAPAGOS", "MAGEARNA", "CHI-YU", "CHIEN-PAO", "TING-LU", "WO-CHIEN"]
    
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
                if any(x in nm.upper() for x in ["G-MAX", "GMAX", " Z-", "MAX ", " Z "]) or m.get("isZ") or m.get("isMax"):
                    continue
                mv_db[nm] = {
                    "type": m.get("type", "Normal"), "bp": m.get("basePower", 0),
                    "cat_class": "phys" if m.get("category") == "Physical" else "spec" if m.get("category") == "Special" else "stat",
                    "cat_label": "FISICA ⚔️" if m.get("category") == "Physical" else "SPECIALE 🔮" if m.get("category") == "Special" else "STATO 🛡️",
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
    # 1. DRAFT POKEMON
    if st.session_state.step == "DRAFT_PKMN":
        available = [p for p in pk_pool if p['name'] not in st.session_state.used_pkmn]
        if not st.session_state.options: st.session_state.options = random.sample(available, 3)
        cols = st.columns(3)
        for i, p in enumerate(st.session_state.options):
            with cols[i]:
                display_sprite(p['name'])
                if st.button(f"SCEGLI {p['name']}", key=f"pk_{i}", use_container_width=True):
                    st.session_state.team.append({"name": p['name'], "moves": [], "ability": "", "item": "", "nature": "", "spread": ""})
                    st.session_state.used_pkmn.add(p['name']); st.session_state.options = []
                    if len(st.session_state.team) == 6: st.session_state.step = "MOVES"
                    st.rerun()

    # 2. DRAFT MOSSE
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
                if st.button(f"Scegli {m}", key=f"mv_{m}", use_container_width=True):
                    p['moves'].append(m); st.session_state.options = []
                    if len(p['moves']) == 4: st.session_state.step = "ABILITY"
                    st.rerun()
            with c2:
                st.markdown(f"""<div style="text-align: left; padding: 5px; border-left: 3px solid #444;">
                    <span class="type-badge {info['type'].lower()}">{info['type']}</span>
                    <span class="cat-badge {info['cat_class']}">{info['cat_label']}</span>
                    <b>BP: {info['bp'] if info['bp']>0 else '--'}</b><br><small>{info['desc']}</small></div>""", unsafe_allow_html=True)

    # 3-6. FASI CON DESCRIZIONI PER ABILITÀ E OGGETTI
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
                # Mostra la descrizione se stiamo scegliendo Abilità o Strumento
                desc = ""
                if step == "ABILITY": desc = ABILITIES.get(opt, "")
                elif step == "ITEM": desc = ITEMS.get(opt, "")
                
                if desc:
                    st.markdown(f"<div style='text-align: left; padding: 5px;'><small>{desc}</small></div>", unsafe_allow_html=True)

    # SCHERMATA FINALE
    elif st.session_state.step == "FINISHED":
        st.success("Draft Completato!")
        res = ""
        for p in st.session_state.team:
            res += f"{p['name']} @ {p['item']}\nAbility: {p['ability']}\nEVs: {p['spread']}\n{p['nature']} Nature\n" + "".join([f"- {m}\n" for m in p['moves']]) + "\n"
        st.code(res)
        if st.button("🔄 RESET", use_container_width=True): st.session_state.clear(); st.rerun()