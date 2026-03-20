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
    .tip-box {
        padding: 15px;
        border-radius: 10px;
        border-left: 6px solid;
        margin: 15px 0;
        font-size: 1.1rem;
    }
    @media print {
        header, footer, .stSidebar, .stButton, [data-testid="stHeader"], .no-print { 
            display:none !important; 
        }
        .main .block-container { 
            max-width:100% !important; padding:0 !important; margin:0 !important; 
        }
    }
</style>
""", unsafe_allow_html=True)

URL_OCORRENCIAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2109672138&single=true&output=csv"
URL_DESEMPENHO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?gid=2131819073&single=true&output=csv"

def limpar_cpf(cpf):
    return re.sub(r'\D', '', str(cpf)).strip()

@st.cache_data(ttl=5)
def carregar_dados():
    # Carrega Ocorrências e remove colunas totalmente vazias
    df_oc = pd.read_csv(URL_OCORRENCIAS).dropna(how='all', axis=1)
    # Carrega Desempenho mantendo a estrutura posicional (sem header definido)
    df_des = pd.read_csv(URL_DESEMPENHO, header=None)
    return df_oc, df_des

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    
    # Padronização de nomes de colunas da aba Ocorrências
    df_oc_bruto.columns = [str(c).strip() for c in df_oc_bruto.columns]
    col_cpf_oc = "CPF Motorista" if "CPF Motorista" in df_oc_bruto.columns else df_oc_bruto.columns[5]
    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf_oc].apply(limpar_cpf)
    
    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Módulo de Consulta")
    lista_cpfs = sorted(df_oc_bruto[col_cpf_oc].dropna().unique())
    
    cpf_selecionado = st.sidebar.selectbox("Selecione o CPF:", [""] + list(lista_cpfs))

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Voltar ao início"):
        st.rerun()

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        
        # 1. BUSCA DE DADOS NA ABA DESEMPENHO (Mapeamento exato do seu CSV)
        total_sm, nota_val, peso_impacto = 0, 0.0, 0.0
        for idx, row in df_des_bruto.iterrows():
            # Localiza a linha onde o CPF está na segunda coluna
            if cpf_limpo_sel in limpar_cpf(str(row[1])):
                # Captura valores baseados na distância das linhas (conforme snippet do Desempenho.csv)
                try:
                    nota_val = float(str(df_des_bruto.iloc[idx + 3, 1]).replace(',', '.'))
                    total_sm = int(float(str(df_des_bruto.iloc[idx + 4, 1]).replace(',', '.')))
                    peso_impacto = float(str(df_des_bruto.iloc[idx + 6, 1]).replace(',', '.'))
                except: pass
                break

        # 2. FILTRAGEM DE OCORRÊNCIAS (Aba Ocorrências)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        
        # Ocorrências monitoradas conforme sua planilha de Desempenho
        ocorrencias_foco = [
            "DESVIO DE ROTA", 
            "PARADA NÃO INFORMADA", 
            "PARADA EXCEDIDA", 
            "PERNOITE EXCEDIDO", 
            "PARADA EM LOCAL NÃO AUTORIZADO"
        ]
        
        col_desc = "Descrição Ocorrência"
        df_hist = df_mot[df_mot[col_desc].str.upper().isin(ocorrencias_foco)].copy()
        
        # Evita duplicidade (mesmo rastreamento, evento e hora)
        df_hist = df_hist.drop_duplicates(subset=["Código Rastreamento", col_desc, "Data Hora Ocorrência"])

        # 3. CÁLCULO DO ÍNDICE (Fiel à Tabela de Conversão)
        sm_divisor = total_sm if total_sm > 0 else 1
        # Soma de pesos baseada no Desempenho.csv: Desvio(5), Parada Não Inf(4), Parada Exc(3), etc.
        mapa_pesos = {
            "DESVIO DE ROTA": 5, "PARADA NÃO INFORMADA": 4, 
            "PARADA EXCEDIDA": 3, "PERNOITE EXCEDIDO": 2, 
            "PARADA EM LOCAL NÃO AUTORIZADO": 2
        }
        df_hist["Peso"] = df_hist[col_desc].str.upper().map(mapa_pesos)
        indice_sev = df_hist["Peso"].sum() / sm_divisor

        # Definição de Status (Tabela de Conversão)
        if indice_sev <= 1.0: status, cor, dica = "DIAMANTE", "#28a745", "👏 **Exemplar:** Manter elogio e manutenção dos procedimentos."
        elif indice_sev <= 2.0: status, cor, dica = "MODERADO", "#fd7e14", "🤝 **Baixo/Moderado:** Necessário orientação e reciclagem."
        elif indice_sev <= 4.0: status, cor, dica = "ALTO", "#d63384", "⚠️ **Alto Risco:** Sujeito a advertência ou suspensão."
        else: status, cor, dica = "CRÍTICO", "#dc3545", "📢 **Crítico:** Bloqueio imediato conforme PGR."

        # --- EXIBIÇÃO ---
        st.markdown(f"""
            <div style='text-align: center; border-bottom: 2px solid #333; margin-bottom: 20px;'>
                <h1 style='margin:0;'>🛡️ Relatório PA Campinas - Comportamento</h1>
                <h3 style='margin:5px 0;'>{df_mot['Motorista'].iloc[0]} | Placa: {df_mot['Placa Veículo'].iloc[0]}</h3>
                <p style='margin:0; font-size:12px;'>CPF: {cpf_selecionado} | Base Campinas</p>
            </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Viagens (SM)", total_sm)
        m2.metric("Ocorrências PGR", len(df_hist))
        m3.metric("Nota Avaliação", f"{nota_val:.1f}")
        with m4: st.markdown(f"<div style='background:{cor};color:white;padding:10px;border-radius:8px;text-align:center;'><b>{status}</b><br>{indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='tip-box' style='border-color:{cor}; background-color:{cor}15;'>{dica}</div>", unsafe_allow_html=True)

        st.write("### 📋 Histórico Detalhado (Ocorrências)")
        st.table(df_hist[["Código Rastreamento", "Data Hora Ocorrência", col_desc]])

        if st.button("🖨️ Imprimir Relatório"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    else:
        # --- CAPA ORIGINAL ---
        st.markdown("""
            <div class='welcome-card'>
                <h1>🛡️ Análise de Comportamento - PA Campinas</h1>
                <p style='font-size:1.3em; opacity: 0.9;'>Gestão de Performance e Segurança PGR</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.3); margin: 20px 0;'>
                <p>Selecione um motorista no menu lateral para visualizar o histórico e o índice de severidade.</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.info(f"📊 **Total de Ocorrências:** {len(df_oc_bruto)}")
        c2.success(f"🚚 **Motoristas Mapeados:** {len(lista_cpfs)}")

except Exception as e:
    st.error(f"Erro ao processar: {e}")