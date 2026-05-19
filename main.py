import streamlit as st
import pandas as pd
from io import BytesIO
import os
import signal
import threading
import time
from streamlit.runtime import get_instance


# --- FUNÇÃO DE AUTO-ENCERRAMENTO ---
def monitorar_conexoes():
    """Verifica se há sessões ativas. Se o navegador fechar, encerra o Python."""
    while True:
        time.sleep(10)  # Checa a cada 10 segundos
        try:
            runtime = get_instance()
            sessions = runtime._session_mgr.list_active_sessions()
            if not sessions:
                os.kill(os.getpid(), signal.SIGTERM)
        except:
            pass


# Inicia o monitoramento em segundo plano
t = threading.Thread(target=monitorar_conexoes, daemon=True)
t.start()


# --- LÓGICA DE TRATAMENTO ---
def converter_letra_para_indice(letra):
    letra = letra.upper()
    resultado = 0
    for char in letra:
        resultado = resultado * 26 + (ord(char) - ord('A') + 1)
    return resultado - 1


def tratar_planilha(df_origem, num_fatura):
    df_final = pd.DataFrame()
    # Pega apenas linhas onde a coluna A original (índice 0) tenha conteúdo
    mask = df_origem.iloc[:, 0].notna()
    df_dados = df_origem[mask].copy()

    df_final['FATURA'] = [num_fatura] * len(df_dados)

    idx_a = converter_letra_para_indice('A')
    idx_y = converter_letra_para_indice('Y')
    df_final['PARTNUMBER'] = (df_dados.iloc[:, idx_a].astype(str) + " - " + df_dados.iloc[:, idx_y].astype(str))

    df_final['QUANTIDADE'] = df_dados.iloc[:, converter_letra_para_indice('F')]
    df_final['PESOUNITARIO'] = df_dados.iloc[:, converter_letra_para_indice('G')]
    df_final['PRECOUNITARIO'] = df_dados.iloc[:, converter_letra_para_indice('K')]
    df_final['MOEDA'] = df_dados.iloc[:, converter_letra_para_indice('U')]
    df_final['INCOTERM'] = 'CIP'
    df_final['UNIDADE'] = df_dados.iloc[:, converter_letra_para_indice('D')]

    return df_final


# --- INTERFACE ---
st.set_page_config(page_title="Tratador de Faturas", layout="wide")
st.title("📂 Processador de Planilhas de Fatura")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("1. Anexe a planilha original (.xlsx)", type=["xlsx"])
with col2:
    num_fatura = st.text_input("2. Digite o número da FATURA:")

if uploaded_file and num_fatura:
    if st.button("🚀 Processar e Gerar Download"):
        try:
            # skiprows=1 pula o cabeçalho original (Linha 1)
            df_input = pd.read_excel(uploaded_file, skiprows=1, header=None)

            if df_input.empty:
                st.error("A planilha não possui dados após a linha 1.")
            else:
                df_resultado = tratar_planilha(df_input, num_fatura)
                st.success("Dados processados com sucesso!")
                st.dataframe(df_resultado.head(10))

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_resultado.to_excel(writer, index=False, sheet_name='Tratado')

                st.download_button(
                    label="📥 Baixar Planilha Tratada",
                    data=output.getvalue(),
                    file_name=f"Fatura_{num_fatura}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Erro: {e}")