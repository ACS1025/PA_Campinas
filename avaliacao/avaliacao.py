import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO VISUAL (FONTE 13 + CARDS COM SOMBRA)
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
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"] { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO INTEGRAL (SEM PERDA DE LINHAS)
# ---------------------------------------------------
def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=2)
def carregar_dados_brutos():
    URL_OC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
    URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"
    
    # Carrega mantendo absolutamente tudo (inclusive linhas vazias se houver no CSV)
    df_oc = pd.read_csv(URL_OC)
    df_des = pd.read_csv(URL_DES, header=None).fillna("")
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados_brutos()
    
    # Padronização de nomes sem remover linhas
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    # Criamos a coluna de busca sem filtrar o DF principal
    df_oc_bruto["cpf_limpo_busca"] = df_oc_bruto["CPF Motorista"].astype(str).apply(limpar_cpf)

    # --- CONTROLE DE NAVEGAÇÃO ---
    if 'cpf_selecionado' not in st.session_state:
        st.session_state.cpf_selecionado = ""

    def voltar_ao_inicio():
        st.session_state.cpf_selecionado = ""
        st.rerun()

    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Módulo de Consulta")
    # Lista de CPFs baseada nos dados existentes
    cpfs_disponiveis = sorted(df_oc_bruto["CPF Motorista"].dropna().unique())
    
    cpf_escolhido = st.sidebar.selectbox(
        "Selecione o CPF:", 
        [""] + list(cpfs_disponiveis),
        index=0 if st.session_state.cpf_selecionado == "" else (list(cpfs_disponiveis).index(st.session_state.cpf_selecionado) + 1)
    )
    st.session_state.cpf_selecionado = cpf_escolhido

    st.sidebar.markdown("---")
    st.sidebar.button("🏠 Voltar ao início", on_click=voltar_ao_inicio)

    # ---------------------------------------------------
    # LÓGICA DE EXIBIÇÃO
    # ---------------------------------------------------
    if st.session_state.cpf_selecionado != "":
        # === PÁGINA 1: RELATÓRIO (IGUAL AO PDF APROVADO) ===
        cpf_busca = limpar_cpf(st.session_state.cpf_selecionado)
        df_motorista = df_oc_bruto[df_oc_bruto["cpf_limpo_busca"] == cpf_busca].copy()
        
        # Resgate total de dados da aba Desempenho
        total_sm, nota_val, peso_impacto = 0, 0.0, 0.0
        df_matriz_desempenho = pd.DataFrame()
        
        for idx, row in df_des_bruto.iterrows():
            if cpf_busca in limpar_cpf(str(row[1])):
                df_matriz_desempenho = df_des_bruto.iloc[idx: idx+8, 0:2].copy()
                # Captura valores numéricos exatos
                lista_celulas = df_des_bruto.iloc[idx-1 : idx+12].astype(str).values.flatten().tolist()
                for i, texto in enumerate(lista_celulas):
                    t = texto.upper()
                    try:
                        if "TOTAL DE SM" in t: total_sm = float(lista_celulas[i+1].replace(',', '.'))
                        if "NOTA AVALIAÇÃO" in t: nota_val = float(lista_celulas[i+1].replace(',', '.'))
                        if "PESO DE IMPACTO" in t: peso_impacto = float(lista_celulas[i+1].replace(',', '.'))
                    except: continue
                break

        # Dados Técnicos do Cabeçalho
        st.markdown(f"### 🛡️ Relatório Técnico - {df_motorista['Motorista'].iloc[0]}")
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Motorista:** {df_motorista['Motorista'].iloc[0]}")
            st.write(f"**CPF:** {st.session_state.cpf_selecionado}")
        with c2:
            st.write(f"**Placa:** {df_motorista['Placa Veículo'].iloc[0]}")
            st.write(f"**Rastreamento:** {df_motorista['Código Rastreamento'].iloc[0]}")
        with c3:
            st.write(f"**Cliente:** {df_motorista['Cliente'].iloc[0]}")
            st.write(f"**Perfil:** {df_motorista['Perfil Motorista'].iloc[0] if 'Perfil Motorista' in df_motorista.columns else 'N/D'}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Filtro PGR para cálculo do índice (não afeta o DF bruto)
        oc_pgr = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_pgr_individual = df_motorista[df_motorista["Descrição Ocorrência"].str.upper().isin(oc_pgr)]
        
        indice = (len(df_pgr_individual) * 3) / (total_sm if total_sm > 0 else 1)
        status_cor = "#28a745" if indice <= 1.0 else "#fd7e14" if indice <= 2.5 else "#dc3545"

        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (SM)", int(total_sm))
        m2.metric("Eventos PGR", len(df_pgr_individual))
        m3.markdown(f"<div class='metric-box' style='background:{status_cor};'>Índice: {indice:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            st.write("#### 📋 Matriz de Desempenho")
            st.dataframe(df_matriz_desempenho, use_container_width=True, hide_index=True)
        with col_r:
            st.write("#### 📊 Histórico de Ocorrências")
            st.dataframe(df_motorista[["Data Hora Ocorrência", "Descrição Ocorrência"]], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # === PÁGINA 2: CAPA (IMAGEM 2) - TOTALMENTE INTEGRAL ===
        # AQUI USAMOS O DATAFRAME BRUTO SEM NENHUM FILTRO (195 linhas)
        total_geral_linhas = len(df_oc_bruto) 
        total_motoristas_unicos = len(cpfs_disponiveis)
        
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Gerenciamento de Risco e Performance Operacional</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista para análise detalhada no menu à esquerda.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 Panorama Geral (Base Completa)")
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"<div class='data-card' style='text-align:center;'><h2 style='color:#007bff;'>{total_motoristas_unicos}</h2><b>Motoristas Mapeados</b></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='data-card' style='text-align:center;'><h2 style='color:#dc3545;'>{total_geral_linhas}</h2><b>Total de Ocorrências (Base Bruta)</b></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='data-card' style='text-align:center;'><h2 style='color:#28a745;'>Campinas</h2><b>Unidade de Monitoramento</b></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro técnico: {e}")