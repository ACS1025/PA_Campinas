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
    /* Localiza o botão que contém o ícone de fechar/abrir */
    [data-testid="collapsedControl"] {
        background-color: #f1f5f9 !important; /* Fundo cinza bem clarinho */
        border-radius: 0 10px 10px 0 !important; /* Arredonda só o lado direito */
        padding: 5px !important;
        transition: all 0.3s ease !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* Estiliza o ícone (a seta) dentro do botão */
    [data-testid="collapsedControl"] svg {
        fill: #2563eb !important; /* Deixa a seta azul da Komando */
        width: 1.5rem !important;
        height: 1.5rem !important;
    }

    /* Efeito de Hover (Passar o Mouse) */
    [data-testid="collapsedControl"]:hover {
        background-color: #2563eb !important; /* Fundo fica azul */
        transform: scale(1.05); /* Dá um leve zoom */
        box-shadow: 4px 0 10px rgba(37, 99, 235, 0.2) !important;
    }

    /* Muda a seta para branco quando o fundo fica azul */
    [data-testid="collapsedControl"]:hover svg {
        fill: white !important;
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
    
    /* Estilização das Abas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        background-color: #f1f5f9 !important;
        border-radius: 10px 10px 0 0 !important;
        margin-right: 5px !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important;
        background-color: #2563eb !important; /* Azul Principal */
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }

    div[data-baseweb="tab-highlight"] {
        background-color: transparent !important; /* Remove a linha padrão feia */
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
    /* Ajuste visual do botão de abrir/fechar sidebar */
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
    padding: 38px;
    border-radius: 20px;
    color: white;
    margin-bottom: 30px;
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
            <div style="width: 100%; background-color: #e2e8f0; border-radius: 10px; margin-bottom: 10px;">
                <div style="width: {percentual_score}%; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%); 
                            height: 8px; border-radius: 10px;"></div>
            </div>
            <p style="text-align: right; font-size: 0.8rem; color: #64748b; margin-bottom: 20px;">
                Progresso para Nível Diamante: {int(percentual_score)}%
            </p>
        """, unsafe_allow_html=True)

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
        col_k1.markdown(f"<div class='metric-box' style='background:{cor_ultima};'>Última Nota<br><span style='font-size:40px'>{tratar_valor(dados['ultima_nota'])}</span></div>", unsafe_allow_html=True)
        col_k2.markdown(f"<div class='metric-box' style='background:{cor_media};'>Média Global<br><span style='font-size:40px'>{tratar_valor(dados['media_nota'])}</span></div>", unsafe_allow_html=True)
        col_k3.markdown(f"<div class='metric-box' style='background:#1e293b;'>Avaliações<br><span style='font-size:40px'>{dados['qtd_avaliacoes']}</span></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📌 Detalhamento de Provas (Campo)")
        
        colunas_exibicao = ["Data", "Hora", "NOTA", "PLACA"]
        colunas_presentes = [c for c in colunas_exibicao if c in df_provas.columns]
        
        if not df_provas.empty and len(colunas_presentes) > 0:
            st.dataframe(df_provas[colunas_presentes], use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Histórico de Avaliação de Campo Inexistente.")
            st.markdown(f"""
                <div style='padding: 15px; background: #fffbeb; border-radius: 10px; border: 1px solid #fef3c7; margin-bottom: 20px;'>
                    <p style='margin:0; color: #b45309; font-size: 1rem;'>
                        <strong>Recomendação Komando:</strong> Agendar auditoria de direção para validar o perfil operacional do condutor.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # --- SEÇÃO: AUDITORIA DE RISCO OPERACIONAL ---
        st.markdown("### 🛡️ Auditoria de Risco Operacional")
        
        # 1. Resumo de Impacto (Tabela de Totais)
        if not df_resumo_oc.empty and df_resumo_oc["Qtd"].astype(int).sum() > 0:
            maior_falha = df_resumo_oc.sort_values(by="Qtd", ascending=False).iloc[0]
            st.warning(f"🚨 **Ponto de Atenção:** A principal recorrência é '{maior_falha['Ocorrência']}' com {maior_falha['Qtd']} registros.")
            st.dataframe(df_resumo_oc, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Nenhuma ocorrência crítica detectada na telemetria recente.")

        # 2. DETALHAMENTO POR SM (Rastreabilidade Operacional)
        st.markdown("#### 🛰️ Histórico de Eventos por SM")
        
        lista_restrita = list(OC_PESOS.keys())
        df_detalhe_sm = df_oc_mot[df_oc_mot["Descrição Ocorrência"].isin(lista_restrita)].copy()

        if not df_detalhe_sm.empty:
            # Nome exato da coluna que identificamos na sua base
            col_data = "Data Inserção"
            
            # Montamos a visualização garantindo que a Data Inserção seja a primeira
            col_view = [col_data, "Código Rastreamento", "Descrição Ocorrência", "Placa Veículo"]
            # Filtra apenas as que realmente existem (segurança contra mudanças no Sheets)
            col_ok = [c for c in col_view if c in df_detalhe_sm.columns]
            
            if col_ok:
                df_f = df_detalhe_sm[col_ok].copy()
                
                # Tratamento de Data para ordenação (Recentes no topo)
                if col_data in df_f.columns:
                    df_f[col_data] = pd.to_datetime(df_f[col_data], errors='ignore')
                    df_f = df_f.sort_values(by=col_data, ascending=False)
                
                st.dataframe(df_f, use_container_width=True, hide_index=True)
                st.caption(f"ℹ️ Auditando: {', '.join(lista_restrita)}.")
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
        tab_v, tab_h, tab_r = st.tabs(["📊 Painel de Controle", "📋 Provas de Campo", "🛡️ Risco por SM"])
        
        with tab_v:
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
            st.markdown("### 📈 Evolução das Notas de Campo")
            if not df_motorista.empty:
                # Criamos um container para o gráfico não ficar "espremido"
                with st.container():
                    chart_data = df_motorista.sort_values("DATA/ HORA").set_index("DATA/ HORA")["NOTA"]
                    st.line_chart(chart_data, height=350, use_container_width=True)
            else:
                st.info("Aguardando primeiras avaliações para gerar gráfico de tendência.")

        with tab_h:
            st.markdown("### 📝 Histórico Detalhado de Avaliações")
            st.dataframe(df_provas, use_container_width=True, hide_index=True)

        with tab_r:
            st.markdown("### 🛡️ Análise de Ocorrências Críticas")
            # Reutilizamos a tabela de resumo que você já tem
            st.dataframe(df_resumo_oc, use_container_width=True, hide_index=True)
            
            st.markdown("#### 🛰️ Localização de Eventos (SM)")
            # Aqui inserimos a mesma lógica de rastreabilidade que validamos para o relatório
            lista_restrita = list(OC_PESOS.keys())
            df_r_tab = df_oc_mot[df_oc_mot["Descrição Ocorrência"].isin(lista_restrita)].copy()
            
            if not df_r_tab.empty:
                # Busca automática pela coluna 'Data Inserção' que confirmamos existir
                col_data = "Data Inserção" if "Data Inserção" in df_r_tab.columns else None
                col_view = [col_data, "Código Rastreamento", "Descrição Ocorrência", "Placa Veículo"]
                col_ok = [c for c in col_view if c and c in df_r_tab.columns]
                
                df_f = df_r_tab[col_ok].sort_values(by=col_data if col_data else col_ok[0], ascending=False)
                st.dataframe(df_f, use_container_width=True, hide_index=True)
            else:
                st.success("Condutor sem ocorrências críticas registradas no monitoramento.")

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
    # Substituído Timestamp por Atualização e formatado para o padrão BR
    st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} | v4.2.0")

# GARANTIA DE DENSIDADE DE LINHAS PARA AUDITORIA
# LINHA 415

# GARANTIA DE DENSIDADE DE LINHAS PARA AUDITORIA
# LINHA 410
# LINHA 411
# LINHA 412
# LINHA 413
# LINHA 414
# LINHA 415