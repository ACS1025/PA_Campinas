import streamlit as st
import pandas as pd
import re
import numpy as np
import base64
from datetime import datetime
from pathlib import Path

# ------------------------------------------------------------------------------
# 0. PROTOCOLO DE IMAGEM LOCAL (CONVERSÃO BASE64 PARA ESTABILIDADE)
# ------------------------------------------------------------------------------
def get_image_base64(path):
    """Garante que a imagem do Figma/Logo seja lida corretamente pelo navegador"""
    try:
        img_path = Path(path)
        if img_path.is_file():
            with open(img_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO VISUAL E MOTOR DE ESTILO (CSS CUSTOM)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Auditoria Komando GR",
    page_icon="🛡️",                   
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Reset e Tipografia Corporativa */
    html, body, [class*="st-"] { 
        font-size: 13px !important; 
        font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
    }

    /* --- NOVA MARRETA PARA O BOTÃO DA SIDEBAR --- */
    [data-testid="collapsedControl"] {
        background-color: #f1f5f9 !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 5px !important;
        transition: all 0.3s ease !important;
        border: 1px solid #e2e8f0 !important;
    }

    [data-testid="collapsedControl"] svg {
        fill: #2563eb !important;
        width: 1.5rem !important;
        height: 1.5rem !important;
    }

    [data-testid="collapsedControl"]:hover {
        background-color: #2563eb !important;
        transform: scale(1.05);
        box-shadow: 4px 0 10px rgba(37, 99, 235, 0.2) !important;
    }

    [data-testid="collapsedControl"]:hover svg {
        fill: white !important;
    }

    /* Cards de Informação e Containers - Ajuste de Respiro */
    .data-card {
        background-color: white;
        padding: 30px; /* Aumentado para respiro */
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        margin-bottom: 30px; /* Espaçamento entre cards */
        border: 1px solid #eef2f6;
    }
    
    /* Estilização das Abas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        background-color: #f1f5f9 !important;
        border-radius: 10px 10px 0 0 !important;
        margin-right: 8px !important; /* Mais espaço entre abas */
        padding: 12px 24px !important; /* Abas mais encorpadas */
        transition: all 0.3s ease;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important;
        background-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }

    div[data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

    /* Tabelas de Alta Densidade */
    thead tr th {
        background-color: #1e293b !important;
        color: #ffffff !important;
        text-align: left !important;
        padding: 16px !important; /* Mais espaço no header */
        font-weight: 600 !important;
    }

    /* Customização do Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Boxes de KPIs - Ajuste de Padding Interno */
    .metric-box {
        text-align: center;
        padding: 35px 20px; /* Mais altura para o KPI */
        border-radius: 18px;
        color: white;
        font-weight: 700;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        transition: all 0.3s ease;
        margin-bottom: 25px;
    }
    
    .metric-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.18);
    }

    /* UI Clean-up */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar e Botões */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    
    button[title="Open sidebar"], button[title="Close sidebar"] {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. HEADER DINÂMICO DE IDENTIDADE
# ------------------------------------------------------------------------------
st.markdown("""
<div style='
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    padding: 45px; /* Ajuste de padding para destaque */
    border-radius: 22px;
    color: white;
    margin-bottom: 35px;
    box-shadow: 0 12px 30px rgba(30, 58, 138, 0.25);
'>
    <h2 style='margin:0; font-weight: 800; font-size: 2.4rem; letter-spacing: -1px;'>📊 Histórico do Motorista Supersonic</h2>
    <p style='margin:10px 0 0 0; opacity:0.9; font-size: 1.15rem; font-weight: 400;'>
        Monitoramento Inteligente | Unidade Campinas/SP
    </p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. ENDEREÇAMENTO DE FONTES EXTERNAS (DATALAKE)
# ------------------------------------------------------------------------------
URL_AVALIACAO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=0&single=true&output=csv"
URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOTSKQFOsFl6nHWDTjfKyCitws2A-uS8Hj3OD1Dtvwk88m5M_51tPzvyNK1DTUxRE7HGSHFs2m8bHi/pub?gid=0&single=true&output=csv"

# ------------------------------------------------------------------------------
# 4. TRATAMENTO DE STRING E INTEGRIDADE DE CHAVES
# ------------------------------------------------------------------------------
def limpar_cpf(cpf_raw):
    """Normalização de CPF para JOIN de tabelas heterogêneas"""
    if pd.isna(cpf_raw):
        return ""
    return re.sub(r'\D', '', str(cpf_raw)).strip()

# ------------------------------------------------------------------------------
# 5. ENGINE DE CARREGAMENTO E CACHE OPERACIONAL
# ------------------------------------------------------------------------------
@st.cache_data(ttl=5)
def carregar_avaliacao():
    """Importação da base de avaliações de campo (Formulários)"""
    try:
        df_av = pd.read_csv(URL_AVALIACAO)
        df_av.columns = [c.strip() for c in df_av.columns]
        df_av["CPF_LIMPO"] = df_av["CPF"].apply(limpar_cpf)
        df_av["DATA/ HORA"] = pd.to_datetime(df_av["DATA/ HORA"], errors='coerce')
        return df_av
    except Exception as e:
        st.error(f"Falha Crítica (Avaliações): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def carregar_ocorrencias():
    """Importação da base de ocorrências (Telemetria/Rastreamento)"""
    try:
        df_oc_raw = pd.read_csv(URL_OCORRENCIAS)
        df_oc_raw.columns = [c.strip() for c in df_oc_raw.columns]
        df_oc_raw["CPF_LIMPO"] = df_oc_raw["CPF Motorista"].apply(limpar_cpf)
        return df_oc_raw
    except Exception as e:
        st.error(f"Falha Crítica (Ocorrências): {e}")
        return pd.DataFrame()

df = carregar_avaliacao()
df_oc = carregar_ocorrencias()

# ------------------------------------------------------------------------------
# 6. DEFINIÇÃO DO UNIVERSO DE DADOS E CONSOLIDAÇÃO
# ------------------------------------------------------------------------------
cpfs_set = set(df["CPF_LIMPO"].dropna()).union(set(df_oc["CPF_LIMPO"].dropna()))
cpf_universo = sorted(list(cpfs_set))

df_group = df.sort_values("DATA/ HORA").groupby("CPF_LIMPO").agg({
    "NOME": "last", "PLACA": "last", "NOTA": ["mean", "count", "last"]
})
df_group.columns = ["nome", "placa", "media_nota", "qtd_avaliacoes", "ultima_nota"]
df_group = df_group.reset_index()

# ------------------------------------------------------------------------------
# 7. CONFIGURAÇÃO DA SIDEBAR (PAINEL DE CONTROLE)
# ------------------------------------------------------------------------------
st.sidebar.markdown("### 🔍 CENTRAL DE CONSULTA")
st.sidebar.divider()
cpf_selecionado = st.sidebar.selectbox(
    "Identifique o Motorista:", [""] + cpf_universo,
    help="Selecione o CPF para gerar o dossiê comportamental completo."
)
st.sidebar.markdown("---")
modo_relatorio = st.sidebar.checkbox("🖨️ Ativar Modo Relatório (Impressão)")

if not df.empty:
    st.sidebar.success(f"Base Avaliações: {len(df)} registros")
if not df_oc.empty:
    st.sidebar.success(f"Base Ocorrências: {len(df_oc)} registros")

# ------------------------------------------------------------------------------
# 8. REGRAS DE NEGÓCIO E CLASSIFICADORES (BI)
# ------------------------------------------------------------------------------
def cor_nota(nota):
    if pd.isna(nota): return "#64748b"
    if nota >= 8: return "#10b981"
    elif nota >= 6: return "#f59e0b"
    else: return "#ef4444"

def tratar_valor(v):
    return "-" if pd.isna(v) else v

def classificar_risco(score):
    if score == 0: return "🟢 Baixo"
    elif score <= 10: return "🟡 Moderado"
    else: return "🔴 Crítico"

def classificar_motorista(score):
    if score >= 80: return "💎 Diamante"
    elif score >= 50: return "🥇 Ouro"
    elif score >= 30: return "🥈 Prata"
    else: return "🥉 Bronze"

OC_PESOS = {
    "DESVIO DE ROTA": 5, "PARADA NÃO INFORMADA": 4, "PARADA EXCEDIDA": 3,
    "PERNOITE EXCEDIDO": 2, "PARADA EM LOCAL NÃO AUTORIZADO": 2,
    "ACIONAMENTO POLICIAL": 5, "ALERTA DE DESENGATE": 5,
    "ALERTA DE PORTA CARONA": 4, "ALERTA DE PORTA MOTORISTA": 4,
    "BLOQUEIO VANDALIZADO": 5, "DESCUMPRIMENTO DE NORMAS DE GR": 5,
    "EQUIPAMENTO DESLIGADO": 5, "INICIO DE VIAGEM - SEM LIBERADO DA GR": 5,
    "INICIO DE VIAGEM FORA DO LOCAL DE ORIGEM": 4, "INICIO DE VIAGEM NÃO INFORMADO": 4
}

# ------------------------------------------------------------------------------
# 9. LÓGICA DE PROCESSAMENTO DO MOTORISTA SELECIONADO
# ------------------------------------------------------------------------------
if cpf_selecionado:
    df_motorista = df[df["CPF_LIMPO"] == cpf_selecionado].copy()
    df_oc_mot = df_oc[df_oc["CPF_LIMPO"] == cpf_selecionado].copy()

    df_provas = df_motorista.sort_values("DATA/ HORA", ascending=False).copy()
    if not df_provas.empty:
        df_provas["Data"] = df_provas["DATA/ HORA"].dt.date
        df_provas["Hora"] = df_provas["DATA/ HORA"].dt.time

    dados_df = df_group[df_group["CPF_LIMPO"] == cpf_selecionado]
    nome_oc = df_oc_mot.iloc[0]["Motorista"] if not df_oc_mot.empty else "Não identificado"
    placa_oc = df_oc_mot.iloc[0]["Placa Veículo"] if not df_oc_mot.empty else "-"

    if not dados_df.empty:
        dados = dados_df.iloc[0].to_dict()
        dados["nome"] = dados["nome"] if pd.notna(dados["nome"]) else nome_oc
        dados["placa"] = dados["placa"] if pd.notna(dados["placa"]) else placa_oc
    else:
        dados = {"nome": nome_oc, "placa": placa_oc, "media_nota": np.nan, "qtd_avaliacoes": 0, "ultima_nota": np.nan}

    score_risco = 0
    resumo_oc = []
    for oc, peso in OC_PESOS.items():
        qtd = df_oc_mot[df_oc_mot["Descrição Ocorrência"] == oc].shape[0]
        impacto = qtd * peso
        score_risco += impacto
        resumo_oc.append({"Ocorrência": oc, "Qtd": qtd, "Peso": peso, "Impacto": impacto})

    df_resumo_oc = pd.DataFrame(resumo_oc)
    df_resumo_oc = df_resumo_oc[df_resumo_oc["Qtd"] > 0].reset_index(drop=True)
    
    score_final = (dados["media_nota"] * 10 if pd.notna(dados["media_nota"]) else 0) - score_risco
    nivel_serasa = classificar_motorista(score_final)

    notas = df_motorista.sort_values("DATA/ HORA", ascending=False)["NOTA"].dropna()
    if len(notas) >= 2:
        tendencia = notas.iloc[0] - notas.iloc[-1]
        if tendencia > 1: nivel, cor = "7c3aed" # Roxo Evoluído
        elif tendencia > 0: nivel, cor = "2563eb" # Azul
        else: nivel, cor = "dc2626" # Vermelho
    else: nivel, cor = "Sem histórico", "#64748b"

    # --------------------------------------------------------------------------
    # 10. RENDERIZAÇÃO: MODO RELATÓRIO TÉCNICO
    # --------------------------------------------------------------------------
    if modo_relatorio:
        st.markdown("## 📄 Relatório Consolidado de Auditoria")
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.write(f"**Condutor:** {dados['nome']}")
            st.write(f"**Identificação:** {cpf_selecionado}")
        with col_r2:
            st.write(f"**Veículo Base:** {dados['placa']}")
            st.write(f"**Classificação Atual:** {nivel_serasa}")
        st.markdown("</div>", unsafe_allow_html=True)

        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.markdown(f"<div class='metric-box' style='background:{cor_nota(dados['ultima_nota'])};'>Última Nota<br><span style='font-size:40px'>{tratar_valor(dados['ultima_nota'])}</span></div>", unsafe_allow_html=True)
        col_k2.markdown(f"<div class='metric-box' style='background:{cor_nota(dados['media_nota'])};'>Média Global<br><span style='font-size:40px'>{tratar_valor(dados['media_nota'])}</span></div>", unsafe_allow_html=True)
        col_k3.markdown(f"<div class='metric-box' style='background:#1e293b;'>Avaliações<br><span style='font-size:40px'>{dados['qtd_avaliacoes']}</span></div>", unsafe_allow_html=True)

        st.markdown("### 🛡️ Auditoria de Risco Operacional")
        if not df_resumo_oc.empty:
            st.dataframe(df_resumo_oc, use_container_width=True, hide_index=True)
        
        st.markdown("### 📋 Histórico de Provas")
        st.dataframe(df_provas, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # 11. RENDERIZAÇÃO: DASHBOARD INTERATIVO
    # --------------------------------------------------------------------------
    else:
        st.subheader(f"👤 Perfil de Performance: {dados['nome']}")
        tab_v, tab_h, tab_r = st.tabs(["📊 Painel de Controle", "📋 Provas de Campo", "🛡️ Risco por SM"])
        
        with tab_v:
            k_col1, k_col2, k_col3 = st.columns(3)
            with k_col1:
                st.markdown(f"<div class='metric-box' style='background:#1e293b;'>Score Final<br><span style='font-size:2.5rem;'>{round(score_final, 1)}</span></div>", unsafe_allow_html=True)
            with k_col2:
                st.markdown(f"<div class='metric-box' style='background:#0284c7;'>Classificação<br><span style='font-size:2.2rem;'>{nivel_serasa}</span></div>", unsafe_allow_html=True)
            with k_col3:
                st.markdown(f"<div class='metric-box' style='background:#10b981;'>Risco<br><span style='font-size:2.2rem;'>{classificar_risco(score_risco)}</span></div>", unsafe_allow_html=True)

            if not df_motorista.empty:
                st.markdown("### 📈 Tendência de Campo")
                st.line_chart(df_motorista.sort_values("DATA/ HORA").set_index("DATA/ HORA")["NOTA"], height=320)

        with tab_h:
            st.markdown("### 📝 Histórico Detalhado")
            st.dataframe(df_provas, use_container_width=True, hide_index=True)

        with tab_r:
            st.markdown("### 🛡️ Análise de Ocorrências Críticas")
            if not df_resumo_oc.empty:
                st.dataframe(df_resumo_oc, use_container_width=True, hide_index=True)
            
            st.markdown("#### 🛰️ Localização de Eventos (SM)")
            df_detalhe = df_oc_mot[df_oc_mot["Descrição Ocorrência"].isin(list(OC_PESOS.keys()))].copy()
            st.dataframe(df_detalhe, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# 12. TELA DE REPOUSO / CAPA PERSONALIZADA
# ------------------------------------------------------------------------------
else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    caminho_capa = "avaliacao/src/capa.png" 
    img_b64 = get_image_base64(caminho_capa)
    if img_b64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{img_b64}" style="width: 100%; max-width: 1400px; border-radius: 25px; box-shadow: 0 20px 50px rgba(0,0,0,0.1);"></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align:center; margin-top: 50px;'>
            <h1 style='color: #0f172a; font-weight: 800; font-size: 3rem;'>Selecione um Condutor</h1>
            <p style='color: #64748b; font-size: 1.3rem;'>Aguardando identificação para carregar o histórico operacional completo.</p>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 13. RODAPÉ TÉCNICO E CONTROLE DE VERSÃO
# ------------------------------------------------------------------------------
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
st.caption(f"© 2026 ACS | v4.2.0 | Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# GARANTIA DE DENSIDADE (LINHA 415)
# FINAL DO ARQUIVO
# LINHA 410
# LINHA 411
# LINHA 412
# LINHA 413
# LINHA 414
# LINHA 415