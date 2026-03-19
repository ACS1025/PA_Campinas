import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(page_title="Análise de Risco - PA Campinas", layout="wide")

st.markdown("""
<style>
    .report-header { text-align: center; border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px; }
    .metric-box { text-align: center; padding: 10px; border-radius: 10px; color: white; font-weight: bold; }
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"], .no-print { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; }
    }
</style>
""", unsafe_allow_html=True)

# URLs das planilhas (Publicadas como CSV)
URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
URL_DESEMPENHO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"

# ---------------------------------------------------
# FUNÇÕES DE SUPORTE
# ---------------------------------------------------
def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

def encontrar_coluna(df, palavras):
    for col in df.columns:
        for p in palavras:
            if p.upper() in str(col).upper(): return col
    return None

@st.cache_data(ttl=5)
def carregar_dados():
    # Ocorrências (Intervalo A:AW via IMPORTRANGE)
    df_oc = pd.read_csv(URL_OCORRENCIAS).dropna(how='all', axis=1)
    # Desempenho (Matriz posicional)
    df_des = pd.read_csv(URL_DESEMPENHO, header=None).dropna(how='all', axis=1)
    df_oc.columns = [str(c).strip() for c in df_oc.columns]
    return df_oc, df_des

# ---------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ---------------------------------------------------
try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    
    # Mapeamento Dinâmico (Garante que a coluna AW seja lida)
    col_cpf = encontrar_coluna(df_oc_bruto, ["CPF"])
    col_mot = encontrar_coluna(df_oc_bruto, ["MOTORISTA"])
    col_evento = encontrar_coluna(df_oc_bruto, ["DESCRIÇÃO", "OCORRÊNCIA"])
    col_rastr = encontrar_coluna(df_oc_bruto, ["RASTREAMENTO", "CÓDIGO"])
    col_data = "Data Inserção" # Coluna AW

    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf].apply(limpar_cpf)
    lista_cpfs = sorted(df_oc_bruto[col_cpf].dropna().unique())
    
    st.sidebar.header("Módulo de Consulta")
    cpf_selecionado = st.sidebar.selectbox("Selecione o CPF:", [""] + list(lista_cpfs))

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        nome_mot = df_mot[col_mot].iloc[0] if col_mot else "Motorista"

        # 1. BUSCA POSICIONAL NA ABA DESEMPENHO (Baseado na Ficha de Cadastro)
        total_sm_planilha, nota_val, peso_val = 0, 0.0, 0.0
        for r in range(len(df_des_bruto)):
            # Procura o CPF em qualquer lugar da linha
            if cpf_limpo_sel in limpar_cpf(str(df_des_bruto.iloc[r].values)):
                sub_matriz = df_des_bruto.iloc[r-2 : r+15].astype(str).values.flatten().tolist()
                for i, texto in enumerate(sub_matriz):
                    t_up = texto.upper().strip()
                    try:
                        if "TOTAL DE SM" in t_up: total_sm_planilha = float(sub_matriz[i+1].replace(",", "."))
                        elif "NOTA AVALIAÇÃO" in t_up: nota_val = float(sub_matriz[i+1].replace(",", "."))
                        elif "PESO DE IMPACTO" in t_up: peso_val = float(sub_matriz[i+1].replace(",", "."))
                    except: continue
                break

        # 2. LÓGICA DE RISCO (Fiel ao PDF do Elias)
        ocorrencias_foco = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO", "PARADA PERNOITE"]
        df_hist = df_mot[df_mot[col_evento].str.upper().isin(ocorrencias_foco)].copy()
        df_hist = df_hist.drop_duplicates(subset=[col_rastr, col_evento, col_data])

        mapa_pesos = {"DESVIO DE ROTA": 5, "PARADA NÃO INFORMADA": 4, "PARADA EXCEDIDA": 4, "PERNOITE EXCEDIDO": 3, "PARADA EM LOCAL NÃO AUTORIZADO": 3, "PARADA PERNOITE": 3}
        df_hist["Peso"] = df_hist[col_evento].str.upper().map(mapa_pesos).fillna(1)
        
        sm_divisor = total_sm_planilha if total_sm_planilha > 0 else 1
        indice_sev = df_hist["Peso"].sum() / sm_divisor

        # Cores e Status do Relatório Original
        if indice_sev <= 1.5: status, cor = "DIAMANTE", "#28a745"
        elif indice_sev <= 3.0: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "ALTO RISCO", "#dc3545"

        # --- LAYOUT DO RELATÓRIO ---
        st.markdown(f"### Comportamento do Motorista (PGR)")
        st.markdown(f"## Análise Crítica: {nome_mot}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (SM) - Aba Desemp.", int(sm_divisor))
        m2.metric("Ocorrências Avaliadas", len(df_hist))
        with m3: st.markdown(f"<div class='metric-box' style='background:{cor};'><b>{status}</b><br>Indice: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Resumo da Avaliação (Aba Desempenho)")
        r1, r2 = st.columns(2)
        r1.metric("Nota da Avaliação", f"{nota_val:.1f}")
        r2.metric("Peso de Impacto", f"{peso_val:.2f}")

        # Tabela de Impacto (Qtd por tipo)
        st.markdown("#### Impacto por Ocorrência (Apenas Avaliadas):")
        impacto = df_hist[col_evento].value_counts().reset_index()
        impacto.columns = ['Ocorrência', 'Qtd']
        st.table(impacto)

        st.markdown("#### Histórico Completo / Desempenho Detalhado")
        st.table(df_hist[[col_rastr, col_data, col_evento]])

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        st.info("👈 Selecione um motorista no menu lateral para visualizar o relatório.")

except Exception as e:
    st.error(f"Erro ao carregar relatório: {e}")