import streamlit as st
import pandas as pd
import re

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CSS (PADRÃO "WORD" TAMANHO 13)
# ---------------------------------------------------
st.set_page_config(page_title="Análise de Risco - PA Campinas", layout="wide")

st.markdown("""
<style>
    /* Fonte padrão 13px para otimizar espaço */
    html, body, [class*="st-"] {
        font-size: 13px !important;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    .welcome-card {
        background: linear-gradient(135deg, #007bff 0%, #003366 100%);
        color: white; padding: 50px; border-radius: 15px; text-align: center;
    }
    .metric-box { text-align: center; padding: 10px; border-radius: 8px; color: white; font-weight: bold; }
    
    /* Remoção de cabeçalhos de tabelas e índices do Pandas */
    thead { display: none !important; }
    .blank { display: none !important; }
    
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"], .no-print { display:none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        /* Garante que a tabela use 100% da largura na impressão */
        table { width: 100% !important; border-collapse: collapse; }
        td { border: 1px solid #dee2e6; padding: 4px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARREGAMENTO E LIMPEZA
# ---------------------------------------------------
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
    df_oc_bruto["cpf_limpo"] = df_oc_bruto["CPF Motorista"].apply(limpar_cpf)
    
    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto["CPF Motorista"].dropna().unique())
    
    if "cpf_input" not in st.session_state: st.session_state.cpf_input = ""

    cpf_selecionado = st.sidebar.selectbox(
        "Selecione o CPF:", [""] + list(lista_cpfs), key="cpf_selector"
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Voltar ao início"):
        st.session_state.cpf_selector = ""
        st.rerun()

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        # 1. BUSCA POSICIONAL NA ABA DESEMPENHO
        total_sm, nota_val, peso_val = 0, 0.0, 0.0
        df_ficha_bruta = pd.DataFrame()
        
        for idx, row in df_des_bruto.iterrows():
            if cpf_limpo_sel in limpar_cpf(str(row[1])):
                # Pega a "fatia" do formulário (sem índices)
                df_ficha_bruta = df_des_bruto.iloc[idx: idx+7, 0:2].copy() # Pega os dados principais
                sub = df_des_bruto.iloc[idx-1 : idx+15].astype(str).values.flatten().tolist()
                for i, txt in enumerate(sub):
                    t_up = txt.upper().strip()
                    try:
                        if "TOTAL DE SM" in t_up: total_sm = float(sub[i+1].replace(',', '.'))
                        elif "NOTA AVALIAÇÃO" in t_up: nota_val = float(sub[i+1].replace(',', '.'))
                        elif "PESO DE IMPACTO" in t_up: peso_val = float(sub[i+1].replace(',', '.'))
                    except: continue
                break

        # 2. DADOS TÉCNICOS DA ABA OCORRÊNCIA
        dados_cabecalho = {
            "Código Rastreamento": df_mot["Código Rastreamento"].iloc[0] if not df_mot.empty else "N/D",
            "Cliente": df_mot["Cliente"].iloc[0] if not df_mot.empty else "N/D",
            "Perfil": df_mot["Perfil Motorista"].iloc[0] if "Perfil Motorista" in df_mot.columns else "N/D",
            "Motorista": df_mot["Motorista"].iloc[0] if not df_mot.empty else "N/D",
            "Placa": df_mot["Placa Veículo"].iloc[0] if not df_mot.empty else "N/D"
        }

        # 3. LÓGICA DE RISCO
        ocorrencias_foco = ["DESVIO DE ROTA", "PARADA NÃO INFORMADA", "PARADA EXCEDIDA", "PERNOITE EXCEDIDO", "PARADA EM LOCAL NÃO AUTORIZADO"]
        df_hist = df_mot[df_mot["Descrição Ocorrência"].str.upper().isin(ocorrencias_foco)].copy()
        df_hist = df_hist.drop_duplicates(subset=["Código Rastreamento", "Descrição Ocorrência", "Data Hora Ocorrência"])
        
        sm_divisor = total_sm if total_sm > 0 else 1
        indice_sev = (len(df_hist) * 3) / sm_divisor # Peso padrão conforme PDF

        if indice_sev <= 1.5: status, cor = "DIAMANTE", "#28a745"
        elif indice_sev <= 3.0: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "ALTO RISCO", "#dc3545"

        # --- RELATÓRIO IMPRESSO ---
        st.markdown(f"### Comportamento do Motorista (PGR)")
        
        # Dados Extras solicitados
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**Rastreamento:** {dados_cabecalho['Código Rastreamento']}")
            st.write(f"**Cliente:** {dados_cabecalho['Cliente']}")
        with c2:
            st.write(f"**Motorista:** {dados_cabecalho['Motorista']}")
            st.write(f"**Perfil:** {dados_cabecalho['Perfil']}")
        with c3:
            st.write(f"**Placa:** {dados_cabecalho['Placa']}")
            st.write(f"**CPF:** {cpf_selecionado}")

        st.markdown("---")

        # Métricas em Colunas
        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens (SM)", int(sm_divisor))
        m2.metric("Ocorrências", len(df_hist))
        with m3: st.markdown(f"<div class='metric-box' style='background:{cor};'><b>{status}</b><br>Indice: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.write("#### Resumo da Avaliação")
        r1, r2 = st.columns(2)
        r1.write(f"**Nota da Avaliação:** {nota_val:.1f}")
        r2.write(f"**Peso de Impacto:** {peso_val:.2f}")

        # Tabela de Histórico (Simples, sem índices)
        st.write("#### Histórico de Ocorrências")
        st.dataframe(df_hist[["Data Hora Ocorrência", "Descrição Ocorrência"]], use_container_width=True, hide_index=True)

        # DESEMPENHO DETALHADO (Limpo: Sem números de colunas/linhas)
        st.write("#### Desempenho Detalhado")
        if not df_ficha_bruta.empty:
            # hide_index=True e cabeçalho oculto via CSS
            st.dataframe(df_ficha_bruta, use_container_width=True, hide_index=True)

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Análise de Comportamento - PA Campinas</h1>
                <p>Selecione um motorista no menu lateral para visualizar o relatório.</p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao carregar relatório: {e}")