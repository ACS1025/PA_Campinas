import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CSS (O PRIMEIRO QUE DEU CERTO)
# ---------------------------------------------------
st.set_page_config(page_title="Análise de Comportamento - PA Campinas", layout="wide")

st.markdown("""
<style>
    /* Estilo dos Cards de Performance */
    .metric-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        text-align: center;
    }
    
    /* Caixa de Dica (Baseada no nível de risco) */
    .tip-box {
        padding: 15px;
        border-radius: 10px;
        border-left: 6px solid;
        margin: 15px 0;
        font-size: 1.1rem;
    }

    /* REGRAS DE IMPRESSÃO - FORÇAR 1 FOLHA */
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"], .no-print { 
            display:none !important; 
        }
        .main .block-container { 
            max-width:100% !important; padding:0 !important; margin:0 !important; 
        }
        table { width: 100% !important; font-size: 10pt !important; }
        .stMarkdown { margin-top: -20px; }
    }
</style>
""", unsafe_allow_html=True)

# URLs Publicadas
URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
URL_DESEMPENHO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"

# ---------------------------------------------------
# FUNÇÕES DE LIMPEZA E BUSCA
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
    df_oc = pd.read_csv(URL_OCORRENCIAS).fillna("")
    df_des = pd.read_csv(URL_DESEMPENHO, header=None).fillna("")
    df_oc.columns = [str(c).strip() for c in df_oc.columns]
    return df_oc, df_des

# ---------------------------------------------------
# PROCESSAMENTO
# ---------------------------------------------------
try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    col_cpf = encontrar_coluna(df_oc_bruto, ["CPF"])
    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf].apply(limpar_cpf)
    
    st.sidebar.header("Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto[col_cpf].unique())
    cpf_selecionado = st.sidebar.selectbox("Selecione o CPF:", [""] + list(lista_cpfs))

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        # Dados Básicos
        nome_mot = df_mot["Motorista"].iloc[0] if "Motorista" in df_mot.columns else "Motorista"
        placa_veic = df_mot["Placa"].iloc[0] if "Placa" in df_mot.columns else "N/D"

        # Captura de Nota e Viagens (Aba Desempenho)
        total_sm, nota_val, peso_val = 0, 0.0, 0.0
        for r in range(len(df_des_bruto)):
            if cpf_limpo_sel in limpar_cpf(str(df_des_bruto.iloc[r].values)):
                sub = df_des_bruto.iloc[r-2 : r+15].astype(str).values.flatten().tolist()
                for i, v in enumerate(sub):
                    v_up = v.upper().strip()
                    if "TOTAL DE SM" in v_up: total_sm = float(sub[i+1].replace(",", "."))
                    if "NOTA AVALIAÇÃO" in v_up: nota_val = float(sub[i+1].replace(",", "."))
                    if "PESO DE IMPACTO" in v_up: peso_val = float(sub[i+1].replace(",", "."))
                break

        # Lógica de Risco (Fiel ao PDF)
        col_evento = encontrar_coluna(df_mot, ["OCORRÊNCIA", "DESCRIÇÃO"])
        ocorrencias_pgr = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_hist = df_mot[df_mot[col_evento].str.upper().isin(ocorrencias_pgr)].copy()
        
        # Cálculo de Índice (Severidade)
        sm_divisor = total_sm if total_sm > 0 else 1
        indice_sev = (len(df_hist) * 2) / sm_divisor # Peso ajustado conforme o primeiro código

        # Definição de Status
        if indice_sev <= 1.0:
            status, cor, dica = "DIAMANTE", "#28a745", "👏 **Excelente performance!** O motorista cumpre rigorosamente os protocolos."
        elif indice_sev <= 2.5:
            status, cor, dica = "MODERADO", "#fd7e14", "🤝 **Atenção:** Recomenda-se orientação sobre os pontos de parada."
        else:
            status, cor, dica = "CRÍTICO", "#dc3545", "📢 **Urgente:** Necessário reciclagem e acompanhamento imediato."

        # --- EXIBIÇÃO DO RELATÓRIO ---
        st.markdown(f"""
            <div style='text-align: center; border-bottom: 2px solid #333; margin-bottom: 15px;'>
                <h1 style='margin:0;'>🛡️ Análise de Comportamento - PA Campinas</h1>
                <h3 style='margin:5px 0;'>{nome_mot} | Placa: {placa_veic}</h3>
                <p style='margin:0; font-size:12px;'>CPF: {cpf_selecionado} | Base Campinas</p>
            </div>
        """, unsafe_allow_html=True)

        # Métricas em linha
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Viagens (SM)", int(sm_divisor))
        m2.metric("Ocorrências", len(df_hist))
        m3.metric("Nota Avaliação", f"{nota_val:.1f}")
        with m4: st.markdown(f"<div style='background:{cor};color:white;padding:10px;border-radius:8px;text-align:center;'><b>{status}</b><br>{indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='tip-box' style='border-color:{cor}; background-color:{cor}15;'>{dica}</div>", unsafe_allow_html=True)

        st.write("### 📋 Histórico de Riscos PGR")
        st.table(df_hist[[encontrar_coluna(df_hist, ["RASTR", "COD"]), "Data Inserção", col_evento]])

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        st.info("👈 Selecione um motorista para gerar a análise.")

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")