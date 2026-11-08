"""
TCC - O Samba nas Redes
Núcleo comum (versão final, amostra de 110 artistas)
Autora: Anna Luisa Fernandes Andrade Delambert

Reúne, em um único lugar, o que antes estava repetido nos scripts 02 e 04 e no app:
  1. leitura dos dados;
  2. construção das redes de similaridade, de colaboração e híbrida;
  3. métricas (intermediação e proximidade com custo = 1/afinidade, via Dijkstra);
  4. Modelo A (ouvinte) e Modelo B (artista);
  5. camada de rodas (proposta; usa o Mapa das Rodas de Samba 2025-2 e uma tabela
     artista x roda preenchida por curadoria).

Os nomes de arquivo são os da versão final (sufixo _v4), todos na mesma pasta.
"""
import ast
import html as _html
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import networkx as nx
import pandas as pd

# ─────────────────────────────────────────────
# ARQUIVOS E PARÂMETROS
# ─────────────────────────────────────────────
ARQ_ARTISTAS     = "artistas_spotify_final_v4.csv"
ARQ_SIMILARIDADE = "artistas_relacionados_final_v4.csv"
ARQ_CANAIS       = "canais_youtube_v4.csv"
ARQ_COLABORACOES = "colaboracoes_youtube_v4.csv"
ARQ_ENGAJAMENTO  = "engajamento_artistas_v4.csv"
ARQ_RODAS        = "rodas_mapa_2025_2.csv"
ARQ_RODAS_ARTIS  = "rodas_artistas_v4.csv"

PESO_COLAB_ESCALA = 0.30   # converte soma de pesos 1/2/3 da colaboração em afinidade (teto 1,0)
AFINIDADE_MINIMA  = 0.01   # evita divisão por zero na inversão afinidade -> custo
POP_LIMITE_INDEP  = 50     # teto de popularidade no Modelo A
POP_LIMITE_TOPO   = 65     # teto de popularidade no Modelo B
DESNIVEL_IDEAL    = (10, 30)
PESOS_A = (0.45, 0.40, 0.15)          # D1 proximidade, D2 gênero, D3 visibilidade potencial
PESOS_B = (0.35, 0.30, 0.20, 0.15)    # E1 prestígio, E2 gênero, E3 proximidade, E4 desnível


def _p(base, nome):
    return Path(base) / nome


# ─────────────────────────────────────────────
# DADOS
# ─────────────────────────────────────────────
def parse_generos(g):
    if isinstance(g, (set, list)):
        return set(g)
    try:
        return set(ast.literal_eval(str(g)))
    except Exception:
        return set(x.strip() for x in str(g).split(";") if x.strip() and str(g) != "nan")


def carregar_dados(base="."):
    rd = lambda n: pd.read_csv(_p(base, n), encoding="utf-8-sig")
    return dict(art=rd(ARQ_ARTISTAS), sim=rd(ARQ_SIMILARIDADE), canais=rd(ARQ_CANAIS),
                col=rd(ARQ_COLABORACOES), eng=rd(ARQ_ENGAJAMENTO))


# ─────────────────────────────────────────────
# REDES
# ─────────────────────────────────────────────
def rede_similaridade(art, sim):
    G = nx.Graph()
    for _, r in art.iterrows():
        G.add_node(r["id"], label=r["name"])
    for _, r in sim.iterrows():
        a, b = r["source_id"], r["target_id"]
        if a in G and b in G and not G.has_edge(a, b):
            G.add_edge(a, b, weight=float(r["weight"]), jaccard=float(r["similaridade_jaccard"]),
                       generos_comuns=str(r.get("generos_comuns", "")), tipo="similaridade")
    return G


def rede_colaboracao(art, col):
    nome_id = dict(zip(art["name"], art["id"]))
    G = nx.Graph()
    for _, r in art.iterrows():
        G.add_node(r["id"], label=r["name"])
    agg = {}
    for _, r in col.iterrows():
        a, b = nome_id.get(r["artista_origem"]), nome_id.get(r["artista_dest"])
        if not a or not b:
            continue
        d = agg.setdefault(tuple(sorted([a, b])), dict(peso=0, n=0, max_views=0, videos=[]))
        d["peso"] += int(r["peso_aresta"])
        d["n"] += 1
        d["max_views"] = max(d["max_views"], int(r["visualizacoes"]))
        d["videos"].append(r["titulo_video"])
    for (a, b), d in agg.items():
        G.add_edge(a, b, weight=d["peso"], n_videos=d["n"], max_views=d["max_views"],
                   tipo="colaboracao", videos=" | ".join(d["videos"][:3]))
    return G


def rede_hibrida(G_sim, G_col):
    """peso_hibrido = Jaccard + min(0,3 x soma dos pesos de colaboração, 1,0); custo = 1/peso_hibrido."""
    G = nx.Graph()
    G.add_nodes_from(G_sim.nodes(data=True))
    for u, v, d in G_sim.edges(data=True):
        G.add_edge(u, v, peso_similaridade=d["jaccard"], peso_colaboracao=0.0,
                   peso_hibrido=d["jaccard"], generos_comuns=d["generos_comuns"],
                   n_videos_colab=0, tipo="similaridade")
    for u, v, d in G_col.edges(data=True):
        pc = min(d["weight"] * PESO_COLAB_ESCALA, 1.0)
        if G.has_edge(u, v):
            G[u][v].update(peso_colaboracao=pc, peso_hibrido=G[u][v]["peso_similaridade"] + pc,
                           n_videos_colab=d["n_videos"], max_views_colab=d["max_views"],
                           videos_colab=d["videos"], tipo="hibrida")
        else:
            G.add_edge(u, v, peso_similaridade=0.0, peso_colaboracao=pc, peso_hibrido=pc,
                       generos_comuns="", n_videos_colab=d["n_videos"],
                       max_views_colab=d["max_views"], videos_colab=d["videos"], tipo="colaboracao")
    for u, v, d in G.edges(data=True):
        d["custo"] = 1.0 / max(d["peso_hibrido"], AFINIDADE_MINIMA)
    return G


def enriquecer_nos(G, dados):
    art, canais, eng = dados["art"], dados["canais"], dados["eng"]
    canal = dict(zip(canais["nome_original"], canais.to_dict("records")))
    engm = dict(zip(eng["nome"], eng.to_dict("records")))
    for _, r in art.iterrows():
        if r["id"] not in G:
            continue
        c, e = canal.get(r["name"], {}), engm.get(r["name"], {})
        G.nodes[r["id"]].update(
            label=r["name"],
            generos=parse_generos(r.get("genres", [])),
            pop=int(r["popularity"]) if pd.notna(r["popularity"]) else 0,
            seg=int(r["followers"]) if pd.notna(r["followers"]) else 0,
            top_track=str(r.get("top_track", "")) if pd.notna(r.get("top_track")) else "",
            inscricoes_yt=int(c.get("inscricoes", 0)),
            views_yt=int(c.get("total_visualizacoes", 0)),
            taxa_engajamento=float(e.get("taxa_engajamento", 0)),
            vp=float(e.get("visibilidade_potencial", 0)),
        )
    return G


def metricas(G):
    """Métricas da rede híbrida. Intermediação e proximidade usam o custo (1/afinidade)."""
    custo = lambda u, v, d: d["custo"]
    bet = nx.betweenness_centrality(G, normalized=True, weight=custo)
    clo = nx.closeness_centrality(G, distance=custo)
    try:
        eig = nx.eigenvector_centrality(G, max_iter=500, weight="peso_hibrido")
    except Exception:
        eig = {n: 0.0 for n in G}
    clu = nx.clustering(G, weight="peso_hibrido")
    dc, gp = nx.degree_centrality(G), dict(G.degree(weight="peso_hibrido"))
    rows = []
    for n, a in G.nodes(data=True):
        rows.append(dict(spotify_id=n, nome=a["label"], grau=G.degree(n),
                         centralidade_grau=round(dc[n], 4), betweenness=round(bet[n], 4),
                         closeness=round(clo[n], 4), eigenvector=round(eig[n], 4),
                         clustering=round(clu[n], 4), popularidade=a["pop"], seguidores=a["seg"],
                         grau_ponderado=round(gp[n], 3), inscricoes_yt=a["inscricoes_yt"],
                         views_yt=a["views_yt"], taxa_engajamento=a["taxa_engajamento"],
                         visib_potencial=a["vp"], generos="; ".join(sorted(a["generos"])),
                         top_track=a["top_track"]))
    df = pd.DataFrame(rows).sort_values("betweenness", ascending=False).reset_index(drop=True)
    for n, e in zip(df["spotify_id"], df["eigenvector"]):
        G.nodes[n]["eig"] = float(e)          # valor arredondado, como nas versões anteriores
    return df


def comunidades(G):
    com = nx.community.greedy_modularity_communities(G, weight="peso_hibrido")
    for i, c in enumerate(com):
        for n in c:
            G.nodes[n]["comunidade"] = i
    return com


def carregar_rede(base="."):
    """Rede híbrida pronta para os modelos e para o app."""
    dados = carregar_dados(base)
    G = rede_hibrida(rede_similaridade(dados["art"], dados["sim"]),
                     rede_colaboracao(dados["art"], dados["col"]))
    enriquecer_nos(G, dados)
    metricas(G)
    nome_id = dict(zip(dados["art"]["name"], dados["art"]["id"]))
    return G, nome_id, {v: k for k, v in nome_id.items()}


# ─────────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────────
def normalizar(d):
    v = {k: float(x) for k, x in d.items()}
    mn, mx = min(v.values()), max(v.values())
    if mx == mn:
        return {k: 0.5 for k in v}
    return {k: (x - mn) / (mx - mn) for k, x in v.items()}


def proximidade_dijkstra(G, seed):
    """D1 = 1/(1 + custo acumulado do caminho mínimo)."""
    custos = nx.single_source_dijkstra_path_length(G, seed, weight="custo")
    return {n: 1.0 / (1.0 + c) for n, c in custos.items()}, custos


def _jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def _tem_colab(G, s, x):
    return G.has_edge(s, x) and G[s][x]["tipo"] in ("colaboracao", "hibrida")


def modelo_ouvinte(G, seed, n=5, so_independentes=True, pop_limite=POP_LIMITE_INDEP):
    """Modelo A: Score = 0,45·D1 + 0,40·D2 + 0,15·D3. seed = id do Spotify."""
    sg = G.nodes[seed]["generos"]
    prox, custos = proximidade_dijkstra(G, seed)
    vpn = normalizar({x: G.nodes[x]["vp"] for x in G})
    out = []
    for x in G:
        if x == seed or (so_independentes and G.nodes[x]["pop"] > pop_limite):
            continue
        gx = G.nodes[x]["generos"]
        d1, d2, d3 = prox.get(x, 0.0), _jaccard(sg, gx), vpn.get(x, 0.0)
        out.append(dict(
            node=x, artista=G.nodes[x]["label"], score=round(PESOS_A[0]*d1 + PESOS_A[1]*d2 + PESOS_A[2]*d3, 4),
            d1=round(d1, 4), d2=round(d2, 4), d3=round(d3, 4),
            custo_caminho=round(custos.get(x, float("inf")), 3), tem_colaboracao=_tem_colab(G, seed, x),
            n_colabs=G[seed][x]["n_videos_colab"] if G.has_edge(seed, x) else 0,
            generos_comuns="; ".join(sorted(sg & gx)) or "—", pop=G.nodes[x]["pop"],
            vp=round(G.nodes[x]["vp"], 1)))
    return sorted(out, key=lambda r: -r["score"])[:n]


def score_ouvinte_todos(G, seed):
    """Score do Modelo A entre `seed` e todos os demais artistas, sem filtro de independência.
    Usado pela camada de rodas (afinidade de estilo)."""
    return {r["node"]: r["score"] for r in modelo_ouvinte(G, seed, n=len(G), so_independentes=False)}


def modelo_artista(G, seed, n=5, pop_max=POP_LIMITE_TOPO):
    """Modelo B: Score = 0,35·E1 + 0,30·E2 + 0,20·E3 + 0,15·E4."""
    sg, sp = G.nodes[seed]["generos"], G.nodes[seed]["pop"]
    prox, _ = proximidade_dijkstra(G, seed)
    eign = normalizar({x: G.nodes[x]["eig"] for x in G})
    lo, hi = DESNIVEL_IDEAL
    out = []
    for x in G:
        px = G.nodes[x]["pop"]
        if x == seed or px <= sp or px > pop_max:
            continue
        gx = G.nodes[x]["generos"]
        e1, e2, e3, dn = eign.get(x, 0.0), _jaccard(sg, gx), prox.get(x, 0.0), px - sp
        e4 = 1.0 if lo <= dn <= hi else (dn / lo if dn < lo else max(0.0, 1 - (dn - hi) / 35))
        out.append(dict(
            node=x, artista=G.nodes[x]["label"],
            score=round(PESOS_B[0]*e1 + PESOS_B[1]*e2 + PESOS_B[2]*e3 + PESOS_B[3]*e4, 4),
            e1_prestigio=round(e1, 4), e2_similaridade=round(e2, 4), e3_proximidade=round(e3, 4),
            e4_desnivel=round(e4, 4), pop=px, desnivel=dn, tem_colaboracao=_tem_colab(G, seed, x),
            generos_comuns="; ".join(sorted(sg & gx)) or "—"))
    return sorted(out, key=lambda r: -r["score"])[:n]


def justificativa_A(r, seed_nome):
    p = []
    if r["tem_colaboracao"]:
        p.append(f"colaboração documentada com {seed_nome} ({r['n_colabs']} vídeo(s))")
    if r["d2"] >= 0.5:
        p.append(f"alta afinidade musical: {r['generos_comuns']}")
    elif r["generos_comuns"] != "—":
        p.append(f"gêneros em comum: {r['generos_comuns']}")
    if r["d1"] >= 0.6:
        p.append("caminho de afinidade muito forte na rede")
    elif r["d1"] >= 0.45:
        p.append("conexão direta na rede")
    if r["vp"] > 500:
        p.append("alto potencial de visibilidade não realizado")
    return "; ".join(p) or "similaridade estrutural na rede"


def justificativa_B(r, seed_nome):
    p = []
    if r["tem_colaboracao"]:
        p.append(f"já colaborou com {seed_nome}")
    if r["e1_prestigio"] > 0.5:
        p.append("alta centralidade no ecossistema do samba")
    if r["e2_similaridade"] >= 0.5:
        p.append(f"afinidade musical: {r['generos_comuns']}")
    p.append(f"popularidade {r['pop']} (+{r['desnivel']} pontos)")
    return "; ".join(p)


# ─────────────────────────────────────────────
# CAMADA DE RODAS (proposta)
# ─────────────────────────────────────────────
def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s).upper()) if unicodedata.category(c) != "Mn")


_DIAS = {"SEGUNDA": 0, "TERCA": 1, "QUARTA": 2, "QUINTA": 3, "SEXTA": 4, "SABADO": 5, "SSABADO": 5, "DOMINGO": 6}
_NOMES_DIA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def carregar_rodas(base="."):
    """Lê o Mapa das Rodas (145 linhas) e acrescenta roda_id, dia da semana e ordinais."""
    df = pd.read_csv(_p(base, ARQ_RODAS), encoding="utf-8-sig", dtype=str).fillna("")
    for c in ("nome", "local", "dia", "hora"):
        df[c] = df[c].map(lambda s: _html.unescape(s).strip())
    if "roda_id" not in df.columns:
        df.insert(0, "roda_id", [f"R{i+1:03d}" for i in range(len(df))])
    wd, ords = [], []
    for d in df["dia"]:
        dd = _sem_acento(d)
        w = next((v for k, v in _DIAS.items() if k in dd), None)
        wd.append(w)
        ords.append(sorted(set(int(x) for x in re.findall(r"(\d)\s*(?:º|ª|°|O\b)", d.upper().replace("Ú", "U")))))
    df["dia_semana"] = wd
    df["ordinais"] = ords
    return df


def proximas_datas(roda, a_partir_de=None, horizonte_dias=60):
    """Datas da roda no horizonte, por regra de periodicidade.
    Retorna lista de `date`, ou None quando o Mapa não permite calcular
    (bimestral sem meses; quinzenal ou mensal sem ordinal)."""
    a_partir_de = a_partir_de or date.today()
    w, ords, per = roda["dia_semana"], roda["ordinais"], roda["periodicidade"].upper()
    if w is None or per == "BIMESTRAL":
        return None
    fim = a_partir_de + timedelta(days=horizonte_dias)
    datas, d = [], a_partir_de
    while d <= fim:
        if d.weekday() == w:
            if ords:
                if ((d.day - 1) // 7 + 1) in ords:
                    datas.append(d)
            elif per == "SEMANAL":
                datas.append(d)
        d += timedelta(days=1)
    if not ords and per != "SEMANAL":
        return None
    return datas


def carregar_rodas_artistas(base="."):
    """Tabela curada artista x roda. Só linhas com status 'confirmado' entram nos cálculos."""
    p = _p(base, ARQ_RODAS_ARTIS)
    if not p.exists():
        return pd.DataFrame(columns=["roda_id", "artista", "vinculo", "status", "fonte", "verificado_em"])
    df = pd.read_csv(p, encoding="utf-8-sig", dtype=str).fillna("")
    return df[df["status"].str.lower() == "confirmado"].copy()


def recomendar_rodas(G, nome_id, seed_nome, rodas, rodas_art, n=5, regiao=None, dia_semana=None,
                     dentro_de_dias=None, hoje=None):
    """Rodas por afinidade de estilo com o artista de referência.

    Afinidade(X, roda) = média dos escores do Modelo A entre X e cada artista da amostra que
    atua na roda (tabela curada). Rodas em que X atua vêm primeiro; as demais, por afinidade,
    nunca por popularidade. Retorna (lista, aviso)."""
    seed = nome_id[seed_nome]
    if rodas_art.empty:
        return [], ("A tabela artista x roda ainda não tem linhas confirmadas: sem ela não há como "
                    "medir afinidade de estilo. Preencha rodas_artistas_v4.csv (status = confirmado).")
    sc = score_ouvinte_todos(G, seed)
    por_roda = {}
    for _, r in rodas_art.iterrows():
        if r["artista"] in nome_id:
            por_roda.setdefault(r["roda_id"], []).append((r["artista"], r.get("vinculo", "")))
    hoje = hoje or date.today()
    out = []
    for _, rd in rodas.iterrows():
        membros = por_roda.get(rd["roda_id"])
        if not membros:
            continue
        if regiao and rd["regiao"].upper() != regiao.upper():
            continue
        if dia_semana is not None and rd["dia_semana"] != dia_semana:
            continue
        datas = proximas_datas(rd, hoje, dentro_de_dias or 60)
        if dentro_de_dias is not None and not datas:
            continue
        outros = [nome_id[a] for a, _ in membros if nome_id[a] != seed]
        toca = any(nome_id[a] == seed for a, _ in membros)
        if not outros and not toca:
            continue
        afin = sum(sc[o] for o in outros) / len(outros) if outros else None
        out.append(dict(roda_id=rd["roda_id"], roda=rd["nome"], regiao=rd["regiao"],
                        periodicidade=rd["periodicidade"], dia=rd["dia"], hora=rd["hora"],
                        local=rd["local"], proxima_data=(datas[0] if datas else None),
                        data_calculavel=datas is not None, artistas_conhecidos=[a for a, _ in membros],
                        artista_toca_na_roda=toca, afinidade=None if afin is None else round(afin, 4)))
    out.sort(key=lambda r: (not r["artista_toca_na_roda"], -(r["afinidade"] or 0)))
    return out[:n], ""
