import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Análise de Risco - PA Campinas", layout="wide")

# CSS para limpeza visual
st.markdown("""
<style>
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"] { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; }
    }
    .status-card { padding: 20px; border-radius: 10px; color: white; text-align: center; font-size: 20px; }
</style>
""", unsafe_allow_html=True)

URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
URL_DESEMPENHO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

def encontrar_coluna(df, palavras):
    for col in df.columns:
        for p in palavras:
            if p.upper() in str(col).upper(): return col
    return None

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        df_oc = pd.read_csv(URL_OCORRENCIAS).fillna("")
        df_des = pd.read_csv(URL_DESEMPENHO, header=None).fillna("")
        df_oc.columns = [str(c).strip() for c in df_oc.columns]
        return df_oc, df_des
    except Exception as e:
        st.error(f"Erro ao baixar CSV: {e}")
        return None, None

df_oc_bruto, df_des_bruto = carregar_dados()

if df_oc_bruto is not None:
    # Mapeamento Automático
    col_cpf = encontrar_coluna(df_oc_bruto, ["CPF"])
    col_mot = encontrar_coluna(df_oc_bruto, ["MOTORISTA"])
    col_evento = encontrar_coluna(df_oc_bruto, ["OCORRÊNCIA", "DESCRIÇÃO"])
    col_rastr = encontrar_coluna(df_oc_bruto, ["RASTREAMENTO", "CÓDIGO", "COD"])
    # Busca a última coluna para a Data caso "Data Inserção" falhe
    col_data = encontrar_coluna(df_oc_bruto, ["DATA", "INSERÇÃO"]) or df_oc_bruto.columns[-1]

    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf].astype(str).apply(limpar_cpf)
    lista_cpfs = sorted([c for c in df_oc_bruto[col_cpf].unique() if len(str(c)) > 5])

    st.sidebar.header("Filtros")
    cpf_sel = st.sidebar.selectbox("Motorista (CPF):", [""] + lista_cpfs)

    if cpf_sel:
        cpf_limpo_sel = limpar_cpf(cpf_sel)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        nome_mot = df_mot[col_mot].iloc[0] if col_mot else "Motorista"

        # Busca Notas na Aba Desempenho
        nota, peso, sm_planilha = 0.0, 0.0, 0
        for r in range(len(df_des_bruto)):
            linha_str = " ".join(df_des_bruto.iloc[r].astype(str))
            if cpf_limpo_sel in limpar_cpf(linha_str):
                sub = df_des_bruto.iloc[r-2:r+15].astype(str).values.flatten().tolist()
                for i, txt in enumerate(sub):
                    if "TOTAL DE SM" in txt.upper(): sm_planilha = int(float(sub[i+1].replace(",",".")))
                    if "NOTA AVALIAÇÃO" in txt.upper(): nota = float(sub[i+1].replace(",","."))
                    if "PESO DE IMPACTO" in txt.upper(): peso = float(sub[i+1].replace(",","."))
                break

        # Cálculos de Risco
        ocorrencias_alvo = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_hist = df_mot[df_mot[col_evento].str.upper().isin(ocorrencias_alvo)].copy()
        
        sm_final = sm_planilha if sm_planilha > 0 else 1
        indice = (len(df_hist) * 3) / sm_final # Simplificação do peso para estabilidade

        if indice <= 1.0: status, cor = "DIAMANTE", "#28a745"
        elif indice <= 2.5: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "CRÍTICO", "#dc3545"

        # Display
        st.title(f"🛡️ Relatório de Comportamento")
        st.subheader(f"Motorista: {nome_mot}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Viagens (SM)", sm_final)
        c2.metric("Eventos de Risco", len(df_hist))
        with c3: st.markdown(f"<div class='status-card' style='background:{cor}'>{status}<br>{indice:.2f}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.write("### Detalhamento das Ocorrências")
        st.table(df_hist[[col_rastr, col_data, col_evento]])

        if st.button("🖨️ Gerar PDF / Imprimir"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.info("Selecione um CPF na lateral para gerar a análise.")