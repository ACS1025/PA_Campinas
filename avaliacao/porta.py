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
    /* 1. RESET E TIPOGRAFIA */
    html, body, [class*="st-"] { 
        font-size: 13px !important; 
        font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
    }

    /* 2. ENGINE DE IMPRESSÃO */
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        [data-testid="stSidebar"], .stTabs, button { display: none !important; }
        .data-card { box-shadow: none !important; border: 1px solid #e2e8f0 !important; }
    }

    /* 3. SIDEBAR CUSTOM (MARRETA AZUL) */
    [data-testid="collapsedControl"] {
        background-color: #f1f5f9 !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 5px !important;
        border: 1px solid #e2e8f0 !important;
        transition: all 0.3s ease;
    }
    [data-testid="collapsedControl"] svg { fill: #2563eb !important; }
    [data-testid="collapsedControl"]:hover {
        background-color: #2563eb !important;
        transform: scale(1.05);
    }
    [data-testid="collapsedControl"]:hover svg { fill: white !important; }

    /* 4. CARDS E CONTAINERS (O VISUAL ROBUSTO) */
    .data-card {
        background-color: white;
        padding: 30px !important;
        border-radius: 18px; /* Mais arredondado como no Figma */
        box-shadow: 0 10px 25px rgba(0,0,0,0.08); /* Sombra mais presente */
        margin-bottom: 35px !important;
        border: 1px solid #f1f5f9;
        transition: transform 0.3s ease;
    }
    .data-card:hover { transform: translateY(-2px); }

    /* 5. KPIs E MÉTRICAS (GRADIENTES E SOMBRAS) */
    .metric-box {
        text-align: center;
        padding: 32px !important;
        border-radius: 20px;
        color: white;
        font-weight: 700;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
        margin-bottom: 25px !important;
    }
    .metric-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.2);
    }

    /* 6. ABAS (TABS) MODERNAS */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        background-color: #f1f5f9 !important;
        border-radius: 12px 12px 0 0 !important;
        margin-right: 8px !important;
        padding: 12px 24px !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important;
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }

    /* 7. ELEMENTOS DE AUDITORIA (BADGES E LEGENDAS) */
    .status-badge {
        padding: 6px 15px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        background-color: #fef3c7 !important; 
        color: #92400e !important;
        border: 1px solid #fcd34d;
        display: inline-block;
        box-shadow: 0 2px 5px rgba(252, 211, 77, 0.3);
    }

    .escala-gravidade { display: flex; gap: 10px; margin: 15px 0; }
    .item-gravidade {
        font-size: 10px; padding: 5px 12px; border-radius: 6px; 
        color: white; font-weight: 700; text-transform: uppercase;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .legenda-auditoria {
        background-color: #f8fafc !important;
        border-radius: 12px;
        padding: 20px;
        border: 1px dashed #cbd5e1;
        margin-top: 20px;
        border-left: 4px solid #64748b !important; /* Detalhe de autoridade */
    }

    /* 8. TABELAS DE ALTA DENSIDADE */
    thead tr th {
        background-color: #1e293b !important;
        color: #ffffff !important;
        padding: 15px !important;
        font-weight: 600 !important;
    }

    /* 9. UI CLEANUP */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    
    /* --- BARRA DE PROGRESSO (RESTAURAÇÃO) --- */
    .progress-container {
        width: 100%;
        background-color: #f1f5f9 !important; /* Fundo da barra (cinza) */
        border-radius: 20px;
        margin: 15px 0;
        border: 1px solid #e2e8f0;
        overflow: hidden;
        height: 14px !important; /* Garante que ela tenha altura */
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    }

    .progress-bar {
        height: 14px !important;
        background: linear-gradient(90deg, #2563eb 0%, #10b981 100%) !important;
        border-radius: 20px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); /* Animação suave */
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
    }

    .progress-text {
        font-size: 13px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
        display: block;
        letter-spacing: -0.3px;
    }
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
    margin-bottom: 35px; /* Ajuste de margem do header */
    box-shadow: 0 10px 25px rgba(30, 58, 138, 0.2);
'>
    <h2 style='margin:0; font-weight: 800; font-size: 2.2rem;'>📊 Histórico do Motorista Supersonic</h2>
    <p style='margin:8px 0 0 0; opacity:0.85; font-size: 1.1rem; font-weight: 400;'>
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
    "PARADA EM LOCAL NÃO AUTORIZADO": 2,
    "ACIONAMENTO POLICIAL": 5,
    "ALERTA DE DESENGATE": 5,
    "ALERTA DE PORTA CARONA": 4,
    "ALERTA DE PORTA MOTORISTA": 4,
    "BLOQUEIO VANDALIZADO": 5,
    "DESCUMPRIMENTO DE NORMAS DE GR": 5,
    "EQUIPAMENTO DESLIGADO": 5,
    "INICIO DE VIAGEM - SEM LIBERADO DA GR": 5,
    "INICIO DE VIAGEM FORA DO LOCAL DE ORIGEM": 4,
    "INICIO DE VIAGEM NÃO INFORMADO": 4,
    "PARADA EM LOCAL NÃO AUTORIZADO": 2,
    "PARADA EXCEDIDA": 3
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
    # --- DENTRO DA SEÇÃO 9 (Lógica de Processamento) ---

    # Cálculo da Matriz de Risco
    score_risco = 0
    resumo_oc = []
    for oc, peso in OC_PESOS.items():
        qtd = df_oc_mot[df_oc_mot["Descrição Ocorrência"] == oc].shape[0]
        impacto = qtd * peso
        score_risco += impacto
        resumo_oc.append({"Ocorrência": oc, "Qtd": qtd, "Peso": peso, "Impacto": impacto})

    # CRIANDO O DATAFRAME E FILTRANDO OS ZERADOS IMEDIATAMENTE
    df_resumo_oc = pd.DataFrame(resumo_oc)
    df_resumo_oc = df_resumo_oc[df_resumo_oc["Qtd"] > 0].reset_index(drop=True)
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
    # 10. RENDERIZAÇÃO: MODO RELATÓRIO TÉCNICO (COM NOVOS REFINAMENTOS)
    # --------------------------------------------------------------------------
    if modo_relatorio:
        # Script para botão de impressão direta
        st.markdown("<script>window.print_report = function() { window.print(); }</script>", unsafe_allow_html=True)
        
        col_header_1, col_header_2 = st.columns([3, 1])
        with col_header_1:
            st.markdown("## 📄 Relatório Consolidado de Auditoria")
        with col_header_2:
            if st.button("🖨️ Imprimir / PDF"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

        # Barra de Performance Visual
        percentual_score = max(0, min(100, score_final))
        st.markdown(f"""
            <div style="margin-top: 20px; margin-bottom: 20px;">
                <span class="progress-text">🎯 Progresso para Nível Diamante: {int(percentual_score)}%</span>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {percentual_score}%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.write(f"**Condutor:** {dados['nome']}")
            st.write(f"**Identificação:** {cpf_selecionado}")
        with col_r2:
            st.write(f"**Veículo Base:** {dados['placa']}")
            st.markdown(f"**Classificação Atual:** <span class='status-badge'>{nivel_serasa}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.markdown(f"<div class='metric-box' style='background:{cor_ultima};'>Última Nota<br><span style='font-size:40px'>{tratar_valor(dados['ultima_nota'])}</span></div>", unsafe_allow_html=True)
        col_k2.markdown(f"<div class='metric-box' style='background:{cor_media};'>Média Global<br><span style='font-size:40px'>{tratar_valor(dados['media_nota'])}</span></div>", unsafe_allow_html=True)
        col_k3.markdown(f"<div class='metric-box' style='background:#1e293b;'>Avaliações<br><span style='font-size:40px'>{dados['qtd_avaliacoes']}</span></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("<br>📌 Detalhamento de Provas", unsafe_allow_html=True)
        
        colunas_exibicao = ["Data", "Hora", "NOTA", "PLACA"]
        colunas_presentes = [c for c in colunas_exibicao if c in df_provas.columns]
        
        if not df_provas.empty and len(colunas_presentes) > 0:
            st.dataframe(df_provas[colunas_presentes], use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Histórico de Avaliação de Campo Inexistente.")
            st.markdown(f"""
                <div style='padding: 15px; background: #fffbeb; border-radius: 10px; border: 1px solid #fef3c7; margin-bottom: 25px;'>
                    <p style='margin:0; color: #b45309; font-size: 1rem;'>
                        <strong>Recomendação Komando:</strong> Agendar auditoria de direção para validar o perfil operacional do condutor.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # --- 10. SEÇÃO: AUDITORIA DE RISCO OPERACIONAL (VERSÃO FINAL) ---
        st.markdown("<br>### 🛡️ Matriz de Risco Comportamental", unsafe_allow_html=True)
        
        # LEGENDA DE CORES PARA IMPRESSÃO
        st.markdown("""
            <div class="escala-gravidade">
                <span class="item-gravidade" style="background:#3b82f6">1-2 Baixa</span>
                <span class="item-gravidade" style="background:#f59e0b">3-4 Média</span>
                <span class="item-gravidade" style="background:#ef4444">5 Crítica</span>
            </div>
        """, unsafe_allow_html=True)

        if not df_resumo_oc.empty and df_resumo_oc["Qtd"].astype(int).sum() > 0:
            # Ponto de Atenção em Destaque
            maior_falha = df_resumo_oc.sort_values(by="Qtd", ascending=False).iloc[0]
            st.warning(f"🚨 **Ponto de Atenção:** A principal recorrência é '{maior_falha['Ocorrência']}' com {maior_falha['Qtd']} registros.")
            
            # Renomeando as colunas para o Dossiê ficar explicativo
            df_exibicao_oc = df_resumo_oc.rename(columns={
                "Peso": "Gravidade (Peso)",
                "Impacto": "Total Pontos (Impacto)"
            })
            
            st.dataframe(df_exibicao_oc, use_container_width=True, hide_index=True)
            
            # EXPLICAÇÃO TÉCNICA DO CÁLCULO
            st.markdown(f"""
                <div style='padding: 12px; background: #fffbeb; border-radius: 8px; border-left: 5px solid #f59e0b; font-size: 11px; color: #854d0e;'>
                    <strong>Nota de Auditoria:</strong> O <b>Impacto</b> é o resultado matemático da (Quantidade x Gravidade). 
                    Este índice reflete o nível de exposição ao risco que o condutor gera para a operação.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.success("✅ Nenhuma ocorrência crítica detectada na telemetria recente.")

        # 2. DETALHAMENTO POR SM (Rastreabilidade Operacional)
        st.markdown("#### 🛰️ Histórico de Eventos por SM")
        
        lista_restrita = list(OC_PESOS.keys())
        df_detalhe_sm = df_oc_mot[df_oc_mot["Descrição Ocorrência"].isin(lista_restrita)].copy()

        if not df_detalhe_sm.empty:
            col_data = "Data Inserção"
            col_view = [col_data, "Código Rastreamento", "Descrição Ocorrência", "Placa Veículo"]
            col_ok = [c for c in col_view if c in df_detalhe_sm.columns]
            
            if col_ok:
                df_f = df_detalhe_sm[col_ok].copy()
                if col_data in df_f.columns:
                    df_f[col_data] = pd.to_datetime(df_f[col_data], errors='ignore')
                    df_f = df_f.sort_values(by=col_data, ascending=False)
                
                st.dataframe(df_f, use_container_width=True, hide_index=True)
                
                # --- LEGENDA FINAL DO ESCOPO ---
                st.markdown(f"""
                    <div class="legenda-auditoria">
                        <span class="legenda-titulo">🔍 Escopo da Auditoria de Risco:</span>
                        <span class="legenda-corpo">
                            Este dossiê monitora automaticamente os seguintes eventos críticos na telemetria: {', '.join(lista_restrita)}.
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Se a coluna sumir ou mudar de nome, o sistema avisa sem travar
                st.warning(f"⚠️ A coluna '{col_data}' não foi encontrada. Colunas disponíveis: {list(df_detalhe_sm.columns)}")
        else:
            st.info("💡 Este condutor não possui eventos críticos registrados nas categorias monitoradas.")

    # --------------------------------------------------------------------------
    # 11. RENDERIZAÇÃO: DASHBOARD INTERATIVO
    # --------------------------------------------------------------------------
    else:
        st.subheader(f"👤 Perfil de Performance: {dados['nome']}")
        st.markdown("<br>", unsafe_allow_html=True)
        tab_v, tab_h, tab_r = st.tabs(["📊 Painel de Controle", "📋 Provas de Campo", "🛡️ Risco por SM"])
        
        with tab_v:
            st.markdown("<br>", unsafe_allow_html=True)
            # --- KPIs ESTILIZADOS ---
            k_col1, k_col2, k_col3 = st.columns(3)
            
            with k_col1:
                st.markdown(f"""
                    <div class='metric-box' style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%);'>
                        <span style='font-size: 1rem; opacity: 0.8;'>Score Final</span><br>
                        <span style='font-size: 2.5rem;'>{round(score_final, 1)}</span>
                    </div>
                """, unsafe_allow_html=True)
            
            with k_col2:
                st.markdown(f"""
                    <div class='metric-box' style='background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);'>
                        <span style='font-size: 1rem; opacity: 0.8;'>Classificação</span><br>
                        <span style='font-size: 2.2rem;'>{nivel_serasa}</span>
                    </div>
                """, unsafe_allow_html=True)
                
            with k_col3:
                st.markdown(f"""
                    <div class='metric-box' style='background: {cor};'>
                        <span style='font-size: 1rem; opacity: 0.8;'>Status Evolutivo</span><br>
                        <span style='font-size: 2.2rem;'>{nivel}</span>
                    </div>
                """, unsafe_allow_html=True)

            # --- GRÁFICO DE TENDÊNCIA ENCORPADO ---
            st.markdown("<br>📈 Evolução das Notas de Campo", unsafe_allow_html=True)
            if not df_motorista.empty:
                # Criamos um container para o gráfico não ficar "espremido"
                with st.container():
                    chart_data = df_motorista.sort_values("DATA/ HORA").set_index("DATA/ HORA")["NOTA"]
                    st.line_chart(chart_data, height=350, use_container_width=True)
            else:
                st.info("Aguardando primeiras avaliações para gerar gráfico de tendência.")

        with tab_h:
            st.markdown("<br>📝 Histórico Detalhado de Avaliações", unsafe_allow_html=True)
            st.dataframe(df_provas, use_container_width=True, hide_index=True)

        with tab_r:
            st.markdown("<br>🛡️ Análise de Ocorrências Críticas", unsafe_allow_html=True)
            
            # --- NOVA LEGENDA DE PESOS ---
            with st.expander("<br>ℹ️ Legenda de Pesos e Gravidade", expanded=False):
                st.markdown("""
                | Peso | Gravidade | Exemplos de Ocorrências |
                | :--- | :--- | :--- |
                | **5** | 🔴 Crítica | Desvio de Rota, Acionamento Policial, Bloqueio Vandalizado |
                | **4** | 🟠 Alta | Alertas de Porta, Início de Viagem não Informado |
                | **3** | 🟡 Média | Parada Excedida |
                | **2** | 🔵 Baixa | Pernoite Excedido, Parada em Local não Autorizado |
                """)

            # Exibição da tabela filtrada (apenas o que aconteceu)
            if not df_resumo_oc.empty:
                st.dataframe(df_resumo_oc, use_container_width=True, hide_index=True)
            else:
                st.success("<br>✅ Nenhuma ocorrência monitorada foi registrada para este condutor.")
            
            st.markdown("<br>🛰️ Localização de Eventos (SM)", unsafe_allow_html=True)
            lista_restrita = list(OC_PESOS.keys())
            df_r_tab = df_oc_mot[df_oc_mot["Descrição Ocorrência"].isin(lista_restrita)].copy()
            
            if not df_r_tab.empty:
                col_data = "Data Inserção" if "Data Inserção" in df_r_tab.columns else None
                col_view = [col_data, "Código Rastreamento", "Descrição Ocorrência", "Placa Veículo"]
                col_ok = [c for c in col_view if c and c in df_r_tab.columns]
                
                df_f = df_r_tab[col_ok].sort_values(by=col_data if col_data else col_ok[0], ascending=False)
                st.dataframe(df_f, use_container_width=True, hide_index=True)
            else:
                st.info("Condutor sem ocorrências críticas registradas no monitoramento.")
                

# ------------------------------------------------------------------------------
# 12. TELA DE REPOUSO / CAPA PERSONALIZADA (DESIGN FIGMA)
# ------------------------------------------------------------------------------
else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # CAMINHO EXATO: Refletindo a pasta 'avaliacao/src' do seu VS Code
    caminho_capa = "avaliacao/src/capa.png" 
    
    img_b64 = get_image_base64(caminho_capa)

    if img_b64:
        # Renderiza a imagem usando Base64 para garantir que funcione no navegador
        st.markdown(f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{img_b64}" 
                     style="width: 100%; max-width: 1400px; border-radius: 25px; 
                            box-shadow: 0 30px 60px rgba(0,0,0,0.15); border: 1px solid #f1f5f9;">
            </div>
        """, unsafe_allow_html=True)
    else:
        # Se a imagem não for encontrada, mostra o placeholder limpo
        st.markdown("""
            <div style='text-align:center; padding: 100px; background: #f8fafc; border-radius: 30px; border: 2px dashed #e2e8f0;'>
                <h1 style='color: #cbd5e1;'>[ LOGO KMD ]</h1>
                <p style='color: #94a3b8;'>Verifique se o arquivo capa.png está na pasta /avaliacao/src</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align:center; margin-top: 55px;'>
            <h1 style='color: #0f172a; font-weight: 800; font-size: 3rem; letter-spacing: -2px; margin-bottom: 10px;'>
                Selecione um Condutor para Iniciar
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
    st.caption(f"© 2026 ACS| Tecnologia de Monitoramento Komando")
with col_f2:
    st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} | v4.2.0")

# GARANTIA DE DENSIDADE DE LINHAS PARA AUDITORIA
# LINHA 415
# LINHA 410
# LINHA 411
# LINHA 412
# LINHA 413
# LINHA 414
# LINHA 415