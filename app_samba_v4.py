"""
O Samba nas Redes — aplicativo (versão final, 110 artistas)
Três perfis: ouvinte (Modelo A), artista (Modelo B) e rodas (camada de eventos, proposta).
Executar:  streamlit run app_samba_v4.py   (CSVs *_v4 e samba_core.py na mesma pasta)
"""

import streamlit as st
from datetime import date

import samba_core as sc

st.set_page_config(
    page_title="O Samba nas Redes",
    page_icon="🎶",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=IM+Fell+English:ital@0;1&family=Lato:wght@300;400&display=swap');

  .stApp {
    background-color: #f5f0e8;
    background-image: radial-gradient(ellipse at 20% 50%, rgba(180,150,100,0.06) 0%, transparent 60%);
  }
  .block-container { padding: 2rem 2rem 4rem 2rem; max-width: 720px; }

  .cabecalho { text-align: center; padding: 2.5rem 1rem 1rem 1rem; border-bottom: 2px solid #8b6914; margin-bottom: 0.5rem; }
  .titulo-principal { font-family: 'Playfair Display', serif; font-size: 2.6rem; font-weight: 700; color: #2c1a0e; letter-spacing: 0.03em; margin: 0; line-height: 1.1; }
  .subtitulo { font-family: 'IM Fell English', serif; font-style: italic; font-size: 1.05rem; color: #6b4c1e; margin-top: 0.4rem; }
  .ornamento { font-size: 1.4rem; color: #8b6914; margin: 0.5rem 0; letter-spacing: 0.3em; }
  .divisor { text-align: center; color: #8b6914; font-size: 1.1rem; letter-spacing: 0.4em; margin: 1.2rem 0; opacity: 0.7; }
  .instrucao { font-family: 'IM Fell English', serif; font-style: italic; color: #4a3520; font-size: 1.0rem; text-align: center; margin-bottom: 1.2rem; }

  /* Botões de escolha de perfil */
  .perfil-btn-container { display: flex; gap: 1rem; justify-content: center; margin: 1.5rem 0; }
  .perfil-card {
    background: #ede8dc;
    border: 2px solid #c4a96a;
    border-radius: 4px;
    padding: 1.5rem 2rem;
    text-align: center;
    cursor: pointer;
    flex: 1;
    transition: all 0.2s;
  }
  .perfil-card:hover { border-color: #8b6914; background: #e8e0ce; }
  .perfil-card.ativo { border-color: #2c1a0e; border-width: 3px; background: #e0d8c8; }
  .perfil-titulo { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #2c1a0e; margin-bottom: 0.3rem; }
  .perfil-desc { font-family: 'IM Fell English', serif; font-style: italic; font-size: 0.85rem; color: #6b4c1e; }
  .perfil-icon { font-size: 2rem; margin-bottom: 0.5rem; }

  /* Explicação do modelo */
  .modelo-explicacao {
    background: #ede8dc;
    border: 1px solid #c4a96a;
    border-left: 4px solid #8b6914;
    padding: 0.9rem 1.2rem;
    margin: 1rem 0 1.5rem 0;
    border-radius: 2px;
  }
  .modelo-titulo { font-family: 'Playfair Display', serif; font-size: 0.9rem; font-weight: 700; color: #2c1a0e; margin-bottom: 0.3rem; }
  .modelo-texto { font-family: 'Lato', sans-serif; font-size: 0.82rem; color: #4a3520; line-height: 1.5; }
  .peso-item { display: inline-block; background: #2c1a0e; color: #f5f0e8; font-size: 0.72rem; padding: 0.1rem 0.4rem; border-radius: 1px; margin: 0.1rem; font-family: 'Lato', sans-serif; }

  /* Inputs */
  .stSelectbox > div > div { background-color: #ede8dc !important; border: 1px solid #8b6914 !important; border-radius: 2px !important; color: #2c1a0e !important; font-family: 'Lato', sans-serif !important; }
  .stSelectbox label { font-family: 'Playfair Display', serif !important; color: #2c1a0e !important; font-weight: 700 !important; }
  .stCheckbox > label { font-family: 'IM Fell English', serif !important; font-style: italic !important; color: #4a3520 !important; font-size: 0.92rem !important; }

  /* Botão */
  .stButton > button { background-color: #2c1a0e !important; color: #f5f0e8 !important; font-family: 'Playfair Display', serif !important; font-size: 1.0rem !important; font-weight: 700 !important; letter-spacing: 0.12em !important; border: none !important; border-radius: 2px !important; padding: 0.6rem 2rem !important; width: 100% !important; text-transform: uppercase !important; }
  .stButton > button:hover { background-color: #4a3520 !important; }

  /* Cards de resultado */
  .card-resultado { background: linear-gradient(135deg, #ede8dc 0%, #e8e0ce 100%); border: 1px solid #c4a96a; border-left: 4px solid #8b6914; border-radius: 2px; padding: 1.1rem 1.3rem; margin-bottom: 0.9rem; box-shadow: 2px 2px 6px rgba(44,26,14,0.08); position: relative; }
  .card-numero { font-family: 'Playfair Display', serif; font-size: 0.75rem; color: #8b6914; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.2rem; }
  .card-nome { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #2c1a0e; margin-bottom: 0.3rem; line-height: 1.2; }
  .card-genero { font-family: 'IM Fell English', serif; font-style: italic; font-size: 0.88rem; color: #6b4c1e; margin-bottom: 0.5rem; }
  .card-justificativa { font-family: 'Lato', sans-serif; font-size: 0.82rem; color: #4a3520; line-height: 1.5; border-top: 1px dashed #c4a96a; padding-top: 0.5rem; margin-top: 0.3rem; }
  .card-score { position: absolute; top: 1rem; right: 1.2rem; font-family: 'Playfair Display', serif; font-size: 0.78rem; color: #8b6914; font-style: italic; }
  .badge-colab { display: inline-block; background: #2c1a0e; color: #f5f0e8; font-family: 'Lato', sans-serif; font-size: 0.68rem; padding: 0.15rem 0.5rem; border-radius: 1px; margin-left: 0.4rem; text-transform: uppercase; }
  .badge-artista { display: inline-block; background: #8b6914; color: #f5f0e8; font-family: 'Lato', sans-serif; font-size: 0.68rem; padding: 0.15rem 0.5rem; border-radius: 1px; margin-left: 0.4rem; text-transform: uppercase; }

  .titulo-resultado { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #2c1a0e; text-align: center; margin: 1.5rem 0 0.3rem 0; }
  .subtitulo-resultado { font-family: 'IM Fell English', serif; font-style: italic; font-size: 0.9rem; color: #6b4c1e; text-align: center; margin-bottom: 1.2rem; }
  .rodape { text-align: center; font-family: 'IM Fell English', serif; font-style: italic; color: #8b6914; font-size: 0.78rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #c4a96a; opacity: 0.8; }

  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
  .card-roda { background: #ede8dc; border: 1px solid #c4a96a; border-left: 4px solid #2c1a0e; border-radius: 2px; padding: 0.9rem 1.2rem; margin-bottom: 0.8rem; }
  .roda-nome { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: #2c1a0e; }
  .roda-info { font-family: 'Lato', sans-serif; font-size: 0.82rem; color: #4a3520; line-height: 1.5; }
  .aviso { font-family: 'IM Fell English', serif; font-style: italic; font-size: 0.88rem; color: #6b4c1e; background: #f0e9d8; border: 1px dashed #c4a96a; padding: 0.7rem 1rem; margin: 0.8rem 0; }
</style>
""", unsafe_allow_html=True)

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


@st.cache_resource
def carregar():
    G, nome_id, id_nome = sc.carregar_rede(".")
    rodas = sc.carregar_rodas(".")
    rodas_art = sc.carregar_rodas_artistas(".")
    return G, nome_id, id_nome, rodas, rodas_art


def fmt_data(d):
    return f"{DIAS[d.weekday()]}, {d:%d/%m/%Y}"


def card_roda(r, extra=""):
    if r["data_calculavel"] and r["proxima_data"]:
        quando = f"próxima data: <b>{fmt_data(r['proxima_data'])}</b>"
    elif r["data_calculavel"]:
        quando = "sem data nos próximos dias"
    else:
        quando = "data a confirmar (o Mapa não permite calcular)"
    st.markdown(f"""
    <div class="card-roda">
      <div class="roda-nome">{r['roda']}</div>
      <div class="roda-info">{r['regiao'].title()} · {r['local'].title()}<br>
      {r['periodicidade'].lower()}, {r['dia'].lower()}, {r['hora']} · {quando}{extra}</div>
    </div>""", unsafe_allow_html=True)


def lista_rodas(rodas, regiao, dia, dias):
    """Rodas do Mapa (dados reais) filtradas por região, dia da semana e próximos dias."""
    out = []
    hoje = date.today()
    for _, rd in rodas.iterrows():
        if regiao and rd["regiao"] != regiao:
            continue
        if dia is not None and rd["dia_semana"] != dia:
            continue
        datas = sc.proximas_datas(rd, hoje, dias)
        if datas is not None and not datas:
            continue          # calculável e sem data na janela
        out.append(dict(roda=rd["nome"], regiao=rd["regiao"], periodicidade=rd["periodicidade"],
                        dia=rd["dia"], hora=rd["hora"], local=rd["local"],
                        proxima_data=(datas[0] if datas else None), data_calculavel=datas is not None))
    out.sort(key=lambda r: (r["proxima_data"] is None, r["proxima_data"] or date.max))
    return out


st.markdown("""
<div class="cabecalho">
  <p class="ornamento">✦ ✦ ✦</p>
  <h1 class="titulo-principal">O Samba nas Redes</h1>
  <p class="subtitulo">Um guia para descobrir e conectar o samba independente brasileiro</p>
  <p class="ornamento">— ✦ —</p>
</div>
""", unsafe_allow_html=True)

try:
    G, nome_id, id_nome, rodas, rodas_art = carregar()
except FileNotFoundError as e:
    st.error(f"Arquivo não encontrado: {e}. Coloque os CSVs *_v4 e samba_core.py na mesma pasta do app.")
    st.stop()

st.markdown('<p class="instrucao">Antes de começar, quem é você?</p>', unsafe_allow_html=True)
perfil = st.radio("Você é:", ["🎧  Ouvinte", "🎵  Artista", "📍  Rodas"], index=0,
                  horizontal=True, label_visibility="collapsed")
modo = perfil.split()[-1]

if modo == "Ouvinte":
    st.markdown("""
    <div class="modelo-explicacao"><div class="modelo-titulo">Modelo de Descoberta Musical</div>
    <div class="modelo-texto">Você escolhe um artista que já aprecia. O sistema recomenda outros artistas do
    samba independente que você provavelmente vai gostar, priorizando afinidade musical e artistas com alto
    potencial ainda não realizado. Depois, indica onde ouvir ao vivo.<br><br>
    <span class="peso-item">45% proximidade na rede (Dijkstra)</span>
    <span class="peso-item">40% similaridade musical</span>
    <span class="peso-item">15% potencial de visibilidade</span></div></div>""", unsafe_allow_html=True)
elif modo == "Artista":
    st.markdown("""
    <div class="modelo-explicacao"><div class="modelo-titulo">Modelo de Estratégia de Parceria</div>
    <div class="modelo-texto">Você escolhe seu próprio nome (ou um artista de referência). O sistema identifica
    com quem você deveria colaborar para ampliar sua visibilidade: artistas com prestígio na rede, afinidade
    musical e alcance um degrau acima do seu.<br><br>
    <span class="peso-item">35% prestígio na rede (eigenvector)</span>
    <span class="peso-item">30% similaridade musical</span>
    <span class="peso-item">20% proximidade na rede (Dijkstra)</span>
    <span class="peso-item">15% desnível de popularidade</span></div></div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="modelo-explicacao"><div class="modelo-titulo">Rodas de samba da cidade</div>
    <div class="modelo-texto">Rodas do Mapa das Rodas de Samba 2025-2 (Prefeitura do Rio), com a próxima data
    calculada pela periodicidade. Se você escolher um artista de referência e houver rodas com artistas
    confirmados, elas são ordenadas pela afinidade de estilo (e não pela popularidade).</div></div>""",
                unsafe_allow_html=True)

st.markdown('<div class="divisor">· · ·</div>', unsafe_allow_html=True)
artistas = sorted(nome_id)


def bloco_rodas(seed, chave):
    """Filtros e resultado da camada de rodas."""
    c1, c2, c3 = st.columns(3)
    regiao = c1.selectbox("Região", ["Qualquer"] + sorted(rodas["regiao"].unique()), key=f"reg{chave}")
    dia = c2.selectbox("Dia", ["Qualquer"] + [d.capitalize() for d in DIAS], key=f"dia{chave}")
    dias = c3.selectbox("Próximos", [7, 14, 30, 60], index=1, key=f"dias{chave}",
                        format_func=lambda x: f"{x} dias")
    regiao = None if regiao == "Qualquer" else regiao
    dia = None if dia == "Qualquer" else DIAS.index(dia.lower())
    if seed:
        res, aviso = sc.recomendar_rodas(G, nome_id, seed, rodas, rodas_art, n=5, regiao=regiao,
                                         dia_semana=dia, dentro_de_dias=dias)
        if res:
            st.markdown(f'<p class="titulo-resultado">Rodas de estilo parecido com o de {seed}</p>',
                        unsafe_allow_html=True)
            for r in res:
                quem = ", ".join(r["artistas_conhecidos"])
                tag = "<br><b>o artista toca nesta roda</b>" if r["artista_toca_na_roda"] else \
                      f"<br>afinidade {r['afinidade']:.3f} · artistas conhecidos: {quem}"
                card_roda(r, tag)
            return
        st.markdown(f'<div class="aviso">{aviso or "Nenhuma roda com artistas confirmados atende aos filtros."}'
                    ' Abaixo, as rodas do Mapa nos filtros escolhidos (sem ordenação por estilo).</div>',
                    unsafe_allow_html=True)
    lista = lista_rodas(rodas, regiao, dia, dias)
    st.markdown(f'<p class="subtitulo-resultado">{len(lista)} rodas encontradas</p>', unsafe_allow_html=True)
    for r in lista[:15]:
        card_roda(r)
    if len(lista) > 15:
        st.caption(f"Mostrando 15 de {len(lista)}. Use os filtros para refinar.")


if modo in ("Ouvinte", "Artista"):
    c1, c2 = st.columns([3, 1])
    seed = c1.selectbox("Artista de referência" if modo == "Ouvinte" else "Seu nome (ou artista de referência)",
                        ["— escolha —"] + artistas)
    n_rec = c2.selectbox("Quantos?", [3, 5, 8, 10], index=1)
    so_indep = st.checkbox(f"Mostrar apenas artistas independentes (popularidade ≤ {sc.POP_LIMITE_INDEP})",
                           value=True) if modo == "Ouvinte" else False
    buscar = st.button("✦  Descobrir  ✦" if modo == "Ouvinte" else "✦  Encontrar parceiros  ✦")

    if buscar and seed != "— escolha —":
        sid = nome_id[seed]
        if modo == "Ouvinte":
            st.markdown(f'<p class="titulo-resultado">Se você aprecia {seed}...</p>', unsafe_allow_html=True)
            st.markdown('<p class="subtitulo-resultado">...estes artistas merecem a sua atenção.</p>', unsafe_allow_html=True)
            for i, r in enumerate(sc.modelo_ouvinte(G, sid, n=n_rec, so_independentes=so_indep), 1):
                gen = "; ".join(sorted(G.nodes[r["node"]]["generos"]))
                badge = '<span class="badge-colab">colaboração documentada</span>' if r["tem_colaboracao"] else ""
                st.markdown(f"""<div class="card-resultado"><div class="card-score">{r['score']:.3f}</div>
                  <div class="card-numero">Nº {i}</div><div class="card-nome">{r['artista']}{badge}</div>
                  <div class="card-genero">{gen or '—'}</div>
                  <div class="card-justificativa">↳ {sc.justificativa_A(r, seed)}</div></div>""", unsafe_allow_html=True)
            st.markdown('<div class="divisor">· · ·</div>', unsafe_allow_html=True)
            st.markdown('<p class="titulo-resultado">Onde ouvir ao vivo</p>', unsafe_allow_html=True)
            bloco_rodas(seed, "ouv")
        else:
            res = sc.modelo_artista(G, sid, n=n_rec)
            if not res:
                st.warning("Nenhum parceiro encontrado. Isso ocorre quando o artista já tem popularidade alta "
                           "ou quando não há candidatos dentro dos critérios de desnível. Tente com outro artista.")
            else:
                st.markdown(f'<p class="titulo-resultado">{seed} deveria buscar parceria com...</p>', unsafe_allow_html=True)
                st.markdown('<p class="subtitulo-resultado">Artistas estratégicos para ampliar sua visibilidade na rede do samba.</p>', unsafe_allow_html=True)
                for i, r in enumerate(res, 1):
                    gen = "; ".join(sorted(G.nodes[r["node"]]["generos"]))
                    badge = '<span class="badge-colab">já colaboraram</span>' if r["tem_colaboracao"] else ""
                    pop = f'<span class="badge-artista">pop {r["pop"]} (+{r["desnivel"]})</span>'
                    st.markdown(f"""<div class="card-resultado"><div class="card-score">{r['score']:.3f}</div>
                      <div class="card-numero">Nº {i}</div><div class="card-nome">{r['artista']}{badge}{pop}</div>
                      <div class="card-genero">{gen or '—'}</div>
                      <div class="card-justificativa">↳ {sc.justificativa_B(r, seed)}</div></div>""", unsafe_allow_html=True)
    elif buscar:
        st.warning("Por favor, escolha um artista.")
else:
    ref = st.selectbox("Artista de referência (opcional)", ["— nenhum —"] + artistas)
    bloco_rodas(None if ref == "— nenhum —" else ref, "rod")

st.markdown("""
<div class="rodape">
  Trabalho de Conclusão de Curso — Engenharia de Produção, UNIRIO, 2026<br>
  Anna Luisa Fernandes Andrade Delambert<br>
  <em>O samba é de todos. A visibilidade ainda não.</em>
</div>
""", unsafe_allow_html=True)
