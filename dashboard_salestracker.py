import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# Setup halaman
st.set_page_config("Layer 1: Overview", layout="wide")
st.title("📊 SalesTracker Dashboard - Layer 1: Overview")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("sales_visits_finalbgt_enriched.csv", parse_dates=["Tanggal"])
    latest_contracts = df.sort_values("Tanggal").groupby("ID_Customer").last()
    return df, latest_contracts

df, latest_contracts = load_data()

# ---- METRIK TINGKAT TINGGI ----
total_customer = df["ID_Customer"].nunique()
total_kunjungan = len(df)
total_nilai_kontrak = df["Nilai_Kontrak"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Customer Aktif", total_customer)
col2.metric("Total Kunjungan", total_kunjungan)
col3.metric("Total Nilai Kontrak", f"Rp {total_nilai_kontrak:,.0f}")

st.markdown("---")

# ---- PIE CHART STATUS KONTRAK ----
st.subheader("📍 Distribusi Status Kontrak (Kontrak Terakhir per Customer)")
status_map = {'batal': 'Batal/Cancel', 'cancel': 'Batal/Cancel', 'deal': 'Deal', 'berpotensi deal': 'Berpotensi Deal'}
status_kontrak_dist = latest_contracts["Status_Kontrak"].str.lower().replace(status_map).value_counts()
fig1 = px.pie(
    values=status_kontrak_dist.values,
    names=status_kontrak_dist.index,
    color_discrete_sequence=["#F44336", "#4CAF50", "#FFC107"]
)
st.plotly_chart(fig1, use_container_width=True)

# ---- BAR CHART: SEGMENT & TAHAP ----
col4, col5 = st.columns(2)

with col4:
    segment_dist = df.groupby("Segmen")["ID_Customer"].nunique().sort_values(ascending=False)
    fig2 = px.bar(segment_dist, x=segment_dist.index, y=segment_dist.values,
                  labels={"x": "Segmen", "y": "Jumlah Customer"}, color_discrete_sequence=["#6ECEDA"])
    st.subheader("🔷 Distribusi Customer per Segmen")
    st.plotly_chart(fig2, use_container_width=True)

with col5:
    tahap_order = ["Inisiasi", "Presentasi", "Penawaran Harga", "Negosiasi", "Paska Deal"]
    tahap_dist = df["Progress"].value_counts().reindex(tahap_order).fillna(0)
    fig3 = px.bar(tahap_dist, x=tahap_dist.index, y=tahap_dist.values,
                  labels={"x": "Tahap", "y": "Jumlah Kunjungan"}, color_discrete_sequence=["#FFDDC1"])
    st.subheader("🔶 Distribusi Kunjungan per Tahap")
    st.plotly_chart(fig3, use_container_width=True)

# ---- LINE CHART: WEEKLY VISITS ----
st.subheader("📈 Tren Jumlah Kunjungan per Minggu")
weekly_visits = df.groupby(pd.Grouper(key="Tanggal", freq="W"))["ID_Customer"].count().reset_index()
fig4 = px.line(weekly_visits, x="Tanggal", y="ID_Customer", markers=True,
               labels={"ID_Customer": "Jumlah Kunjungan"}, line_shape="spline", color_discrete_sequence=["#FFB7B2"])
st.plotly_chart(fig4, use_container_width=True)

# ---- PIE CHART: NILAI KONTRAK BREAKDOWN ----
st.subheader("💰 Breakdown Nilai Kontrak (Latest per Customer)")

nilai_kontrak_aktual = latest_contracts[
    (latest_contracts['Progress'] == 'Paska Deal') &
    (latest_contracts['Status_Kontrak'].str.lower() == 'deal')
]['Nilai_Kontrak'].sum()

nilai_kontrak_prospek = latest_contracts[
    (latest_contracts['Progress'] != 'Paska Deal') &
    (latest_contracts['Status_Kontrak'].str.lower() == 'berpotensi deal')
]['Nilai_Kontrak'].sum()

nilai_kontrak_lost = latest_contracts[
    latest_contracts['Status_Kontrak'].str.lower().isin(['cancel', 'batal'])
]['Nilai_Kontrak'].sum()

total_nilai_project = latest_contracts["Nilai_Kontrak"].sum()

fig5 = px.pie(
    values=[nilai_kontrak_aktual, nilai_kontrak_prospek, nilai_kontrak_lost],
    names=[
        f"Pendapatan Riil\nRp {nilai_kontrak_aktual:,.0f}",
        f"Prospek (Forecast)\nRp {nilai_kontrak_prospek:,.0f}",
        f"Lost/Cancel\nRp {nilai_kontrak_lost:,.0f}"
    ],
    title="Breakdown Nilai Kontrak",
    color_discrete_sequence=["#4CAF50", "#FFC107", "#F44336"]
)
st.plotly_chart(fig5, use_container_width=True)

# Penutup
st.markdown("---")
st.caption("Layer 1 selesai! Lanjutkan ke Layer 2 untuk eksplorasi funnel 🎯")
