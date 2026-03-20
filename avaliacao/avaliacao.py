import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO VISUAL (FONTE 13 + CARDS + CABEÇALHO ESCURO)
# ---------------------------------------------------
st.set_page_config(page_title="Relatório PGR - PA Campinas", layout="wide")

st.markdown("""
<style>
    html, body, [class*="st-"] { font-size: 13px !important; font-family: "Segoe UI", sans-serif; }
    .data-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #f0f0f0;
    }
    /* Cabeçalhos de coluna escuros */
    thead tr th { background-color: #212529 !important; color: white !important; }
    
    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white; padding: 60px; border-radius: 20px; text-align: center;
    }
    .metric-box { text-align: center; padding: 12px; border-radius: 8px; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO INTEGRAL (SEM DROPA NADA)
# ---------------------------------------------------
OC_PGR = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=1)
def carregar_dados_totais():
    URL_OC = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
    URL_DES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"
    
    # Importante: Mantendo todas as linhas, inclusive as com NaN
    df_oc = pd.read_csv(URL_OC, skip_blank_lines=False)
    df_des = pd.read_csv(URL_DES, header=None).fillna("")
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados_totais()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    
    # Criamos a chave de busca sem filtrar o dataframe principal
    df_oc_bruto["cpf_busca"] = df_oc_bruto["CPF Motorista"].astype(str).apply(limpar_cpf)

    # --- LÓGICA DO BOTÃO "VOLTAR" (CORRIGIDA) ---
    if 'cpf_selecionado' not in st.session_state:
        st.session_state.cpf_selecionado = ""

    # Sidebar
    st.sidebar.header("🔍 Consulta")
    # Lista de CPFs (removemos apenas nulos da lista visual, mas não do dataframe)
    lista_cpfs = sorted([c for c in df_oc_bruto["CPF Motorista"].unique() if pd.notna(c) and str(c).strip() != ""])
    
    # Widget de seleção
    escolha = st.sidebar.selectbox("Selecione o CPF:", [""] + lista_cpfs, key="widget_cpf")
    st.session_state.cpf_selecionado = escolha

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Voltar ao início"):
        st.session_state.cpf_selecionado = ""
        st.rerun()

    # ---------------------------------------------------
    # RENDERIZAÇÃO
    # ---------------------------------------------------
    if st.session_state.cpf_selecionado:
        # === RELATÓRIO ===
        cpf_limpo = limpar_cpf(st.session_state.cpf_selecionado)
        df_motorista = df_oc_bruto[df_oc_bruto["cpf_busca"] == cpf_limpo].copy()
        
        # Filtro de histórico: Apenas as 5 ocorrências que você quer ver
        df_hist_filtrado = df_motorista[df_motorista["Descrição Ocorrência"].str.upper().isin(OC_PGR)].copy()

        # Busca dados de desempenho (SM)
        sm_vagens, nota_form, peso_form = 0, 0.0, 0.0
        df_matriz_original = pd.DataFrame()
        
        for idx, row in df_des_bruto.iterrows():
            if cpf_limpo in limpar_cpf(str(row[1])):
                df_matriz_original = df_des_bruto.iloc[idx: idx+8, 0:2].copy()
                bloco = df_des_bruto.iloc[idx-1 : idx+12].astype(str).values.flatten().tolist()
                for i, v in enumerate(bloco):
                    if "TOTAL DE SM" in v.upper(): 
                        try: sm_vagens = float(bloco[i+1].replace(',', '.'))
                        except: pass
                break

        # CÁLCULO DO ÍNDICE (CORREÇÃO DA QUEBRA)
        qtd_oc_pgr = len(df_hist_filtrado)
        # Se tem ocorrência mas SM é zero, assume 1 SM para cálculo justo
        divisor_sm = sm_vagens if sm_vagens > 0 else (1 if qtd_oc_pgr > 0 else 0)
        
        indice = (qtd_oc_pgr * 3) / divisor_sm if divisor_sm > 0 else 0
        cor_status = "#28a745" if indice <= 1.0 else "#fd7e14" if indice <= 2.5 else "#dc3545"

        st.markdown(f"### 🛡️ Análise PGR - {df_motorista['Motorista'].iloc[0]}")
        
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
            st.write(f"**Perfil:** {df_motorista['Perfil Motorista'].iloc[0]}")
        st.markdown("</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (SM)", int(sm_vagens))
        m2.metric("Ocorrências PGR", qtd_oc_pgr)
        m3.markdown(f"<div class='metric-box' style='background:{cor_status};'>Índice: {indice:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### 📋 Matriz de Desempenho")
            st.dataframe(df_matriz_original, use_container_width=True, hide_index=True)
        with col2:
            st.write("#### 📊 Histórico PGR (Apenas Filtradas)")
            st.dataframe(df_hist_filtrado[["Data Hora Ocorrência", "Descrição Ocorrência"]], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # === CAPA (IMAGEM 2) ===
        # O contador agora usa o dataframe bruto sem nenhuma exclusão
        total_real_linhas = len(df_oc_bruto) 
        
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Gerenciamento de Risco e Performance Operacional</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista na lateral para abrir o relatório detalhado.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>{len(lista_cpfs)}</h2><b>Motoristas na Base</b></div>", unsafe_allow_html=True)
        with k2: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>{total_real_linhas}</h2><b>Ocorrências Totais (Base Bruta)</b></div>", unsafe_allow_html=True)
        with k3: st.markdown(f"<div class='data-card' style='text-align:center;'><h2>Campinas</h2><b>Unidade Base</b></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro na carga de dados: {e}")