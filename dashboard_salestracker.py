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
page = st.sidebar.radio("Pilih Halaman", ["🟦 Overview", "🟦 Funnel & Konversi", "🟦 Profil Sales"])

if page == "🟦 Overview":
    st.title("SalesLens 360 – Aktivitas & Kinerja Tim Sales")

    # KPI Ringkasan
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        total_cust = filtered_df['ID_Customer'].nunique()
        st.metric("Customer Aktif", total_cust)
        st.caption("Progress rata-rata stagnan di tahap 3")
    with col2:
        total_visit = filtered_df.shape[0]
        st.metric("Total Kunjungan", total_visit)
        st.caption("Frekuensi kunjungan cukup stabil")
    with col3:
        total_kontrak = filtered_df['Nilai_Kontrak'].sum()
        st.metric("Total Nilai Kontrak", f"Rp {total_kontrak/1e6:.0f} Juta")
        st.caption("Nilai potensi proyek")
    with col4:
        deal_count = filtered_df[filtered_df['Progress'] == 'Paska Deal']['ID_Customer'].nunique()
        deal_percent = (deal_count / total_cust * 100) if total_cust else 0
        st.metric("Customer Deal", f"{deal_count} ({deal_percent:.0f}%)")
        st.caption("Konversi ke deal")
    with col5:
        avg_progress = filtered_df['Progress_Score'].mean()
        st.metric("Rata-rata Progress", f"{avg_progress:.1f} / 5")
        st.caption("Tahapan funnel rata-rata")

    # Funnel Aktivitas
    st.subheader("📉 Funnel Aktivitas Sales")
    funnel = filtered_df['Progress'].value_counts().reindex(progress_map.keys(), fill_value=0)
    funnel_fig = px.funnel_area(
        names=funnel.index,
        values=funnel.values,
        title="Funnel Aktivitas Berdasarkan Tahapan",
        color_discrete_sequence=px.colors.sequential.Teal_r
    )
    st.plotly_chart(funnel_fig)

    # Trend Mingguan
    st.subheader("📈 Trend Aktivitas Mingguan")
    filtered_df['Week'] = filtered_df['Tanggal'].dt.to_period("W").astype(str)
    kunjungan = filtered_df.groupby('Week').size().reset_index(name='Kunjungan')
    nilai_kontrak = filtered_df.groupby('Week')['Nilai_Kontrak'].sum().reset_index(name='Kontrak')
    trend_df = pd.merge(kunjungan, nilai_kontrak, on='Week')
    fig_trend = px.line(trend_df, x='Week', y='Kunjungan', markers=True, title="Kunjungan per Minggu")
    fig_trend.add_bar(x=trend_df['Week'], y=trend_df['Kontrak'], name="Nilai Kontrak",
                      marker_color='lightblue')
    st.plotly_chart(fig_trend)

    # Distribusi Segmen & Status
    st.subheader("📊 Distribusi Segmen & Status Customer")
    col1, col2 = st.columns(2)
    with col1:
        seg_fig = px.pie(filtered_df, names='Segmen', title='Distribusi Segmen',
                         color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(seg_fig)
    with col2:
        stat_fig = px.pie(filtered_df, names='Status_Customer', title='Status Customer',
                          color_discrete_sequence=px.colors.sequential.Greens)
        st.plotly_chart(stat_fig)

    st.subheader("Heatmap Segmen vs Tahapan")
    heatmap_df = pd.crosstab(filtered_df['Segmen'], filtered_df['Progress'])
    st.dataframe(heatmap_df.style.background_gradient(cmap="BuGn"))

elif page == "🟦 Funnel & Konversi":
    st.title("Funnel & Konversi Detail")

    # Funnel per Sales
    st.subheader("Funnel Komparatif per Sales")
    funnel_sales = filtered_df.groupby(['Nama_Sales', 'Progress']).size().reset_index(name='Jumlah')
    fig = px.bar(funnel_sales, x='Progress', y='Jumlah', color='Nama_Sales', barmode='group',
                 color_discrete_sequence=px.colors.sequential.Mint_r)
    st.plotly_chart(fig)

    # Durasi Konversi
    st.subheader("Durasi vs Nilai Kontrak")
    durasi = filtered_df.groupby('ID_Customer').agg(
        Sales=('Nama_Sales', 'first'),
        Start=('Tanggal', 'min'),
        End=('Tanggal', 'max'),
        Kontrak=('Nilai_Kontrak', 'max')
    ).reset_index()
    durasi['Durasi'] = (durasi['End'] - durasi['Start']).dt.days
    scatter_fig = px.scatter(durasi, x='Durasi', y='Kontrak', color='Sales',
                             title='Durasi Inisiasi → Deal vs Nilai Kontrak',
                             color_discrete_sequence=px.colors.sequential.RdBu_r)
    st.plotly_chart(scatter_fig)

    # Jeda antar kunjungan
    st.subheader("Rata-rata Jeda antar Kunjungan")
    jeda_df = filtered_df.sort_values(['ID_Customer', 'Tanggal'])
    jeda_df['Prev'] = jeda_df.groupby('ID_Customer')['Tanggal'].shift()
    jeda_df['Jeda_Hari'] = (jeda_df['Tanggal'] - jeda_df['Prev']).dt.days
    jeda_summary = jeda_df.groupby('Nama_Sales')['Jeda_Hari'].mean().reset_index()
    bar_jeda = px.bar(jeda_summary, x='Nama_Sales', y='Jeda_Hari', title="Jeda Rata-rata (Hari) per Sales",
                      color='Nama_Sales', color_discrete_sequence=px.colors.sequential.Plasma_r)
    st.plotly_chart(bar_jeda)

    # Timeline Journey
    st.subheader("Customer Journey Map")
    timeline = px.timeline(filtered_df, x_start='Tanggal', x_end='Tanggal', y='Nama_Customer', color='Progress',
                           hover_data=['Catatan', 'Jenis_Kunjungan'], color_discrete_sequence=px.colors.qualitative.Vivid)
    st.plotly_chart(timeline)

elif page == "🟦 Profil Sales":
    st.title("Profil Individu Sales")
    nama = st.selectbox("Pilih Sales", options=df['Nama_Sales'].unique())
    data_sales = filtered_df[filtered_df['Nama_Sales'] == nama]

    st.subheader("👤 Ringkasan Profil Sales")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nama", nama)
        st.metric("Level", data_sales['Level_Sales'].iloc[0])
    with col2:
        st.metric("Kunjungan", data_sales.shape[0])
        st.metric("Customer", data_sales['ID_Customer'].nunique())
    with col3:
        deal = data_sales[data_sales['Progress'] == 'Paska Deal']['ID_Customer'].nunique()
        st.metric("Jumlah Deal", deal)
        st.metric("Rata-rata Progress", f"{data_sales['Progress_Score'].mean():.1f} / 5")

    # Rata-rata durasi closing
    closing_df = data_sales.groupby('ID_Customer').agg(
        Start=('Tanggal', 'min'), End=('Tanggal', 'max')).reset_index()
    closing_df['Durasi'] = (closing_df['End'] - closing_df['Start']).dt.days
    st.metric("Rata-rata Durasi Closing", f"{closing_df['Durasi'].mean():.0f} Hari")

    # Timeline Vertikal
    st.subheader("📅 Timeline Kunjungan")
    timeline2 = px.timeline(data_sales, x_start='Tanggal', x_end='Tanggal', y='Kunjungan_Ke', color='Progress',
                            hover_data=['Jenis_Kunjungan', 'Catatan'],
                            color_discrete_sequence=px.colors.qualitative.Prism)
    st.plotly_chart(timeline2)

    # Jenis Aktivitas
    st.subheader("🔄 Distribusi Jenis Aktivitas")
    aktivitas = px.pie(data_sales, names='Jenis_Kunjungan', title='Distribusi Aktivitas',
                       color_discrete_sequence=px.colors.sequential.BuGn_r)
    st.plotly_chart(aktivitas)

    st.subheader("📘 Rekomendasi Pribadi")
    st.info("\n- Perkuat dokumentasi kunjungan yang membawa deal.\n- Berpotensi jadi mentor EAM baru.")