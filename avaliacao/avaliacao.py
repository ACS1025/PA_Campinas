import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CSS (ESTILO CORPORATIVO)
# ---------------------------------------------------
st.set_page_config(page_title="Relatório PGR - PA Campinas", layout="wide")

st.markdown("""
<style>
    html, body, [class*="st-"] { font-size: 13px !important; font-family: "Segoe UI", sans-serif; }
    
    .data-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #f0f0f0;
    }

    thead tr th { background-color: #212529 !important; color: white !important; font-size: 11px !important; }

    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white; padding: 60px; border-radius: 20px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    .metric-box { text-align: center; padding: 12px; border-radius: 8px; color: white; font-weight: bold; font-size: 16px; }

    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"] { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO E FUNÇÕES
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

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto["CPF Motorista"].apply(limpar_cpf)

    # --- LÓGICA DO BOTÃO VOLTAR ---
    if 'cpf_selecionado' not in st.session_state:
        st.session_state.cpf_selecionado = ""

    def voltar_inicio():
        st.session_state.cpf_selecionado = ""
        st.rerun()

    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto["CPF Motorista"].dropna().unique())
    
    cpf_input = st.sidebar.selectbox(
        "Selecione o CPF:", 
        [""] + list(lista_cpfs),
        index=0 if st.session_state.cpf_selecionado == "" else (list(lista_cpfs).index(st.session_state.cpf_selecionado) + 1),
        key="campo_cpf"
    )
    
    st.session_state.cpf_selecionado = cpf_input

    st.sidebar.markdown("---")
    st.sidebar.button("🏠 Voltar ao início", on_click=voltar_inicio)

    # --- NAVEGAÇÃO ---
    if st.session_state.cpf_selecionado != "":
        # ---------------------------------------------------
        # PÁGINA DO RELATÓRIO (IMAGEM 1 - PERFEITA)
        # ---------------------------------------------------
        cpf_limpo_sel = limpar_cpf(st.session_state.cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        # Coleta posicional na aba Desempenho
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

        # Cálculo de Risco
        ocorrencias_monitoradas = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_hist = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(ocorrencias_monitoradas)].copy()
        df_hist = df_hist.drop_duplicates(subset=["Código Rastreamento", "Descrição Ocorrência", "Data Hora Ocorrência"])
        
        sm_divisor = total_sm if total_sm > 0 else 1
        indice_sev = (len(df_hist) * 3) / sm_divisor
        
        if indice_sev <= 1.0: status, cor = "DIAMANTE", "#28a745"
        elif indice_sev <= 2.5: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "ALTO RISCO", "#dc3545"

        st.markdown(f"### 🛡️ Comportamento do Motorista (PGR)")
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
        with m1: st.metric("Viagens (SM)", int(sm_divisor))
        with m2: st.metric("Eventos Detectados", len(df_hist))
        with m3: st.markdown(f"<div class='metric-box' style='background:{cor};'>{status}<br>Índice: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        col_res1, col_res2 = st.columns([1, 1.2])
        with col_res1:
            st.write("#### 📊 Resumo de Performance")
            st.write(f"**Nota Global:** {nota_val:.1f}")
            st.write(f"**Peso de Impacto:** {peso_impacto:.2f}")
            impacto_resumo = df_hist["Descrição Ocorrência"].value_counts().reset_index()
            impacto_resumo.columns = ['Ocorrência', 'Qtd']
            st.dataframe(impacto_resumo, use_container_width=True, hide_index=True)
        with col_res2:
            st.write("#### 📋 Matriz de Desempenho (Original)")
            st.dataframe(df_ficha_bruta, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        # ---------------------------------------------------
        # PÁGINA INICIAL (IMAGEM 2 - AJUSTADA)
        # ---------------------------------------------------
        # Cálculo dos Totais Gerais para a Capa
        total_ocorrencias_base = len(df_oc_bruto)
        total_motoristas_base = len(lista_cpfs)
        
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Central de Operações - PA Campinas</h1>
                <p style='font-size:1.2em;'>Análise de Comportamento e Gerenciamento de Risco</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 30px 0;'>
                <p>Selecione um motorista na lateral para gerar o documento técnico.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 Panorama Geral da Base (Campinas)")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
                <div class='data-card' style='text-align:center;'>
                    <h2 style='color:#007bff; margin:0;'>{total_motoristas_base}</h2>
                    <p style='margin:0; font-weight:bold;'>Motoristas Ativos</p>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class='data-card' style='text-align:center;'>
                    <h2 style='color:#dc3545; margin:0;'>{total_ocorrencias_base}</h2>
                    <p style='margin:0; font-weight:bold;'>Ocorrências Registradas</p>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class='data-card' style='text-align:center;'>
                    <h2 style='color:#28a745; margin:0;'>Campinas</h2>
                    <p style='margin:0; font-weight:bold;'>Base Operacional</p>
                </div>
            """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")