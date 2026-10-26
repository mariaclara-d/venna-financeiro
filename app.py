from datetime import date
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="VENNA – Custos de Abertura", page_icon="💎", layout="centered")

def db():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def init():
    with db() as c:
        c.cursor().execute("""CREATE TABLE IF NOT EXISTS custos(
            id SERIAL PRIMARY KEY,
            data TEXT,
            categoria TEXT,
            descricao TEXT,
            fornecedor TEXT,
            valor REAL,
            status TEXT,
            observacoes TEXT)""")

def brl(v):
    return ("R$ " + f"{float(v or 0):,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")

CATEGORIAS = [
    "Abertura / registro da empresa",
    "Contabilidade",
    "Design e identidade visual",
    "Marketing / tráfego pago",
    "Software / ferramentas",
    "Taxas e tarifas",
    "Combustível e deslocamento",
    "Outros",
]

init()

st.title("💎 VENNA — Custos de Abertura")
pagina = st.sidebar.radio("Menu", ["Painel", "Novo custo", "Histórico"])

if pagina == "Painel":
    with db() as c:
        dados = pd.read_sql_query("SELECT * FROM custos", c)

    pago = dados.loc[dados.status == "Pago", "valor"].sum() if not dados.empty else 0
    pendente = dados.loc[dados.status == "Pendente", "valor"].sum() if not dados.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total pago", brl(pago))
    col2.metric("Total pendente", brl(pendente))
    col3.metric("Total geral", brl(pago + pendente))

    st.divider()
    st.subheader("Últimos registros")

    if dados.empty:
        st.info("Nenhum custo registrado ainda.")
    else:
        st.dataframe(
            dados.sort_values("id", ascending=False).head(10)[["data", "categoria", "descricao", "fornecedor", "valor", "status"]],
            use_container_width=True,
            hide_index=True,
        )

elif pagina == "Novo custo":
    st.subheader("Registrar custo")

    for k, v in {"data": date.today(), "status": "Pago", "categoria": CATEGORIAS[0],
                 "descricao": "", "valor": "", "fornecedor": "", "obs": ""}.items():
        if k not in st.session_state:
            st.session_state[k] = v

    col1, col2 = st.columns(2)
    col1.date_input("Data", key="data")
    col2.selectbox("Status", ["Pago", "Pendente", "Cancelado"], key="status")
    st.selectbox("Categoria", CATEGORIAS, key="categoria")
    st.text_input("Descrição", placeholder="Ex.: registro na Junta Comercial", key="descricao")
    col1, col2 = st.columns(2)
    col1.text_input("Valor (R$)", placeholder="Ex.: 1500,00", key="valor")
    col2.text_input("Fornecedor (opcional)", key="fornecedor")
    st.text_area("Observações", height=80, key="obs")

    if st.button("Salvar", type="primary"):
        valor_str = st.session_state.valor.strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        try:
            valor_float = float(valor_str)
        except ValueError:
            valor_float = 0.0

        if not st.session_state.descricao.strip() or valor_float <= 0:
            st.error("Informe uma descrição e um valor válido (ex.: 1500,00).")
        else:
            with db() as c:
                c.cursor().execute(
                    "INSERT INTO custos(data,categoria,descricao,fornecedor,valor,status,observacoes) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (st.session_state.data.isoformat(), st.session_state.categoria,
                     st.session_state.descricao.strip(), st.session_state.fornecedor.strip(),
                     valor_float, st.session_state.status, st.session_state.obs.strip()),
                )
            st.success(f"Custo de {brl(valor_float)} registrado com sucesso!")

else:
    st.subheader("Histórico de custos")
    with db() as c:
        dados = pd.read_sql_query("SELECT * FROM custos ORDER BY data DESC, id DESC", c)

    if dados.empty:
        st.info("Nenhum custo registrado ainda.")
    else:
        filtro = st.selectbox("Filtrar por status", ["Todos", "Pago", "Pendente", "Cancelado"])
        exibir = dados if filtro == "Todos" else dados[dados.status == filtro]
        exibir = exibir.copy()
        exibir["data"] = pd.to_datetime(exibir["data"]).dt.date

        st.metric("Total filtrado", brl(exibir.valor.sum()))
        st.caption("Clique em qualquer célula para editar. Clique em 'Salvar alterações' para confirmar.")

        editado = st.data_editor(
            exibir.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS),
                "descricao": st.column_config.TextColumn("Descrição"),
                "fornecedor": st.column_config.TextColumn("Fornecedor"),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0),
                "status": st.column_config.SelectboxColumn("Status", options=["Pago", "Pendente", "Cancelado"]),
                "observacoes": st.column_config.TextColumn("Observações"),
            },
        )

        if st.button("Salvar alterações", type="primary"):
            with db() as c:
                cur = c.cursor()
                for _, row in editado.iterrows():
                    data_str = row.data.isoformat() if hasattr(row.data, "isoformat") else str(row.data)[:10]
                    cur.execute(
                        """UPDATE custos SET data=%s, categoria=%s, descricao=%s, fornecedor=%s,
                        valor=%s, status=%s, observacoes=%s WHERE id=%s""",
                        (data_str, row.categoria, row.descricao, row.fornecedor,
                         row.valor, row.status, row.observacoes, int(row.id)),
                    )
            st.success("Alterações salvas!")

        st.download_button(
            "Exportar CSV",
            exibir.to_csv(index=False).encode("utf-8-sig"),
            "venna_custos_abertura.csv",
            "text/csv",
        )
