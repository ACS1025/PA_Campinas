import streamlit as st
import pandas as pd
import re

# ... (Configurações de CSS e Header permanecem as mesmas) ...

try:
    df_oc_bruto, df_des_bruto = carregar_dados()
    
    # Mapeamento dinâmico
    col_cpf = encontrar_coluna(df_oc_bruto, ["CPF"])
    col_mot = encontrar_coluna(df_oc_bruto, ["MOTORISTA"])
    col_evento = encontrar_coluna(df_oc_bruto, ["DESCRIÇÃO", "OCORRÊNCIA"])
    col_rastr = encontrar_coluna(df_oc_bruto, ["RASTREAMENTO", "CÓDIGO"])
    col_data = "Data Inserção" 

    df_oc_bruto["cpf_limpo"] = df_oc_bruto[col_cpf].apply(limpar_cpf)
    lista_cpfs = sorted(df_oc_bruto[col_cpf].dropna().unique())
    
    cpf_selecionado = st.sidebar.selectbox("Selecione o CPF:", [""] + list(lista_cpfs))

    if cpf_selecionado:
        cpf_limpo_sel = limpar_cpf(cpf_selecionado)
        df_mot = df_oc_bruto[df_oc_bruto["cpf_limpo"] == cpf_limpo_sel].copy()
        nome_mot = df_mot[col_mot].iloc[0] if col_mot else "Motorista"

        # --- BUSCA DE DADOS DA ABA DESEMPENHO (Conforme PDF) ---
        total_sm_planilha, nota_val, peso_val = 0, 0.0, 0.0
        for r in range(len(df_des_bruto)):
            if cpf_limpo_sel in limpar_cpf(str(df_des_bruto.iloc[r, :])):
                sub_matriz = df_des_bruto.iloc[r-2 : r+15].astype(str).values.flatten().tolist()
                for i, texto in enumerate(sub_matriz):
                    t_up = texto.upper().strip()
                    try:
                        if "TOTAL DE SM" in t_up: total_sm_planilha = float(sub_matriz[i+1].replace(",", "."))
                        elif "NOTA AVALIAÇÃO" in t_up: nota_val = float(sub_matriz[i+1].replace(",", "."))
                        elif "PESO DE IMPACTO" in t_up: peso_val = float(sub_matriz[i+1].replace(",", "."))
                    except: continue
                break

        # --- LÓGICA DE IMPACTO DO RELATÓRIO ORIGINAL ---
        # No seu PDF aparecem: PARADA PERNOITE, PERNOITE EXCEDIDO, etc.
        df_historico_risco = df_mot[df_mot[col_evento].str.upper().str.contains("ROTA|PARADA|PERNOITE|AUTORIZADO", na=False)].copy()
        df_historico_risco = df_historico_risco.drop_duplicates(subset=[col_rastr, col_evento, col_data])

        # Mapeamento de Pesos conforme o Relatório PDF
        mapa_pesos = {
            "DESVIO DE ROTA": 5,
            "PARADA NÃO INFORMADA": 4,
            "PARADA EXCEDIDA": 4,
            "PERNOITE EXCEDIDO": 3,
            "PARADA EM LOCAL NÃO AUTORIZADO": 3,
            "PARADA PERNOITE": 3 # Adicionado conforme seu histórico
        }
        df_historico_risco["Peso"] = df_historico_risco[col_evento].str.upper().map(mapa_pesos).fillna(1)
        
        total_sm_final = total_sm_planilha if total_sm_planilha > 0 else 1
        indice_sev = df_historico_risco["Peso"].sum() / total_sm_final

        # Classificação baseada no Índice 3.75 do PDF (ALTO RISCO)
        if indice_sev <= 1.5: status, cor = "DIAMANTE", "#28a745"
        elif indice_sev <= 3.0: status, cor = "MODERADO", "#fd7e14"
        else: status, cor = "ALTO RISCO", "#dc3545"

        # --- INTERFACE (IGUAL AO PDF) ---
        st.markdown(f"## Comportamento do Motorista (PGR)")
        st.markdown(f"### Análise Crítica: {nome_mot}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Viagens (SM)", int(total_sm_final))
        c2.metric("Ocorrências Avaliadas", len(df_historico_risco))
        with c3: st.markdown(f"<div style='background:{cor};color:white;padding:10px;border-radius:10px;text-align:center;'><b>{status}</b><br>Indice: {indice_sev:.2f}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Resumo da Avaliação (Aba Desempenho)")
        ca, cb = st.columns(2)
        ca.metric("Nota da Avaliação", f"{nota_val:.1f}")
        cb.metric("Peso de Impacto", f"{peso_val:.2f}")

        # --- IMPACTO POR OCORRÊNCIA (A visualização por contagem do PDF) ---
        st.markdown("#### Impacto por Ocorrência (Apenas Avaliadas):")
        contagem = df_historico_risco[col_evento].value_counts().reset_index()
        contagem.columns = ['Ocorrência', 'Qtd']
        st.dataframe(contagem, use_container_width=True)

        st.markdown("#### Histórico Completo / Desempenho Detalhado")
        st.table(df_historico_risco[[col_rastr, col_data, col_evento]])

except Exception as e:
    st.error(f"Erro ao restaurar relatório: {e}")