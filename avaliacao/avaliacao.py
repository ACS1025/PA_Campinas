import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(page_title="Análise de Risco - PA Campinas", layout="wide")

st.markdown("""
<style>
    /* Painel de Boas-Vindas */
    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white;
        padding: 60px;
        border-radius: 20px;
        text-align: center;
        margin-top: 50px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .report-section {
        background-color: white;
        padding: 10px;
        margin-bottom: 5px;
    }

    /* Caixa de Dica Amigável */
    .tip-box {
        padding: 15px;
        border-radius: 10px;
        border-left: 6px solid;
        margin: 15px 0;
        font-size: 1.1rem;
        line-height: 1.5;
    }

    /* REGRAS DE IMPRESSÃO - FORÇAR UMA PÁGINA */
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"], .no-print { 
            display:none !important; 
        }
        /* Remove o espaço gigante que o Streamlit coloca no topo e nas laterais */
        .main .block-container { 
            max-width: 100% !important; 
            padding-top: 0 !important; 
            padding-bottom: 0 !important; 
            margin: 0 !important; 
        }
        /* Compacta as tabelas para não estourarem a página */
        table { width: 100% !important; font-size: 9pt !important; }
        .report-section { border: none !important; }
        h1 { font-size: 18pt !important; }
        h3 { font-size: 14pt !important; }
    }
</style>
""", unsafe_allow_html=True)

URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
URL_DESEMPENHO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

def encontrar_coluna(df, palavras):
    for col in df.columns:
        for p in palavras:
            if p.upper() in col.upper(): return col
    return None

@st.cache_data(ttl=5)
def carregar_dados():
    df_oc = pd.read_csv(URL_OCORRENCIAS)
    df_des = pd.read_csv(URL_DESEMPENHO, header=None) 
    df_oc.columns = [c.strip() for c in df_oc.columns]
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    col_cpf_oc = encontrar_coluna(df_oc_bruto, ["CPF"])
    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf_oc].apply(limpar_cpf)
    
    st.sidebar.header("Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto[col_cpf_oc].dropna().unique())
    cpf_selecionado = st.sidebar.selectbox("Selecione o CPF:", [""] + list(lista_cpfs))

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        nome_mot = df_mot["Motorista"].iloc[0] if "Motorista" in df_mot.columns else "Motorista"
        col_placa = encontrar_coluna(df_mot, ["PLACA"])
        placa_veic = df_mot[col_placa].iloc[0] if col_placa else "N/D"

        linha_inicio = None
        for idx, row in df_des_bruto.iterrows():
            if row.astype(str).str.contains(cpf_selecionado).any() or row.astype(str).str.contains(cpf_limpo_sel).any():
                linha_inicio = idx
                break
        
        total_sm_planilha, nota_val, peso_val = 0, 0.0, 0.0
        df_ficha_exibir = pd.DataFrame()

        if linha_inicio is not None:
            df_ficha = df_des_bruto.iloc[linha_inicio-1 : linha_inicio+15].copy()
            df_ficha_exibir = df_ficha.dropna(how='all', axis=1).fillna("")
            valores_planos = df_ficha.astype(str).values.flatten().tolist()
            for i, v in enumerate(valores_planos):
                v_up = v.upper().strip()
                try:
                    if "TOTAL DE SM" in v_up: total_sm_planilha = float(valores_planos[i+1].replace(",", "."))
                    elif "NOTA AVALIAÇÃO" in v_up: nota_val = float(valores_planos[i+1].replace(",", "."))
                    elif "PESO DE IMPACTO" in v_up: peso_val = float(valores_planos[i+1].replace(",", "."))
                except: continue

        col_evento = encontrar_coluna(df_mot, ["OCORR"])
        col_rastr = encontrar_coluna(df_mot, ["RASTR", "COD"])
        total_sm_final = total_sm_planilha if total_sm_planilha > 0 else (df_mot[col_rastr].nunique() if col_rastr else 1)
        ocorrencias_risco = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_historico_risco = df_mot[df_mot[col_evento].str.upper().isin(ocorrencias_risco)].copy()
        df_historico_risco = df_historico_risco.drop_duplicates(subset=[col_rastr, col_evento, "Data/Hora de ocorrência"])
        
        mapa_pesos = {"DESVIO DE ROTA": 5, "PARADA NÃO INFORMADA": 4, "PARADA EXCEDIDA": 4, "PERNOITE EXCEDIDO": 3, "PARADA EM LOCAL NÃO AUTORIZADO": 3}
        df_historico_risco["Peso"] = df_historico_risco[col_evento].str.upper().map(mapa_pesos)
        indice_sev = df_historico_risco["Peso"].sum() / total_sm_final if total_sm_final > 0 else 0

        if indice_sev <= 1:
            status, cor, dica = "DIAMANTE", "#28a745", "👏 **Excelente performance!** O motorista demonstra total comprometimento com as regras de segurança. Recomenda-se manter o reconhecimento e utilizá-lo como exemplo para a equipe."
        elif indice_sev <= 2:
            status, cor, dica = "MODERADO", "#fd7e14", "🤝 **Oportunidade de Conversa:** Identificamos alguns desvios pontuais. Vale um bate-papo amigável para reforçar os procedimentos de rota e garantir que ele continue evoluindo para o nível Diamante."
        else:
            status, cor, dica = "CRÍTICO", "#dc3545", "📢 **Atenção Prioritária:** O nível de risco atual exige uma intervenção imediata. Recomendamos uma reciclagem técnica e acompanhamento próximo para garantir a segurança do motorista e da operação."

        # CABEÇALHO (Respeitando seu título)
        st.markdown(f"""
            <div style='text-align: center; border-bottom: 2px solid #333; margin-bottom: 10px;'>
                <h1 style='margin:0;'>🛡️ Análise de Comportamento - PA Campinas</h1>
                <h3 style='margin:5px 0;'>{nome_mot} | Placa: {placa_veic}</h3>
                <p style='margin:0; font-size:12px;'>CPF: {cpf_selecionado} | Base Campinas</p>
            </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Viagens (SM)", int(total_sm_final))
        m2.metric("Riscos", len(df_historico_risco))
        m3.metric("Nota", f"{nota_val:.1f}")
        m4.metric("Peso", f"{peso_val:.2f}")
        with m5: st.markdown(f"<div style='background:{cor};color:white;padding:8px;border-radius:8px;text-align:center;'><b>{status}</b><br>{indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class='tip-box' style='border-color: {cor}; background-color: {cor}15; color: #333;'>
                {dica}
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📋 Histórico de Riscos PGR")
        cols_tab = [col_rastr, "Data/Hora de ocorrência", col_evento]
        st.table(df_historico_risco[[c for c in cols_tab if c in df_historico_risco.columns]])

        st.markdown("### 📑 Ficha de Desempenho Detalhada")
        if not df_ficha_exibir.empty:
            st.table(df_ficha_exibir)

        st.markdown("<div class='no-print' style='margin-top:20px;'>", unsafe_allow_html=True)
        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # PAINEL DE BOAS VINDAS (Respeitando seu título)
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Análise de Comportamento - PA Campinas</h1>
                <p style='font-size:1.3em;'>Gestão de Performance - PA Campinas</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        c_i1, c_i2 = st.columns(2)
        c_i1.info(f"📊 Registros na base: {len(df_oc_bruto)}")
        c_i2.success(f"🚚 Motoristas ativos: {len(lista_cpfs)}")
        st.warning("👈 Selecione um motorista na barra lateral para gerar o relatório.")

except Exception as e:
    st.error(f"Erro: {e}")