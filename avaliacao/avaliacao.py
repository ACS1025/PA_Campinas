import streamlit as st
import pandas as pd
import re

# 1. Configuração e Estética Profissional
st.set_page_config(page_title="PGR - PA Campinas", layout="wide")

st.markdown("""
<style>
    html, body, [class*="st-"] { font-size: 13px !important; font-family: "Segoe UI", sans-serif; }
    .data-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #f0f0f0;
    }
    thead tr th { background-color: #212529 !important; color: white !important; }
    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white; padding: 60px; border-radius: 20px; text-align: center;
    }
    .metric-box { text-align: center; padding: 12px; border-radius: 8px; color: white; font-weight: bold; }
    .info-vazio { color: #666; font-style: italic; padding: 10px; background: #f8f9fa; border-left: 5px solid #ccc; }
    /* Esconde o botão keyboard do Streamlit para limpar a tela */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

OC_PGR = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=2)
def carregar_dados():
    URL_OC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
    URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"
    df_oc = pd.read_csv(URL_OC, skip_blank_lines=False)
    df_des = pd.read_csv(URL_DES, header=None).fillna("")
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto["CPF Motorista"].astype(str).apply(limpar_cpf)

    if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

    def voltar_inicio():
        st.session_state.reset_key += 1
        st.rerun()

    # Sidebar
    st.sidebar.header("🔍 Consulta")
    lista_cpfs = sorted([c for c in df_oc_bruto["CPF Motorista"].unique() if pd.notna(c) and str(c).strip() != ""])
    cpf_selecionado = st.sidebar.selectbox("Selecio o CPF:", [""] + lista_cpfs, key=f"s_{st.session_state.reset_key}")
    st.sidebar.button("🏠 Voltar ao início", on_click=voltar_inicio)

    if cpf_selecionado:
        cpf_alvo = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_alvo].copy()
        
        # Filtro de Histórico PGR
        df_hist_pgr = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(OC_PGR)].sort_values(by="Data Hora Ocorrência", ascending=False).copy()
        
        # --- Lógica de Rastreamento ---
        # SM Real = Contagem de códigos distintos
        sm_real = df_mot["Código Rastreamento"].nunique()
        
        # Último Rastreamento = O código da última ocorrência registrada (se houver) ou a última viagem
        if not df_hist_pgr.empty:
            ultimo_rastreio = df_hist_pgr.iloc[0]["Código Rastreamento"]
            ultima_data = df_hist_pgr.iloc[0]["Data Hora Ocorrência"]
        else:
            ultimo_rastreio = df_mot.iloc[-1]["Código Rastreamento"] if not df_mot.empty else "N/A"
            ultima_data = "Sem ocorrências"

        # Matriz de Desempenho
        df_matriz = pd.DataFrame()
        for idx, row in df_des_bruto.iterrows():
            if cpf_alvo in limpar_cpf(str(row[1])):
                df_matriz = df_des_bruto.iloc[idx: idx+8, 0:2].copy()
                break

        # Cálculo
        qtd_oc = len(df_hist_pgr)
        divisor = sm_real if sm_real > 0 else (1 if qtd_oc > 0 else 0)
        indice = (qtd_oc * 3) / divisor if divisor > 0 else 0
        cor_ind = "#28a745" if indice <= 1.0 else "#fd7e14" if indice <= 2.5 else "#dc3545"

        st.subheader(f"🛡️ Análise PGR - {df_mot['Motorista'].iloc[0]}")
        
        # Cabeçalho Detalhado
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Motorista:** {df_mot['Motorista'].iloc[0]}")
            st.write(f"**CPF:** {cpf_selecionado}")
        with c2:
            st.write(f"**Placa:** {df_mot['Placa Veículo'].iloc[0]}")
            st.write(f"**Último Rastreio:** {ultimo_rastreio}")
        with c3:
            st.write(f"**Cliente:** {df_mot['Cliente'].iloc[0]}")
            st.write(f"**Perfil:** {df_mot['Perfil Motorista'].iloc[0]}")
        st.markdown("</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (Total SM Distintos)", sm_real)
        m2.metric("Ocorrências PGR", qtd_oc)
        m3.markdown(f"<div class='metric-box' style='background:{cor_ind};'>Índice: {indice:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            st.write("#### 📋 Matriz de Desempenho")
            if not df_matriz.empty: st.dataframe(df_matriz, use_container_width=True, hide_index=True)
            else: st.markdown("<div class='info-vazio'>Sem dados na matriz.</div>", unsafe_allow_html=True)
        
        with col_r:
            st.write("#### 📊 Histórico de Ocorrências (Por Data)")
            if not df_hist_pgr.empty:
                # Exibe Data, Ocorrência e o Rastreamento específico daquele evento
                st.dataframe(df_hist_pgr[["Data Hora Ocorrência", "Descrição Ocorrência", "Código Rastreamento"]], use_container_width=True, hide_index=True)
            else:
                st.markdown("<div class='info-vazio'>Nenhuma ocorrência PGR vinculada a este CPF.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Capa Azul
        st.markdown(f"""<div class='welcome-card'><h1>🛡️ PA Campinas</h1><p>Gestão de Comportamento PGR</p><br><p>Total de Registros na Base: {len(df_oc_bruto)}</p></div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro: {e}")