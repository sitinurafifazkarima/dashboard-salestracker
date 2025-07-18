# dashboard_salestracker.py

import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

# Setup page
st.set_page_config("Dashboard Aktivitas Sales", layout="wide")
st.title("📊 Dashboard Aktivitas Sales")
st.caption("Versi interaktif dari hasil analisis - by Rima Nurafifa")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("sales_visits_finalbgt_enriched.csv", parse_dates=["Tanggal"])
    return df

df = load_data()

# Filter: tanggal
st.sidebar.header("🧭 Filter Data")
tanggal_awal, tanggal_akhir = st.sidebar.date_input("Pilih Rentang Tanggal", [df["Tanggal"].min(), df["Tanggal"].max()])
filtered_df = df[(df["Tanggal"] >= pd.to_datetime(tanggal_awal)) & (df["Tanggal"] <= pd.to_datetime(tanggal_akhir))]

# Ringkasan metrik
st.subheader("🔢 Ringkasan Aktivitas")
col1, col2, col3 = st.columns(3)
col1.metric("Total Customer Aktif", filtered_df["ID_Customer"].nunique())
col2.metric("Total Kunjungan", len(filtered_df))
col3.metric("Total Nilai Kontrak", f"Rp {filtered_df['Nilai_Kontrak'].sum():,.0f}")

# Kontrak terakhir per customer
latest_contracts = filtered_df.sort_values("Tanggal").groupby("ID_Customer").last()

# Pie Chart: Status Kontrak
st.subheader("📍 Distribusi Status Kontrak (Kontrak Terakhir per Customer)")
status_map = {'batal': 'Batal/Cancel', 'cancel': 'Batal/Cancel', 'deal': 'Deal', 'berpotensi deal': 'Berpotensi Deal'}
status_counts = latest_contracts["Status_Kontrak"].str.lower().replace(status_map).value_counts()
fig1 = px.pie(values=status_counts.values, names=status_counts.index, color_discrete_sequence=["#F4978E", "#A8D5BA", "#FFD97D"])
st.plotly_chart(fig1, use_container_width=True)

# Bar Chart: Distribusi Segmen & Tahap Funnel
st.subheader("📌 Distribusi Segmen dan Tahap Kunjungan")
col4, col5 = st.columns(2)

with col4:
    segmen_count = filtered_df.groupby("Segmen")["ID_Customer"].nunique().sort_values(ascending=False)
    fig2 = px.bar(segmen_count, x=segmen_count.index, y=segmen_count.values, labels={"x": "Segmen", "y": "Jumlah Customer"}, color_discrete_sequence=["#92A8D1"])
    st.plotly_chart(fig2, use_container_width=True)

with col5:
    tahap_order = ["Inisiasi", "Presentasi", "Penawaran Harga", "Negosiasi", "Paska Deal"]
    tahap_count = filtered_df["Progress"].value_counts().reindex(tahap_order).fillna(0)
    fig3 = px.bar(tahap_count, x=tahap_count.index, y=tahap_count.values, labels={"x": "Tahap", "y": "Jumlah Kunjungan"}, color_discrete_sequence=["#B5EAD7"])
    st.plotly_chart(fig3, use_container_width=True)

# Line Chart: Tren Kunjungan Mingguan
st.subheader("📈 Tren Jumlah Kunjungan per Minggu")
weekly_visits = filtered_df.groupby(pd.Grouper(key="Tanggal", freq="W"))["ID_Customer"].count().reset_index()
fig4 = px.line(weekly_visits, x="Tanggal", y="ID_Customer", markers=True, labels={"ID_Customer": "Jumlah Kunjungan"}, line_shape="spline", color_discrete_sequence=["#FFB7B2"])
st.plotly_chart(fig4, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Dibuat oleh Rima dengan ❤️ pakai Streamlit dan Plotly. Kalau Hapis buka ini, senyum yaa 😚")
