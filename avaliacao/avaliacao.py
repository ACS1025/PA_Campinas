import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO VISUAL E LIMPEZA DE INTERFACE
# ---------------------------------------------------
st.set_page_config(page_title="Relatório PGR - PA Campinas", layout="wide")

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
    
    /* REMOVE A "SUJEIRA" VISUAL (BOTÃO DE SETA E MENUS PADRÃO) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    button[title="View fullscreen"] {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO E LÓGICA DE DADOS
# ---------------------------------------------------
OC_PGR = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=2)
def carregar_dados():
    URL_OC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
    URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"
    # Lendo todas as linhas sem pular brancos para garantir integridade
    df_oc = pd.read_csv(URL_OC, skip_blank_lines=False)
    df_des = pd.read_csv(URL_DES, header=None).fillna("")
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto["CPF Motorista"].astype(str).apply(limpar_cpf)

    if 'reset_key' not in st.session_state:
        st.session_state.reset_key = 0

    def voltar_inicio():
        st.session_state.reset_key += 1
        st.rerun()

    # --- SIDEBAR ---
    st.sidebar.header("🔍 Consulta")
    cpfs_lista = sorted([c for c in df_oc_bruto["CPF Motorista"].unique() if pd.notna(c) and str(c).strip() != ""])
    
    cpf_selecionado = st.sidebar.selectbox(
        "Selecione o CPF:", 
        [""] + cpfs_lista, 
        key=f"sb_{st.session_state.reset_key}"
    )

    st.sidebar.markdown("---")
    st.sidebar.button("🏠 Voltar ao início", on_click=voltar_inicio)

    if cpf_selecionado != "":
        # === RELATÓRIO INDIVIDUAL ===
        cpf_alvo = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_alvo].copy()
        
        # 1. SM REAL: Contagem de códigos de rastreamento distintos
        sm_real = df_mot["Código Rastreamento"].nunique()

        # 2. Ocorrências PGR Filtradas (Ordenadas pela mais recente)
        df_hist_pgr = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(OC_PGR)].copy()
        df_hist_pgr = df_hist_pgr.sort_values(by="Data Hora Ocorrência", ascending=False)
        qtd_oc_pgr = len(df_hist_pgr)

        # 3. Definição do Rastreamento em destaque (da última ocorrência ou última viagem)
        if not df_hist_pgr.empty:
            rastreio_destaque = df_hist_pgr.iloc[0]["Código Rastreamento"]
        else:
            rastreio_destaque = df_mot.iloc[-1]["Código Rastreamento"] if not df_mot.empty else "N/A"

        # 4. Busca da Matriz de Desempenho
        df_matriz_des = pd.DataFrame()
        for idx, row in df_des_bruto.iterrows():
            if cpf_alvo in limpar_cpf(str(row[1])):
                df_matriz_des = df_des_bruto.iloc[idx: idx+8, 0:2].copy()
                break

        # --- CÁLCULO DO ÍNDICE ---
        indice_pgr = (qtd_oc_pgr * 3) / sm_real if sm_real > 0 else 0
        cor_status = "#28a745" if indice_pgr <= 1.0 else "#fd7e14" if indice_pgr <= 2.5 else "#dc3545"
        label_status = "DIAMANTE" if indice_pgr <= 1.0 else "MODERADO" if indice_pgr <= 2.5 else "ALTO RISCO"

        st.markdown(f"### 🛡️ Análise PGR - {df_mot['Motorista'].iloc[0]}")
        
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Motorista:** {df_mot['Motorista'].iloc[0]}")
            st.write(f"**CPF:** {cpf_selecionado}")
        with c2:
            st.write(f"**Placa:** {df_mot['Placa Veículo'].iloc[0]}")
            st.write(f"**Último Rastreamento:** {rastreio_destaque}")
        with c3:
            st.write(f"**Cliente:** {df_mot['Cliente'].iloc[0]}")
            st.write(f"**Perfil:** {df_mot['Perfil Motorista'].iloc[0]}")
        st.markdown("</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (Total SM)", sm_real)
        m2.metric("Ocorrências PGR", qtd_oc_pgr)
        m3.markdown(f"<div class='metric-box' style='background:{cor_status};'>{label_status}<br>Índice: {indice_pgr:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_1, col_2 = st.columns(2)
        with col_1:
            st.write("#### 📋 Matriz de Desempenho")
            if not df_matriz_des.empty:
                st.dataframe(df_matriz_des, use_container_width=True, hide_index=True)
            else:
                st.markdown("<div class='info-vazio'>Nenhum dado de matriz encontrado para este motorista.</div>", unsafe_allow_html=True)
        
        with col_2:
            st.write("#### 📊 Histórico Detalhado (Com Datas)")
            if not df_hist_pgr.empty:
                # Inclui a coluna de Código Rastreamento para vincular cada erro à sua SM específica
                st.dataframe(df_hist_pgr[["Data Hora Ocorrência", "Descrição Ocorrência", "Código Rastreamento"]], 
                             use_container_width=True, hide_index=True)
            else:
                st.markdown("<div class='info-vazio'>Sem ocorrências PGR registradas no histórico.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # === CAPA (VALORES TOTAIS) ===
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Gerenciamento de Risco e Comportamento PGR</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista no menu lateral para iniciar a análise técnica.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>{len(cpfs_lista)}</h2><b>Motoristas Ativos</b></div>", unsafe_allow_html=True)
        with k2: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>{len(df_oc_bruto)}</h2><b>Registros na Base (Integridade Total)</b></div>", unsafe_allow_html=True)
        with k3: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>Campinas</h2><b>Base de Monitoramento</b></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro técnico ao processar: {e}")