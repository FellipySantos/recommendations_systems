
# app_streamlit_regras.py
# QuantumFinance - Regras + Explainability + Métricas (Open Finance)
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="QuantumFinance - Regras + Explainability", layout="wide")

# ================== Utils ==================
@st.cache_data
def load_data():
    users = pd.read_csv("users.csv")
    products = pd.read_csv("products.csv")
    transactions = pd.read_csv("transactions.csv")
    interactions = pd.read_csv("interactions.csv")
    return users, products, transactions, interactions


def compute_user_features(users, transactions):
    gastos_sum = transactions.groupby("user_id")["gasto_mensal"].sum().to_dict()
    viagens_sum = transactions[transactions["categoria"]=="viagens"].groupby("user_id")["gasto_mensal"].sum().to_dict()
    feats = {}
    for _, u in users.iterrows():
        uid = int(u["user_id"])
        renda = float(u["renda"])
        gastos = float(gastos_sum.get(uid, 0.0))
        sobra = renda - gastos
        g_viagens = float(viagens_sum.get(uid, 0.0))
        ratio_viagens = (g_viagens / renda) if renda > 0 else 0.0
        feats[uid] = {
            "renda": renda,
            "score_credito": float(u["score_credito"]),
            "dividas": float(u["dividas"]),
            "sobra": sobra,
            "gasto_viagens": g_viagens,
            "ratio_viagens": ratio_viagens
        }
    return feats

def regras_explainability(uid, feats):
    recs, just = [], []
    f = feats[uid]
    renda, score, dividas = f["renda"], f["score_credito"], f["dividas"]
    sobra, ratio_viagens = f["sobra"], f["ratio_viagens"]

    # Regra 1: Sobra mensal alta
    if sobra > 2000:
        recs.append(103)  
        just.append(f"Oferecemos CDB Liquidez Diária porque você tem sobra de caixa mensal de R${sobra:.0f}.")
        recs.append(106)  
        just.append(f"Sobra de R${sobra:.0f}/mês: previdência ajuda no planejamento de longo prazo.")
    # Regra 2: Viagens relevantes
    if ratio_viagens > 0.09:
        recs.append(107)  
        just.append(f"Seus gastos com viagens representam {ratio_viagens*100:.1f}% da renda; cartão com milhas maximiza benefícios.")
        recs.append(104) 
        just.append("Viagens frequentes: seguro viagem oferece assistência e proteção.")
    # Regra 3: Dívidas altas
    if dividas > renda*0.6:
        recs.append(102) 
        just.append(f"Dívidas de R${dividas:.0f} (>60% da renda). Consignado pode reduzir juros e organizar o fluxo.")
    # Regra 4: Score alto + sobra → renda fixa
    if score >= 750 and sobra > 1000:
        if 103 not in recs:
            recs.append(103)
            just.append("Score alto + sobra mensal: renda fixa com liquidez é aderente ao seu perfil.")

    seen = set(); final_recs=[]; final_just=[]
    for pid, j in zip(recs, just):
        if pid not in seen:
            final_recs.append(pid); final_just.append(j); seen.add(pid)
    return final_recs, final_just

st.title("QuantumFinance — Open Finance")

users, products, transactions, interactions = load_data()
feats = compute_user_features(users, transactions)

col1, col2 = st.columns([1,2])
with col1:
    nome_sel = st.selectbox("Selecione o cliente", users["nome"])
    uid = int(users.loc[users["nome"]==nome_sel, "user_id"].values[0])
    f = feats[uid]
    st.subheader("Perfil:")
    st.write(f"**Renda:** R${f['renda']:.2f}")
    st.write(f"**Score de crédito:** {f['score_credito']:.0f}")
    st.write(f"**Dívidas:** R${f['dividas']:.2f}")
    st.write(f"**Gastos mensais (total):** R${(f['renda']-f['sobra']):.2f}")
    st.write(f"**Sobra mensal:** R${f['sobra']:.2f}")
    st.write(f"**Gastos em viagens:** R${f['gasto_viagens']:.2f} ({f['ratio_viagens']*100:.1f}% da renda)")
with col2:
    st.subheader("Recomendações (Regras + Explicações)")
    recs, just = regras_explainability(uid, feats)
    if len(recs)==0:
        st.info("Nenhuma recomendação pelas regras atuais para este perfil.")
    else:
        for pid, j in zip(recs, just):
            nome_prod = products.loc[products["product_id"]==pid, "nome_produto"].values[0]
            st.success(f"👉 **{nome_prod}** — {j}")

