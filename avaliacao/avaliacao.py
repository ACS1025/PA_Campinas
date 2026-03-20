import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(page_title="Análise de Risco - PA Campinas", layout="wide")

st.markdown("""
<style>
    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white;
        padding: 60px;
        border-radius: 20px;
        text-align: center;
        margin-top: 50px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .metric-box { text-align: center; padding: 15px; border-radius: 10px; color: white; font-weight: bold; }
    .tip-box { padding: 15px; border-radius: 10px; border-left: 6px solid; margin: 15px 0; font-size: 1.1rem; }
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"], .no-print { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        table { width: 100% !important; font-size: 9pt !important; }
    }
</style>
""", unsafe_allow_html=True)

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
    col_cpf_oc = "CPF Motorista" if "CPF Motorista" in df_oc_bruto.columns else df_oc_bruto.columns[5]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf_oc].apply(limpar_cpf)
    
    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto[col_cpf_oc].dropna().unique())
    
    # Correção do Reset: Usamos o session_state para controlar o selectbox
    if "cpf_input" not in st.session_state:
        st.session_state.cpf_input = ""

    def reset_app():
        st.session_state.cpf_input = ""
        st.rerun()

    cpf_selecionado = st.sidebar.selectbox(
        "Selecione o CPF:", 
        [""] + list(lista_cpfs), 
        index=0 if st.session_state.cpf_input == "" else (list(lista_cpfs).index(st.session_state.cpf_input) + 1),
        key="cpf_selector"
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Voltar ao início"):
        reset_app()

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        # 1. BUSCA POSICIONAL NA ABA DESEMPENHO (DADOS DO RELATÓRIO ANTERIOR)
        total_sm, nota_val, peso_val = 0, 0.0, 0.0
        df_ficha_bruta = pd.DataFrame()
        
        for idx, row in df_des_bruto.iterrows():
            if cpf_limpo_sel in limpar_cpf(str(row[1])):
                # Pega a "fatia" do formulário para exibir no final (conforme o PDF)
                df_ficha_bruta = df_des_bruto.iloc[idx-1 : idx+15].copy()
                sub = df_ficha_bruta.astype(str).values.flatten().tolist()
                for i, txt in enumerate(sub):
                    t_up = txt.upper().strip()
                    try:
                        if "TOTAL DE SM" in t_up: total_sm = float(sub[i+1].replace(',', '.'))
                        elif "NOTA AVALIAÇÃO" in t_up: nota_val = float(sub[i+1].replace(',', '.'))
                        elif "PESO DE IMPACTO" in t_up: peso_val = float(sub[i+1].replace(',', '.'))
                    except: continue
                break

        # 2. LÓGICA DE RISCO (Fiel ao PDF do Elias)
        ocorrencias_foco = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_hist = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(ocorrencias_foco)].copy()
        df_hist = df_hist.drop_duplicates(subset=["Código Rastreamento", "Descrição Ocorrência", "Data Hora Ocorrência"])
        
        sm_divisor = total_sm if total_sm > 0 else 1
        mapa_pesos = {"DESVIO DE ROTA": 5, "PARADA NÃO INFORMADA": 4, "PARADA EXCEDIDA": 3, "PERNOITE EXCEDIDO": 2, "PARADA EM LOCAL NÃO AUTORIZADO": 2}
        df_hist["Peso"] = df_hist["Descrição Ocorrência"].str.upper().map(mapa_pesos).fillna(1)
        indice_sev = df_hist["Peso"].sum() / sm_divisor

        if indice_sev <= 1.5: status, cor = "DIAMANTE", "#28a745"
        elif indice_sev <= 3.0: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "ALTO RISCO", "#dc3545"

        # --- CABEÇALHO ---
        st.markdown(f"### Comportamento do Motorista (PGR)")
        st.markdown(f"## Análise Crítica: {df_mot['Motorista'].iloc[0]}")

        # MÉTRICAS (Conforme PDF)
        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (SM) - Aba Desemp.", int(sm_divisor))
        m2.metric("Ocorrências Avaliadas", len(df_hist))
        with m3: st.markdown(f"<div class='metric-box' style='background:{cor};'><b>{status}</b><br>Indice: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Resumo da Avaliação (Aba Desempenho)")
        r1, r2 = st.columns(2)
        r1.metric("Nota da Avaliação", f"{nota_val:.1f}")
        r2.metric("Peso de Impacto", f"{peso_val:.2f}")

        # TABELA DE IMPACTO (Contagem por tipo)
        st.markdown("#### Impacto das Ocorrências")
        impacto = df_hist["Descrição Ocorrência"].value_counts().reset_index()
        impacto.columns = ['Ocorrência', 'Qtd']
        st.table(impacto)

        # HISTÓRICO COMPLETO
        st.markdown("#### Histórico Completo")
        st.table(df_hist[["Código Rastreamento", "Data Hora Ocorrência", "Descrição Ocorrência"]])

        # DESEMPENHO DETALHADO (A matriz bruta que aparece no final do PDF)
        st.markdown("#### Desempenho Detalhado")
        if not df_ficha_bruta.empty:
            st.info("✔ Dados de desempenho encontrados para este CPF.")
            st.table(df_ficha_bruta.reset_index(drop=True))

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        # CAPA
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Análise de Comportamento - PA Campinas</h1>
                <p style='font-size:1.3em; opacity: 0.9;'>Gestão de Performance e Segurança PGR</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.3); margin: 20px 0;'>
                <p>Selecione um motorista no menu lateral para visualizar o relatório completo.</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.info(f"📊 Registros na base: {len(df_oc_bruto)}")
        c2.success(f"🚚 Motoristas ativos: {len(lista_cpfs)}")

except Exception as e:
    st.error(f"Erro ao carregar relatório: {e}")