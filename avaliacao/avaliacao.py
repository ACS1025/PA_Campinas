import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CSS (ESTILO CORPORATIVO)
# ---------------------------------------------------
st.set_page_config(page_title="Relatório PGR - PA Campinas", layout="wide")

st.markdown("""
<style>
    /* Fonte e Estilo Geral */
    html, body, [class*="st-"] {
        font-size: 13px !important;
        font-family: "Segoe UI", sans-serif;
    }
    
    /* Card com Sombra e Bordas */
    .data-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }

    /* Cabeçalhos de Tabela Escuros */
    thead tr th {
        background-color: #212529 !important;
        color: white !important;
        text-transform: uppercase;
        font-size: 11px !important;
    }

    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white; padding: 60px; border-radius: 20px; text-align: center;
    }

    .metric-box { text-align: center; padding: 12px; border-radius: 8px; color: white; font-weight: bold; font-size: 16px; }

    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"] { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        .data-card { box-shadow: none; border: 1px solid #ddd; }
        thead tr th { background-color: #212529 !important; color: white !important; -webkit-print-color-adjust: exact; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# FUNÇÕES DE APOIO
# ---------------------------------------------------
def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=5)
def carregar_dados():
    URL_OC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
    URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"
    df_oc = pd.read_csv(URL_OC).dropna(how='all', axis=1)
    df_des = pd.read_csv(URL_DES, header=None).fillna("")
    return df_oc, df_des

# ---------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------
try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto["CPF Motorista"].apply(limpar_cpf)

    # Sidebar e Controle de Navegação
    st.sidebar.header("🔍 Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto["CPF Motorista"].dropna().unique())
    
    # Seleção de CPF
    cpf_selecionado = st.sidebar.selectbox("Selecione o CPF:", [""] + list(lista_cpfs))

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Voltar ao início"):
        st.rerun()

    if cpf_selecionado != "":
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        # 1. Recuperando Dados da Aba Desempenho (Posicional)
        total_sm, nota_val, peso_impacto = 0, 0.0, 0.0
        df_ficha_bruta = pd.DataFrame()
        
        for idx, row in df_des_bruto.iterrows():
            if cpf_limpo_sel in limpar_cpf(str(row[1])):
                df_ficha_bruta = df_des_bruto.iloc[idx: idx+8, 0:2].copy()
                sub = df_des_bruto.iloc[idx-1 : idx+15].astype(str).values.flatten().tolist()
                for i, txt in enumerate(sub):
                    t_up = txt.upper().strip()
                    try:
                        if "TOTAL DE SM" in t_up: total_sm = float(sub[i+1].replace(',', '.'))
                        elif "NOTA AVALIAÇÃO" in t_up: nota_val = float(sub[i+1].replace(',', '.'))
                        elif "PESO DE IMPACTO" in t_up: peso_impacto = float(sub[i+1].replace(',', '.'))
                    except: continue
                break

        # 2. Lógica de Pesos e Impacto (DADOS RECUPERADOS)
        mapa_pesos = {
            "DESVIO DE ROTA": 5, 
            "PARADA NÃO INFORMADA": 4, 
            "PARADA EXCEDIDA": 3, 
            "PERNOITE EXCEDIDO": 2, 
            "PARADA EM LOCAL NÃO AUTORIZADO": 2
        }
        
        ocorrencias_monitoradas = list(mapa_pesos.keys())
        df_hist = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(ocorrencias_monitoradas)].copy()
        df_hist = df_hist.drop_duplicates(subset=["Código Rastreamento", "Descrição Ocorrência", "Data Hora Ocorrência"])
        
        # Cálculo do Índice de Severidade
        df_hist["Peso"] = df_hist["Descrição Ocorrência"].str.upper().map(mapa_pesos)
        sm_divisor = total_sm if total_sm > 0 else 1
        indice_sev = df_hist["Peso"].sum() / sm_divisor

        # Status
        if indice_sev <= 1.0: status, cor = "DIAMANTE", "#28a745"
        elif indice_sev <= 2.5: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "ALTO RISCO", "#dc3545"

        # --- VIEW DO RELATÓRIO ---
        st.markdown(f"### 🛡️ Comportamento do Motorista (PGR)")
        
        # Bloco de Dados Técnicos (Com sombra)
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Motorista:** {df_mot['Motorista'].iloc[0]}")
            st.write(f"**CPF:** {cpf_selecionado}")
        with c2:
            st.write(f"**Placa:** {df_mot['Placa Veículo'].iloc[0]}")
            st.write(f"**Rastreamento:** {df_mot['Código Rastreamento'].iloc[0]}")
        with c3:
            st.write(f"**Cliente:** {df_mot['Cliente'].iloc[0]}")
            st.write(f"**Perfil:** {df_mot['Perfil Motorista'].iloc[0] if 'Perfil Motorista' in df_mot.columns else 'N/D'}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Métricas Principais
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Viagens (SM)", int(sm_divisor))
        with m2: st.metric("Eventos Detectados", len(df_hist))
        with m3: st.markdown(f"<div class='metric-box' style='background:{cor};'>{status}<br>Índice: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        # Resumo da Avaliação e Impacto
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_res1, col_res2 = st.columns([1, 1.2])
        
        with col_res1:
            st.write("#### 📊 Resumo de Performance")
            st.write(f"**Nota Global:** {nota_val:.1f}")
            st.write(f"**Peso de Impacto:** {peso_impacto:.2f}")
            st.write("**Impacto por Ocorrência:**")
            # Tabela de contagem recuperada
            impacto_resumo = df_hist["Descrição Ocorrência"].value_counts().reset_index()
            impacto_resumo.columns = ['Ocorrência', 'Qtd']
            st.dataframe(impacto_resumo, use_container_width=True, hide_index=True)
            
        with col_res2:
            st.write("#### 📋 Matriz de Desempenho (Original)")
            st.dataframe(df_ficha_bruta, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Histórico Completo no final
        st.write("#### 📂 Histórico Detalhado de Eventos")
        st.dataframe(df_hist[["Data Hora Ocorrência", "Descrição Ocorrência", "Código Rastreamento"]], use_container_width=True, hide_index=True)

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        # CAPA
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Análise de Comportamento e Risco PGR</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista na lateral para gerar o documento técnico.</p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")