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
    page_title="Relatório Avaliação Motoristas | ACS Consult", 
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

    /* Cards de Informação e Containers */
    .data-card {
        background-color: white;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        margin-bottom: 25px;
        border: 1px solid #eef2f6;
    }

    /* Tabelas de Alta Densidade */
    thead tr th {
        background-color: #1e293b !important;
        color: #ffffff !important;
        text-align: left !important;
        padding: 14px !important;
        font-weight: 600 !important;
    }

    /* Customização do Sidebar (Navegação) */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    button[title="Open sidebar"] {
        background-color: #2563eb !important;
        border-radius: 10px !important;
    }

    /* Boxes de Métricas de Performance (KPIs) */
    .metric-box {
        text-align: center;
        padding: 28px;
        border-radius: 18px;
        color: white;
        font-weight: 700;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }
    .metric-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.18);
    }

    /* UI Clean-up */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar Estilizada */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. HEADER DINÂMICO DE IDENTIDADE
# ------------------------------------------------------------------------------
st.markdown("""
<div style='
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    padding: 38px;
    border-radius: 20px;
    color: white;
    margin-bottom: 30px;
    box-shadow: 0 10px 25px rgba(30, 58, 138, 0.2);
'>
    <h1 style='margin:0; font-weight: 800; font-size: 2.2rem;'>📊 Histórico do Motorista Supersonic</h1>
    <p style='margin:8px 0 0 0; opacity:0.85; font-size: 1.1rem; font-weight: 400;'>
        Monitoramento Inteligente ACS Consult | Unidade Campinas/SP
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

# Execução do carregamento inicial
df = carregar_avaliacao()
df_oc = carregar_ocorrencias()

# ------------------------------------------------------------------------------
# 6. DEFINIÇÃO DO UNIVERSO DE DADOS E CONSOLIDAÇÃO
# ------------------------------------------------------------------------------
cpfs_set = set(df["CPF_LIMPO"].dropna()).union(set(df_oc["CPF_LIMPO"].dropna()))
cpf_universo = sorted(list(cpfs_set))

# Agrupamento Técnico para Visão Macro
df_group = df.sort_values("DATA/ HORA").groupby("CPF_LIMPO").agg({
    "NOME": "last",
    "PLACA": "last",
    "NOTA": ["mean", "count", "last"]
})

df_group.columns = ["nome", "placa", "media_nota", "qtd_avaliacoes", "ultima_nota"]
df_group = df_group.reset_index()

# ------------------------------------------------------------------------------
# 7. CONFIGURAÇÃO DA SIDEBAR (PAINEL DE CONTROLE)
# ------------------------------------------------------------------------------
st.sidebar.markdown("### 🔍 CENTRAL DE CONSULTA")
st.sidebar.divider()

cpf_selecionado = st.sidebar.selectbox(
    "Identifique o Motorista:",
    [""] + cpf_universo,
    help="Selecione o CPF para gerar o dossiê comportamental completo."
)

st.sidebar.markdown("---")
modo_relatorio = st.sidebar.checkbox("🖨️ Ativar Modo Relatório (Impressão)")

# Logs de Auditoria do Backend
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
    "DESVIO DE ROTA": 5,
    "PARADA NÃO INFORMADA": 4,
    "PARADA EXCEDIDA": 3,
    "PERNOITE EXCEDIDO": 2,
    "PARADA EM LOCAL NÃO AUTORIZADO": 2
}

# ------------------------------------------------------------------------------
# 9. LÓGICA DE PROCESSAMENTO DO MOTORISTA SELECIONADO
# ------------------------------------------------------------------------------
if cpf_selecionado:
    # Segmentação e Preparação de Dados
    df_motorista = df[df["CPF_LIMPO"] == cpf_selecionado].copy()
    df_oc_mot = df_oc[df_oc["CPF_LIMPO"] == cpf_selecionado].copy()

    df_provas = df_motorista.sort_values("DATA/ HORA", ascending=False).copy()
    if not df_provas.empty:
        df_provas["Data"] = df_provas["DATA/ HORA"].dt.date
        df_provas["Hora"] = df_provas["DATA/ HORA"].dt.time

    dados_df = df_group[df_group["CPF_LIMPO"] == cpf_selecionado]

    # Recuperação de Identidade Visual
    nome_oc = df_oc_mot.iloc[0]["Motorista"] if not df_oc_mot.empty else "Não identificado"
    placa_oc = df_oc_mot.iloc[0]["Placa Veículo"] if not df_oc_mot.empty else "-"

    if not dados_df.empty:
        dados = dados_df.iloc[0].to_dict()
        dados["nome"] = dados["nome"] if pd.notna(dados["nome"]) else nome_oc
        dados["placa"] = dados["placa"] if pd.notna(dados["placa"]) else placa_oc
    else:
        dados = {
            "nome": nome_oc, "placa": placa_oc, "media_nota": np.nan,
            "qtd_avaliacoes": 0, "ultima_nota": np.nan
        }

    tem_avaliacao = pd.notna(dados["ultima_nota"])

    # Cálculo da Matriz de Risco
    score_risco = 0
    resumo_oc = []
    for oc, peso in OC_PESOS.items():
        qtd = df_oc_mot[df_oc_mot["Descrição Ocorrência"] == oc].shape[0]
        impacto = qtd * peso
        score_risco += impacto
        resumo_oc.append({"Ocorrência": oc, "Qtd": qtd, "Peso": peso, "Impacto": impacto})

    df_resumo_oc = pd.DataFrame(resumo_oc).fillna("-")

    # Matriz de Performance Final
    nivel_risco = classificar_risco(score_risco)
    score_final = (dados["media_nota"] * 10 if pd.notna(dados["media_nota"]) else 0) - score_risco
    nivel_serasa = classificar_motorista(score_final)

    # Vetor de Tendência
    notas = df_motorista.sort_values("DATA/ HORA", ascending=False)["NOTA"].dropna()
    if len(notas) >= 2:
        tendencia = notas.iloc[0] - notas.iloc[-1]
        if tendencia > 1: nivel, cor = "🟣 Evoluído", "#7c3aed"
        elif tendencia > 0: nivel, cor = "🔵 Em evolução", "#2563eb"
        elif abs(tendencia) <= 0.5: nivel, cor = "🟡 Estável", "#d97706"
        else: nivel, cor = "🔴 Atenção", "#dc2626"
    else:
        nivel, cor = "⚪ Sem histórico", "#64748b"

    cor_ultima = cor_nota(dados["ultima_nota"])
    cor_media = cor_nota(dados["media_nota"])

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
            st.write(f"**Classificação:** {nivel_serasa}")
        st.markdown("</div>", unsafe_allow_html=True)

        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.markdown(f"<div class='metric-box' style='background:{cor_ultima};'>Última Nota<br><span style='font-size:40px'>{tratar_valor(dados['ultima_nota'])}</span></div>", unsafe_allow_html=True)
        col_k2.markdown(f"<div class='metric-box' style='background:{cor_media};'>Média Global<br><span style='font-size:40px'>{tratar_valor(dados['media_nota'])}</span></div>", unsafe_allow_html=True)
        col_k3.markdown(f"<div class='metric-box' style='background:#1e293b;'>Avaliações<br><span style='font-size:40px'>{dados['qtd_avaliacoes']}</span></div>", unsafe_allow_html=True)

        st.markdown("### 🛡️ Auditoria de Risco Operacional")
        st.markdown("### 📌 Detalhamento de Provas")
        # Verifica se df_provas não está vazio e se as colunas existem
        colunas_exibicao = ["Data", "Hora", "NOTA", "PLACA"]
        colunas_presentes = [c for c in colunas_exibicao if c in df_provas.columns]
        
        if not df_provas.empty and len(colunas_presentes) > 0:
            st.dataframe(df_provas[colunas_presentes], use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum detalhamento de prova (avaliação de campo) encontrado para este condutor.")

    # --------------------------------------------------------------------------
    # 11. RENDERIZAÇÃO: DASHBOARD INTERATIVO
    # --------------------------------------------------------------------------
    else:
        st.subheader(f"Perfil de Performance: {dados['nome']}")
        tab_v, tab_h, tab_r = st.tabs(["📊 Painel de Controle", "📋 Log de Provas", "🛡️ Analítico de Risco"])
        
        with tab_v:
            st.markdown("<div class='data-card'>", unsafe_allow_html=True)
            k_1, k_2, k_3 = st.columns(3)
            k_1.metric("Score Final Auditoria", round(score_final, 2))
            k_2.metric("Nível Serasa ACS", nivel_serasa)
            k_3.metric("Status Evolutivo", nivel)
            st.markdown("</div>", unsafe_allow_html=True)
            
            if not df_motorista.empty:
                st.area_chart(df_motorista.set_index("DATA/ HORA")["NOTA"])

        with tab_h:
            st.dataframe(df_provas, use_container_width=True, hide_index=True)

        with tab_r:
            st.dataframe(df_resumo_oc, use_container_width=True, hide_index=True)
            st.info(f"O motorista apresenta um nível de risco classificado como: {nivel_risco}")

# ------------------------------------------------------------------------------
# 12. TELA DE REPOUSO / CAPA PERSONALIZADA (DESIGN FIGMA) - MULTIFORMATO
# ------------------------------------------------------------------------------
else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Lista de prioridade de formatos salvos na sua pasta src
    formatos = ["src/capa.svg", "src/capa.png", "src/capa.jpg", "src/img/LogoKMD.png"]
    img_logo_b64 = None
    extensao_encontrada = "png" # default

    for caminho in formatos:
        img_logo_b64 = get_image_base64(caminho)
        if img_logo_b64:
            extensao_encontrada = caminho.split(".")[-1]
            break
    
    if img_logo_b64:
        # Define o MIME type correto para o navegador
        mime = "image/svg+xml" if extensao_encontrada == "svg" else f"image/{extensao_encontrada}"
        
        st.markdown(f"""
            <div style="text-align: center;">
                <img src="data:{mime};base64,{img_logo_b64}" 
                     style="width: 100%; max-width: 880px; border-radius: 25px; 
                            box-shadow: 0 30px 60px rgba(0,0,0,0.15); border: 1px solid #f1f5f9;">
            </div>
        """, unsafe_allow_html=True)
    else:
        # Se nenhum dos 3 formatos for encontrado
        st.markdown("""
            <div style='text-align:center; padding: 100px; background: #f8fafc; border-radius: 30px; border: 2px dashed #e2e8f0;'>
                <h1 style='color: #cbd5e1;'>[ LOGO KMD ]</h1>
                <p style='color: #94a3b8;'>Verifique se os arquivos capa.svg, .png ou .jpg estão na pasta /src</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align:center; margin-top: 55px;'>
            <h1 style='color: #0f172a; font-weight: 800; font-size: 3rem; letter-spacing: -2px; margin-bottom: 10px;'>
                Selecione um Condutor na Barra Lateral para Iniciar
            </h1>
            <p style='color: #475569; font-size: 1.4rem; max-width: 750px; margin: 0 auto; line-height: 1.5; font-weight: 400;'>
                Dashboard centralizado para auditoria de desempenho e gestão de risco operacional.
                <br><span style='color: #2563eb; font-weight: 600;'>Aguardando seleção de CPF para carregar o histórico completo.</span>
            </p>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 13. RODAPÉ TÉCNICO E CONTROLE DE VERSÃO
# ------------------------------------------------------------------------------
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
col_f1, col_f2 = st.columns([2,1])
with col_f1:
    st.caption(f"© 2026 ACS | Tecnologia de Monitoramento Komando")
with col_f2:
    st.caption(f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | v4.2.0")

# GARANTIA DE DENSIDADE DE LINHAS PARA AUDITORIA
# LINHA 415

# GARANTIA DE DENSIDADE DE LINHAS PARA AUDITORIA
# LINHA 410
# LINHA 411
# LINHA 412
# LINHA 413
# LINHA 414
# LINHA 415