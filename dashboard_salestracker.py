import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# Load data
df = pd.read_csv("sales_visits_finalbgt_enriched.csv")
df['Tanggal'] = pd.to_datetime(df['Tanggal'])

# Progress mapping
progress_map = {'Inisiasi': 1, 'Presentasi': 2, 'Penawaran Harga': 3, 'Negosiasi': 4, 'Paska Deal': 5}
df['Progress_Score'] = df['Progress'].map(progress_map)

# Sidebar filters
st.sidebar.header("Filter Data")
date_range = st.sidebar.date_input("Pilih Rentang Tanggal", [df['Tanggal'].min(), df['Tanggal'].max()])
nama_sales = st.sidebar.multiselect("Nama Sales", options=df['Nama_Sales'].unique(), default=df['Nama_Sales'].unique())
segmen = st.sidebar.multiselect("Segmen", options=df['Segmen'].unique(), default=df['Segmen'].unique())
status_cust = st.sidebar.multiselect("Status Customer", options=df['Status_Customer'].unique(), default=df['Status_Customer'].unique())

# Filter data sesuai input
filtered_df = df[
    (df['Tanggal'] >= pd.to_datetime(date_range[0])) &
    (df['Tanggal'] <= pd.to_datetime(date_range[1])) &
    (df['Nama_Sales'].isin(nama_sales)) &
    (df['Segmen'].isin(segmen)) &
    (df['Status_Customer'].isin(status_cust))
]

# Halaman navigasi
page = st.sidebar.radio("Pilih Halaman", [
    "🟦 Layer 1 – Overview Aktivitas & Sales Funnel",
    "🟦 Layer 2 – Performa Individu & Profil Detail Sales",
    "🟦 Layer 3 – Segment-Customer Focus",
    "🟦 Layer 4 – Insight Otomatis & Rekomendasi Aksi"
])

if page == "🟦 Layer 1 – Overview Aktivitas & Sales Funnel":
    st.title("Layer 1 – Aktivitas & Funnel Sales")

    # KPI Ringkasan
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Customer Aktif", filtered_df['ID_Customer'].nunique())
    with col2:
        st.metric("Total Kunjungan", filtered_df.shape[0])
    with col3:
        st.metric("Total Nilai Kontrak", f"Rp {filtered_df['Nilai_Kontrak'].sum()/1e6:.0f} Juta")
    with col4:
        deal_count = filtered_df[filtered_df['Progress'] == 'Paska Deal']['ID_Customer'].nunique()
        st.metric("Jumlah Deal", deal_count)
    with col5:
        st.metric("Rata-rata Progress Funnel", f"{filtered_df['Progress_Score'].mean():.2f} / 5")

    st.subheader("📊 Funnel Aktivitas Sales")
    funnel = filtered_df['Progress'].value_counts().reindex(progress_map.keys(), fill_value=0)
    st.plotly_chart(px.funnel_area(names=funnel.index, values=funnel.values, title="Funnel Chart Tahapan"))

    st.subheader("📈 Aktivitas Sales Over Time")
    filtered_df['Week'] = filtered_df['Tanggal'].dt.to_period("W").astype(str)
    mingguan = filtered_df.groupby('Week').agg(Kunjungan=('Tanggal', 'count'), Kontrak=('Nilai_Kontrak', 'sum')).reset_index()
    fig = px.line(mingguan, x='Week', y='Kunjungan', markers=True)
    fig.add_bar(x=mingguan['Week'], y=mingguan['Kontrak'], name='Nilai Kontrak')
    st.plotly_chart(fig)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(filtered_df, names='Segmen', title='Distribusi Segmen'))
    with col2:
        st.plotly_chart(px.bar(filtered_df['Progress'].value_counts().reset_index(), x='index', y='Progress', title='Jumlah Kunjungan per Progress'))

    st.subheader("⏱️ Durasi & Frekuensi")
    durasi_df = filtered_df.groupby('ID_Customer').agg(start=('Tanggal', 'min'), end=('Tanggal', 'max'), kontrak=('Nilai_Kontrak', 'max'))
    durasi_df['Durasi'] = (durasi_df['end'] - durasi_df['start']).dt.days
    st.metric("Rata-rata Hari Inisiasi → Deal", f"{durasi_df['Durasi'].mean():.1f} hari")

    jeda_df = filtered_df.sort_values(['ID_Customer', 'Tanggal'])
    jeda_df['Prev'] = jeda_df.groupby('ID_Customer')['Tanggal'].shift()
    jeda_df['Jeda'] = (jeda_df['Tanggal'] - jeda_df['Prev']).dt.days
    st.metric("Rata-rata Jeda Antar Kunjungan", f"{jeda_df['Jeda'].mean():.1f} hari")

    st.plotly_chart(px.scatter(durasi_df.reset_index(), x='Durasi', y='kontrak', title='Durasi vs Nilai Kontrak'))

elif page == "🟦 Layer 2 – Performa Individu & Profil Detail Sales":
    st.title("Layer 2 – Profil Sales")
    leaderboard = filtered_df.groupby('Nama_Sales').agg(
        Jumlah_Kunjungan=('Tanggal', 'count'),
        Jumlah_Customer=('ID_Customer', 'nunique'),
        Nilai_Kontrak=('Nilai_Kontrak', 'sum'),
        Jumlah_Deal=('Progress', lambda x: (x == 'Paska Deal').sum()),
        Rata2_Progress=('Progress_Score', 'mean')
    ).reset_index()
    st.dataframe(leaderboard)
    st.plotly_chart(px.bar(leaderboard, x='Nama_Sales', y=['Jumlah_Kunjungan', 'Jumlah_Deal'], barmode='group'))

    nama = st.selectbox("Pilih Sales", options=filtered_df['Nama_Sales'].unique())
    data_sales = filtered_df[filtered_df['Nama_Sales'] == nama]
    st.metric("Customer", data_sales['ID_Customer'].nunique())
    st.metric("Jumlah Deal", (data_sales['Progress'] == 'Paska Deal').sum())
    st.metric("Rata-rata Progress", f"{data_sales['Progress_Score'].mean():.1f}")
    st.plotly_chart(px.timeline(data_sales, x_start='Tanggal', x_end='Tanggal', y='Nama_Customer', color='Progress'))
    st.plotly_chart(px.pie(data_sales, names='Jenis_Kunjungan', title='Distribusi Jenis Kunjungan'))

elif page == "🟦 Layer 3 – Segment-Customer Focus":
    st.title("Layer 3 – Segment-Customer Focus")
    st.plotly_chart(px.histogram(filtered_df, x='Segmen', color='Progress', barmode='group'))
    heatmap = pd.crosstab(filtered_df['Segmen'], filtered_df['Progress'])
    st.dataframe(heatmap.style.background_gradient(cmap="YlGnBu"))
    table = filtered_df.groupby(['Nama_Customer', 'Status_Customer', 'Segmen']).agg(
        Tahapan=('Progress', 'last'), Jumlah_Kunjungan=('Tanggal', 'count'),
        Tanggal_Terakhir=('Tanggal', 'max')).reset_index()
    st.dataframe(table)

elif page == "🟦 Layer 4 – Insight Otomatis & Rekomendasi Aksi":
    st.title("Layer 4 – Insight & Rekomendasi")

    top_sales = filtered_df.groupby('Nama_Sales')['Nilai_Kontrak'].sum().idxmax()
    st.success(f"Top Sales berdasarkan nilai kontrak: {top_sales}")

    drop_off = filtered_df['Progress'].value_counts().diff().fillna(0).abs().idxmax()
    st.warning(f"Tahap paling kritis (drop banyak): {drop_off}")

    seg_perf = filtered_df.groupby('Segmen')['Progress_Score'].mean().idxmin()
    st.error(f"Segmen dengan performa terendah: {seg_perf}")

    stagnant = filtered_df.groupby('ID_Customer')['Tanggal'].max()
    days_inactive = (datetime.today() - stagnant).dt.days
    if any(days_inactive > 20):
        st.warning("⚠️ Ada customer yang belum dikunjungi > 20 hari")

    st.subheader("📝 To-do List")
    st.info("- Follow-up customer stagnan\n- Pelatihan untuk tahap closing\n- Reminder otomatis mingguan")
