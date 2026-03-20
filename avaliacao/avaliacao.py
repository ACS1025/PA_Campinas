import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO VISUAL (CABEÇALHOS ESCUROS E CARDS)
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
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO E LOGICA DE DADOS
# ---------------------------------------------------
OC_PGR = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=2)
def carregar_dados_integrais():
    URL_OC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
    URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"
    # Lendo todas as 195 linhas sem descartar nada
    df_oc = pd.read_csv(URL_OC, skip_blank_lines=False)
    df_des = pd.read_csv(URL_DES, header=None).fillna("")
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados_integrais()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto["CPF Motorista"].astype(str).apply(limpar_cpf)

    # --- CONTROLE DE RESET DO BOTÃO ---
    if 'reset_counter' not in st.session_state:
        st.session_state.reset_counter = 0

    def acao_voltar():
        st.session_state.reset_counter += 1
        st.rerun()

    # --- SIDEBAR ---
    st.sidebar.header("🔍 Consulta")
    cpfs_lista = sorted([c for c in df_oc_bruto["CPF Motorista"].unique() if pd.notna(c) and str(c).strip() != ""])
    
    # Usando a key dinâmica para resetar o componente
    cpf_selecionado = st.sidebar.selectbox(
        "Selecione o CPF:", 
        [""] + cpfs_lista, 
        key=f"filtro_cpf_{st.session_state.reset_counter}"
    )

    st.sidebar.markdown("---")
    st.sidebar.button("🏠 Voltar ao início", on_click=acao_voltar)

    if cpf_selecionado != "":
        # === PÁGINA: RELATÓRIO INDIVIDUAL ===
        cpf_alvo = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_alvo].copy()
        
        # Histórico APENAS das ocorrências específicas PGR
        df_hist_pgr = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(OC_PGR)].copy()

        # Busca do TOTAL DE SM na aba Desempenho
        sm_real = 0
        df_matriz_des = pd.DataFrame()
        
        for idx, row in df_des_bruto.iterrows():
            if cpf_alvo in limpar_cpf(str(row[1])):
                df_matriz_des = df_des_bruto.iloc[idx: idx+8, 0:2].copy()
                # Varredura para achar o valor numérico do SM
                area_busca = df_des_bruto.iloc[idx-1 : idx+12].astype(str).values.flatten().tolist()
                for i, campo in enumerate(area_busca):
                    if "TOTAL DE SM" in campo.upper():
                        try:
                            sm_real = int(float(area_busca[i+1].replace(',', '.')))
                        except: pass
                break

        # --- CÁLCULO REAL (Ocorrências PGR / SM Real) ---
        qtd_oc_pgr = len(df_hist_pgr)
        # Se tem ocorrência mas SM está zero na planilha, usamos 1 para o cálculo não quebrar
        divisor_calculo = sm_real if sm_real > 0 else (1 if qtd_oc_pgr > 0 else 0)
        
        # Peso fixo de 3 por ocorrência conforme conversamos anteriormente
        indice_pgr = (qtd_oc_pgr * 3) / divisor_calculo if divisor_calculo > 0 else 0
        
        cor_indice = "#28a745" if indice_pgr <= 1.0 else "#fd7e14" if indice_pgr <= 2.5 else "#dc3545"

        st.markdown(f"### 🛡️ Comportamento do Motorista - {df_mot['Motorista'].iloc[0]}")
        
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
            st.write(f"**Perfil:** {df_mot['Perfil Motorista'].iloc[0]}")
        st.markdown("</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (SM Real)", sm_real)
        m2.metric("Ocorrências PGR", qtd_oc_pgr)
        m3.markdown(f"<div class='metric-box' style='background:{cor_indice};'>Índice: {indice_pgr:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            st.write("#### 📋 Matriz de Desempenho (Planilha)")
            st.dataframe(df_matriz_des, use_container_width=True, hide_index=True)
        with col_r:
            st.write("#### 📊 Histórico de Ocorrências PGR")
            st.dataframe(df_hist_pgr[["Data Hora Ocorrência", "Descrição Ocorrência"]], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # === PÁGINA: CAPA (DADOS TOTAIS) ===
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Gerenciamento de Risco e Monitoramento de Performance</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista na lateral para abrir o dossiê técnico.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        k1, k2, k3 = st.columns(3)
        # Aqui garantimos as 195 linhas na contagem da capa
        with k1: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>{len(cpfs_lista)}</h2><b>Motoristas Ativos</b></div>", unsafe_allow_html=True)
        with k2: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>{len(df_oc_bruto)}</h2><b>Total de Ocorrências (Base)</b></div>", unsafe_allow_html=True)
        with k3: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>Campinas</h2><b>Unidade Operacional</b></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao processar base: {e}")