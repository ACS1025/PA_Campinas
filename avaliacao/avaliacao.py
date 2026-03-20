import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO VISUAL
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
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .metric-box { text-align: center; padding: 12px; border-radius: 8px; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO E FILTROS
# ---------------------------------------------------
OC_ESPECIFICAS = [
    "DESVIO DE ROTA", "PARADA NÃO INFORMADA", 
    "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", 
    "PARADA EM LOCAL NÃO AUTORIZADO"
]

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=2)
def carregar_dados_brutos():
    URL_OC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
    URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"
    return pd.read_csv(URL_OC), pd.read_csv(URL_DES, header=None).fillna("")

try:
    df_oc_bruto, df_des_bruto = carregar_dados_brutos()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    df_oc_bruto["cpf_limpo_busca"] = df_oc_bruto["CPF Motorista"].astype(str).apply(limpar_cpf)

    # --- LÓGICA DO BOTÃO (RESET DE ESTADO) ---
    if 'cpf_selecionado' not in st.session_state:
        st.session_state.cpf_selecionado = ""

    def reset_app():
        st.session_state.cpf_selecionado = ""
        # Limpa o widget explicitamente
        if 'widget_cpf' in st.session_state:
            st.session_state.widget_cpf = ""
        st.rerun()

    # --- SIDEBAR ---
    st.sidebar.header("🔍 Módulo de Consulta")
    cpfs_disponiveis = sorted(df_oc_bruto["CPF Motorista"].dropna().unique())
    
    selecao_lateral = st.sidebar.selectbox(
        "Selecione o CPF:", 
        [""] + list(cpfs_disponiveis),
        key="widget_cpf"
    )
    
    # Sincroniza a seleção com o estado
    st.session_state.cpf_selecionado = selecao_lateral

    st.sidebar.markdown("---")
    st.sidebar.button("🏠 Voltar ao início", on_click=reset_app)

    # ---------------------------------------------------
    # NAVEGAÇÃO ENTRE CAPA E RELATÓRIO
    # ---------------------------------------------------
    if st.session_state.cpf_selecionado:
        # === RELATÓRIO DO MOTORISTA ===
        cpf_busca = limpar_cpf(st.session_state.cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo_busca"] == cpf_busca].copy()
        
        # Filtro Rigoroso: Mostrar APENAS as 5 ocorrências específicas
        df_hist_filtrado = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(OC_ESPECIFICAS)].copy()

        # Resgate de dados da aba Desempenho
        total_sm, nota_val, peso_imp = 0, 0.0, 0.0
        df_matriz = pd.DataFrame()
        for idx, row in df_des_bruto.iterrows():
            if cpf_busca in limpar_cpf(str(row[1])):
                df_matriz = df_des_bruto.iloc[idx: idx+8, 0:2].copy()
                sub = df_des_bruto.iloc[idx-1 : idx+12].astype(str).values.flatten().tolist()
                for i, txt in enumerate(sub):
                    t = txt.upper()
                    try:
                        if "TOTAL DE SM" in t: total_sm = float(sub[i+1].replace(',', '.'))
                        if "NOTA AVALIAÇÃO" in t: nota_val = float(sub[i+1].replace(',', '.'))
                        if "PESO DE IMPACTO" in t: peso_imp = float(sub[i+1].replace(',', '.'))
                    except: continue
                break

        # Cálculos
        indice = (len(df_hist_filtrado) * 3) / (total_sm if total_sm > 0 else 1)
        status_cor = "#28a745" if indice <= 1.0 else "#fd7e14" if indice <= 2.5 else "#dc3545"

        st.markdown(f"### 🛡️ Relatório Técnico - {df_mot['Motorista'].iloc[0]}")
        
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Motorista:** {df_mot['Motorista'].iloc[0]}")
            st.write(f"**CPF:** {st.session_state.cpf_selecionado}")
        with c2:
            st.write(f"**Placa:** {df_mot['Placa Veículo'].iloc[0]}")
            st.write(f"**Rastreamento:** {df_mot['Código Rastreamento'].iloc[0]}")
        with c3:
            st.write(f"**Cliente:** {df_mot['Cliente'].iloc[0]}")
            st.write(f"**Perfil:** {df_mot['Perfil Motorista'].iloc[0] if 'Perfil Motorista' in df_mot.columns else 'N/D'}")
        st.markdown("</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (SM)", int(total_sm))
        m2.metric("Ocorrências PGR", len(df_hist_filtrado))
        m3.markdown(f"<div class='metric-box' style='background:{status_cor};'>Índice: {indice:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            st.write("#### 📋 Matriz de Desempenho")
            st.dataframe(df_matriz, use_container_width=True, hide_index=True)
        with col_r:
            st.write("#### 📊 Histórico PGR (Apenas Filtradas)")
            st.dataframe(df_hist_filtrado[["Data Hora Ocorrência", "Descrição Ocorrência"]], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # === CAPA INICIAL ===
        total_geral = len(df_oc_bruto) # Mantém as 195 linhas aqui conforme solicitado
        total_mot_unicos = len(cpfs_disponiveis)
        
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Gerenciamento de Risco e Performance Operacional</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista para iniciar.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(f"<div class='data-card' style='text-align:center;'><h2 style='color:#007bff;'>{total_mot_unicos}</h2><b>Motoristas</b></div>", unsafe_allow_html=True)
        with k2: st.markdown(f"<div class='data-card' style='text-align:center;'><h2 style='color:#dc3545;'>{total_geral}</h2><b>Total de Ocorrências</b></div>", unsafe_allow_html=True)
        with k3: st.markdown(f"<div class='data-card' style='text-align:center;'><h2 style='color:#28a745;'>Campinas</h2><b>Unidade Base</b></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro: {e}")