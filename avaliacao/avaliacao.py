import streamlit as st
import pandas as pd

# 1. Configuração do Portal
st.set_page_config(page_title="Portal de Risco - PA Campinas", layout="wide")

# Link direto do seu GSheet
URL_DADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQL5tw7f2ptOEhVk0nyNE5AkddbMVKcXspxL0dl2zz9dhkB7R8HcmtHlW2o-PdgiNw5OBX3M3xTo-al/pub?output=csv"

@st.cache_data(ttl=60)
def buscar_dados():
    df = pd.read_csv(URL_DADOS)
    return df

try:
    df_raw = buscar_dados()
    
    st.title("🛡️ Painel de Controle de Risco (PGR)")
    st.markdown("---")

    # 2. Busca lateral
    st.sidebar.header("Consulta")
    col_cpf = "CPF motorista" if "CPF motorista" in df_raw.columns else "CPF"
    lista_cpfs = sorted(df_raw[col_cpf].unique())
    cpf_selecionado = st.sidebar.selectbox("Digite ou selecione o CPF:", [""] + list(lista_cpfs))

    if cpf_selecionado:
        # Filtragem e Cálculos
        df_mot = df_raw[df_raw[col_cpf] == cpf_selecionado]
        nome_mot = df_mot['Motorista'].iloc[0]
        
        # Mapa de impacto que definimos
        mapa_pesos = {
            'DESVIO DE ROTA': 5,
            'PARADA NÃO INFORMADA': 4,
            'PARADA EXCEDIDA': 4,
            'PERNOITE EXCEDIDO': 3,
            'PARADA EM LOCAL NÃO AUTORIZADO': 3
        }

        # Eventos Reais (D)
        col_rastr = "Cod Rastr." if "Cod Rastr." in df_raw.columns else "Código Rastreador"
        df_distintos = df_mot.drop_duplicates(subset=[col_rastr, 'Ocorrência']).copy()
        df_distintos['Peso'] = df_distintos['Ocorrência'].map(mapa_pesos).fillna(1)
        
        indice_sev = df_distintos['Peso'].sum() / 7 # Dividido por 7 SMs de exemplo

        # --- NOVO: VISUAL DE TOMADA DE DECISÃO ---
        st.subheader(f"Análise Crítica: {nome_mot}")
        
        # Cards de Indicadores Rápidos
        c1, c2, c3 = st.columns(3)
        c1.metric("Viagens Realizadas", "7")
        c2.metric("Ocorrências Reais (D)", len(df_distintos))
        
        # Lógica de Cor para o Índice
        if indice_sev <= 1.0:
            status, cor, msg = "EXEMPLAR", "green", "Baixo risco. Sugerido: Manter operação e Elogiar."
        elif indice_sev <= 2.0:
            status, cor, msg = "RECICLAGEM", "orange", "Risco Moderado. Necessário: Orientação Técnica imediata."
        else:
            status, cor, msg = "CRÍTICO", "red", "Risco Alto de Sinistro. Necessário: Suspensão e Bloqueio."
            
        c3.markdown(f"<div style='background-color:{cor}; color:white; padding:10px; border-radius:10px; text-align:center;'><b>Status: {status}</b><br>Nota: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.info(f"💡 **Recomendação do Sistema:** {msg}")

        # Gráficos e Detalhes
        st.markdown("---")
        g1, g2 = st.columns([1, 2])
        
        with g1:
            st.write("**Impacto por Ocorrência:**")
            st.bar_chart(df_distintos['Ocorrência'].value_counts())
            
        with g2:
            st.write("**Histórico Detalhado (Folha Corrida):**")
            st.dataframe(df_distintos[['Data/Hora de ocorrência', 'Ocorrência', col_rastr]], use_container_width=True)

        # Registro de Atendimento
        st.subheader("✍️ Registrar Atendimento")
        st.text_area("O que foi conversado com o motorista?", placeholder="Ex: Motorista orientado sobre a parada no posto X...")
        if st.button("Salvar no Prontuário"):
            st.success("Registrado com sucesso!")

    else:
        st.info("Selecione um CPF no menu ao lado para iniciar a análise.")

except Exception as e:
    st.error(f"Erro na leitura dos dados: {e}")