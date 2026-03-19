import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO VISUAL
# ---------------------------------------------------
st.set_page_config(page_title="Análise de Risco - PA Campinas", layout="wide")

st.markdown("""
<style>
    .welcome-card { background: linear-gradient(135deg, #007bff 0%, #003366 100%); color: white; padding: 40px; border-radius: 20px; text-align: center; }
    .metric-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center; }
    .report-header { text-align: center; border-bottom: 2px solid #333; margin-bottom: 20px; }
    @media print { .no-print { display:none !important; } .main .block-container { max-width: 100% !important; padding: 0 !important; } }
</style>
""", unsafe_allow_html=True)

URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
URL_DESEMPENHO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=5)
def carregar_dados():
    # Aba Ocorrências: Tratando separadores extras que o Sheets pode enviar nas colunas vazias
    df_oc = pd.read_csv(URL_OCORRENCIAS, on_bad_lines='skip').dropna(how='all', axis=1)
    # Aba Desempenho: Lida como matriz bruta (header=None) para navegar pelas células
    df_des = pd.read_csv(URL_DESEMPENHO, header=None)
    df_oc.columns = [str(c).strip() for c in df_oc.columns]
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    
    # Mapeamento dinâmico (Ocorrências)
    col_cpf = next((c for c in df_oc_bruto.columns if "CPF" in c.upper()), None)
    col_mot = next((c for c in df_oc_bruto.columns if "MOTORISTA" in c.upper()), None)
    col_evento = next((c for c in df_oc_bruto.columns if "OCORRÊNCIA" in c.upper() or "DESCRIÇÃO" in c.upper()), None)
    col_rastr = next((c for c in df_oc_bruto.columns if "RASTREAMENTO" in c.upper()), None)
    col_data = "Data Inserção" # Sua coluna na AW

    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf].apply(limpar_cpf)
    lista_cpfs = sorted(df_oc_bruto[col_cpf].dropna().unique())
    
    st.sidebar.header("Filtro de Análise")
    cpf_selecionado = st.sidebar.selectbox("Escolha o CPF:", [""] + list(lista_cpfs))

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        nome_mot = df_mot[col_mot].iloc[0] if col_mot else "Motorista"

        # --- LÓGICA DE CAPTURA NA PLANILHA DE DESEMPENHO (Baseada na Imagem) ---
        total_sm_planilha, nota_val, peso_val = 0, 0.0, 0.0
        
        # Procura a célula que contém o CPF na matriz bruta
        for r in range(len(df_des_bruto)):
            for c in range(len(df_des_bruto.columns)):
                celula = str(df_des_bruto.iloc[r, c])
                if cpf_limpo_sel in limpar_cpf(celula):
                    # Encontrou o bloco do motorista! Agora busca as labels próximas
                    # Varre as 15 linhas ao redor para achar os valores
                    sub_matriz = df_des_bruto.iloc[r-2 : r+15].astype(str).values.flatten().tolist()
                    for i, texto in enumerate(sub_matriz):
                        t_up = texto.upper()
                        try:
                            if "TOTAL DE SM" in t_up: total_sm_planilha = float(sub_matriz[i+1].replace(",", "."))
                            elif "NOTA AVALIAÇÃO" in t_up: nota_val = float(sub_matriz[i+1].replace(",", "."))
                            elif "PESO DE IMPACTO" in t_up: peso_val = float(sub_matriz[i+1].replace(",", "."))
                        except: continue
                    break

        # --- PROCESSAMENTO DE RISCOS ---
        riscos_pgr = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_riscos = df_mot[df_mot[col_evento].str.upper().isin(riscos_pgr)].copy()
        df_riscos = df_riscos.drop_duplicates(subset=[col_rastr, col_evento, col_data])
        
        pesos = {"DESVIO DE ROTA": 5, "PARADA NÃO INFORMADA": 4, "PARADA EXCEDIDA": 4, "PERNOITE EXCEDIDO": 3, "PARADA EM LOCAL NÃO AUTORIZADO": 3}
        df_riscos["Peso"] = df_riscos[col_evento].str.upper().map(pesos)
        
        viagens = total_sm_planilha if total_sm_planilha > 0 else (df_mot[col_rastr].nunique() if col_rastr else 1)
        indice = df_riscos["Peso"].sum() / viagens if viagens > 0 else 0

        # Status
        if indice <= 1: status, cor = "DIAMANTE", "#28a745"
        elif indice <= 2: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "CRÍTICO", "#dc3545"

        # --- INTERFACE ---
        st.markdown(f"<div class='report-header'><h1>🛡️ {nome_mot}</h1><p>Base Campinas | {cpf_selecionado}</p></div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Viagens Total", int(viagens))
        c2.metric("Ocorrências", len(df_riscos))
        c3.metric("Nota Geral", f"{nota_val:.1f}")
        with c4: st.markdown(f"<div style='background:{cor}; color:white; padding:10px; border-radius:10px;'><b>{status}</b><br>Índice: {indice:.2f}</div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("📋 Detalhamento de Ocorrências (A:AW)")
        # Exibe apenas se a coluna existir no DataFrame filtrado
        cols_final = [c for c in [col_rastr, col_data, col_evento] if c in df_riscos.columns]
        st.table(df_riscos[cols_final])

        if st.button("🖨️ Imprimir"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        st.markdown("<div class='welcome-card'><h1>🛡️ Torre de Controle - PA Campinas</h1><p>Aguardando seleção de motorista...</p></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro na integração: {e}")