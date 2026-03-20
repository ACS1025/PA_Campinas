import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CSS (VISUAL REFINADO)
# ---------------------------------------------------
st.set_page_config(page_title="Relatório PGR - PA Campinas", layout="wide")

st.markdown("""
<style>
    /* Estilo Fonte 13px e Sombras */
    html, body, [class*="st-"] {
        font-size: 13px !important;
        font-family: "Segoe UI", sans-serif;
    }
    
    /* Card com Sombra para os dados */
    .data-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #ececec;
    }

    /* Cabeçalhos de Coluna Escuros */
    .stDataFrame thead tr th {
        background-color: #343a40 !important;
        color: white !important;
    }

    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white; padding: 60px; border-radius: 20px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    .metric-box { text-align: center; padding: 10px; border-radius: 8px; color: white; font-weight: bold; }

    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"] { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        .data-card { box-shadow: none; border: 1px solid #000; }
        .stDataFrame thead tr th { background-color: #343a40 !important; color: white !important; -webkit-print-color-adjust: exact; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO E FUNÇÕES
# ---------------------------------------------------
URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
URL_DESEMPENHO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=5)
def carregar_dados():
    df_oc = pd.read_csv(URL_OCORRENCIAS).dropna(how='all', axis=1)
    df_des = pd.read_csv(URL_DESEMPENHO, header=None).fillna("")
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto["CPF Motorista"].apply(limpar_cpf)
    
    # --- CONTROLE DE NAVEGAÇÃO ---
    if "cpf_selecionado" not in st.session_state:
        st.session_state.cpf_selecionado = ""

    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto["CPF Motorista"].dropna().unique())
    
    # Selectbox vinculada ao session_state
    escolha = st.sidebar.selectbox(
        "Selecione o CPF:", 
        [""] + list(lista_cpfs),
        index=0 if st.session_state.cpf_selecionado == "" else (list(lista_cpfs).index(st.session_state.cpf_selecionado) + 1)
    )
    st.session_state.cpf_selecionado = escolha

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Voltar ao início"):
        st.session_state.cpf_selecionado = ""
        st.rerun()

    # --- LÓGICA DO RELATÓRIO ---
    if st.session_state.cpf_selecionado != "":
        cpf_limpo_sel = limpar_cpf(st.session_state.cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        # Coleta de dados da Aba Desempenho
        total_sm, nota_val, peso_val = 0, 0.0, 0.0
        df_ficha_bruta = pd.DataFrame()
        for idx, row in df_des_bruto.iterrows():
            if cpf_limpo_sel in limpar_cpf(str(row[1])):
                df_ficha_bruta = df_des_bruto.iloc[idx: idx+7, 0:2].copy()
                sub = df_des_bruto.iloc[idx-1 : idx+15].astype(str).values.flatten().tolist()
                for i, txt in enumerate(sub):
                    t_up = txt.upper().strip()
                    try:
                        if "TOTAL DE SM" in t_up: total_sm = float(sub[i+1].replace(',', '.'))
                        elif "NOTA AVALIAÇÃO" in t_up: nota_val = float(sub[i+1].replace(',', '.'))
                        elif "PESO DE IMPACTO" in t_up: peso_val = float(sub[i+1].replace(',', '.'))
                    except: continue
                break

        # Cálculos de Risco
        ocorrencias_foco = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_hist = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(ocorrencias_foco)].copy()
        df_hist = df_hist.drop_duplicates(subset=["Código Rastreamento", "Descrição Ocorrência", "Data Hora Ocorrência"])
        sm_divisor = total_sm if total_sm > 0 else 1
        indice_sev = (len(df_hist) * 3) / sm_divisor

        if indice_sev <= 1.5: status, cor = "DIAMANTE", "#28a745"
        elif indice_sev <= 3.0: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "ALTO RISCO", "#dc3545"

        # --- EXIBIÇÃO DO CONTEÚDO ---
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.subheader("🛡️ Comportamento do Motorista (PGR)")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Rastreamento:** {df_mot['Código Rastreamento'].iloc[0]}")
            st.write(f"**Cliente:** {df_mot['Cliente'].iloc[0]}")
        with c2:
            st.write(f"**Motorista:** {df_mot['Motorista'].iloc[0]}")
            st.write(f"**Placa:** {df_mot['Placa Veículo'].iloc[0]}")
        with c3:
            st.write(f"**CPF:** {st.session_state.cpf_selecionado}")
            st.write(f"**Perfil:** {df_mot['Perfil Motorista'].iloc[0] if 'Perfil Motorista' in df_mot.columns else 'N/D'}")
        st.markdown("</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Viagens (SM)", int(sm_divisor))
        with m2: st.metric("Ocorrências PGR", len(df_hist))
        with m3: st.markdown(f"<div class='metric-box' style='background:{cor};'><b>{status}</b><br>Índice: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.write("#### 📋 Histórico e Desempenho Detalhado")
        
        col_tab1, col_tab2 = st.columns([1, 1])
        with col_tab1:
            st.write("**Ocorrências:**")
            st.dataframe(df_hist[["Data Hora Ocorrência", "Descrição Ocorrência"]], use_container_width=True, hide_index=True)
        with col_tab2:
            st.write("**Matriz de Desempenho:**")
            st.dataframe(df_ficha_bruta, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        # CAPA INICIAL
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Sistema de Análise de Comportamento e Risco PGR</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista na lateral para iniciar a conferência.</p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao carregar relatório: {e}")