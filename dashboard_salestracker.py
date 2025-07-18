import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Load data
df = pd.read_csv("sales_visits_finalbgt_enriched.csv")
df['Tanggal'] = pd.to_datetime(df['Tanggal'])

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

# Navigasi halaman
page = st.sidebar.selectbox("Pilih Halaman", ["📊 Overview", "🔁 Funnel & Konversi", "👤 Profil Sales"])

if page == "📊 Overview":
    st.title("SalesLens 360 – Aktivitas & Kinerja Tim Sales")

    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        total_cust = filtered_df['ID_Customer'].nunique()
        st.metric("Customer Aktif", total_cust)
        st.caption("⬤ Banyak customer yang sedang dijalankan")
    with col2:
        total_visit = filtered_df.shape[0]
        st.metric("Total Kunjungan", total_visit)
        st.caption("⬤ Intensitas kunjungan cukup tinggi")
    with col3:
        total_kontrak = filtered_df['Nilai_Kontrak'].sum()
        st.metric("Nilai Kontrak", f"Rp {total_kontrak/1e6:.1f} Juta")
        st.caption("⬤ Potensi nilai proyek saat ini")
    with col4:
        deal = filtered_df[filtered_df['Progress'] == 'Paska Deal']['ID_Customer'].nunique()
        percent = (deal / total_cust * 100) if total_cust else 0
        st.metric("Customer Deal", f"{deal} ({percent:.1f}%)")
        st.caption("⬤ Tingkat closing sementara")
    with col5:
        progress_map = {'Inisiasi': 1, 'Presentasi': 2, 'Penawaran Harga': 3, 'Negosiasi': 4, 'Paska Deal': 5}
        progress_val = filtered_df['Progress'].map(progress_map).mean()
        st.metric("Progress Funnel", f"{progress_val:.1f} / 5")
        st.caption("⬤ Rata-rata tahap berjalan")

    # Funnel Chart
    st.subheader("Funnel Aktivitas Sales")
    funnel_counts = filtered_df['Progress'].value_counts().reindex(progress_map.keys())
    funnel_fig = px.funnel_area(names=funnel_counts.index, values=funnel_counts.values,
                                title="Jumlah Customer di Tiap Tahap", color_discrete_sequence=px.colors.sequential.Teal)
    st.plotly_chart(funnel_fig)

    # Trend Aktivitas Waktu
    st.subheader("Trend Kunjungan Mingguan")
    trend_df = filtered_df.copy()
    trend_df['Minggu'] = trend_df['Tanggal'].dt.to_period("W").astype(str)
    kunjungan_per_week = trend_df.groupby('Minggu').size().reset_index(name='Kunjungan')
    kontrak_per_week = trend_df.groupby('Minggu')['Nilai_Kontrak'].sum().reset_index()
    trend = pd.merge(kunjungan_per_week, kontrak_per_week, on='Minggu')
    trend_fig = px.line(trend, x='Minggu', y='Kunjungan', markers=True, title="Jumlah Kunjungan per Minggu")
    trend_fig.add_bar(x=trend['Minggu'], y=trend['Nilai_Kontrak'], name="Nilai Kontrak", marker_color="#9AD0EC")
    st.plotly_chart(trend_fig)

    # Distribusi Segmen dan Status
    st.subheader("Distribusi Segmen & Status Customer")
    col1, col2 = st.columns(2)
    with col1:
        pie_seg = px.pie(filtered_df, names='Segmen', title="Distribusi Segmen",
                         color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(pie_seg)
    with col2:
        pie_stat = px.pie(filtered_df, names='Status_Customer', title="Status Customer",
                          color_discrete_sequence=px.colors.sequential.Greens)
        st.plotly_chart(pie_stat)

    # Heatmap Segmen vs Progress
    st.subheader("Heatmap Segmen vs Tahap Tertinggi")
    heat_data = pd.crosstab(filtered_df['Segmen'], filtered_df['Progress'])
    st.dataframe(heat_data.style.background_gradient(cmap='YlGnBu'))

elif page == "🔁 Funnel & Konversi":
    st.title("Sales Funnel & Konversi Detail")
    
    # Funnel per Sales
    st.subheader("Perbandingan Funnel per Sales")
    funnel_sales = filtered_df.groupby(['Nama_Sales', 'Progress']).size().reset_index(name='Jumlah')
    funnel_sales_fig = px.bar(funnel_sales, x='Progress', y='Jumlah', color='Nama_Sales', barmode='group',
                              color_discrete_sequence=px.colors.qualitative.Pastel, title="Funnel per Sales")
    st.plotly_chart(funnel_sales_fig)

    # Durasi Konversi
    st.subheader("Durasi vs Nilai Kontrak")
    durasi_df = filtered_df.sort_values(by=['ID_Customer', 'Tanggal'])
    durasi_df = durasi_df.groupby('ID_Customer').agg({
        'Tanggal': ['min', 'max'],
        'Nilai_Kontrak': 'max',
        'Nama_Sales': 'first'
    })
    durasi_df.columns = ['Start', 'End', 'Nilai_Kontrak', 'Nama_Sales']
    durasi_df['Durasi (Hari)'] = (durasi_df['End'] - durasi_df['Start']).dt.days
    durasi_fig = px.scatter(durasi_df, x='Durasi (Hari)', y='Nilai_Kontrak', color='Nama_Sales',
                            title="Durasi Konversi vs Nilai", color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(durasi_fig)

elif page == "👤 Profil Sales":
    st.title("Profil Individu Sales")
    sales_selected = st.selectbox("Pilih Nama Sales", df['Nama_Sales'].unique())
    df_sales = filtered_df[filtered_df['Nama_Sales'] == sales_selected]

    st.subheader("Ringkasan Sales")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Level", df_sales['Level_Sales'].iloc[0])
    with col2:
        st.metric("Jumlah Kunjungan", df_sales.shape[0])
    with col3:
        st.metric("Customer Unik", df_sales['ID_Customer'].nunique())

    st.metric("Rata-rata Progress", df_sales['Progress'].map(progress_map).mean())

    # Timeline Kunjungan
    st.subheader("Timeline Kunjungan")
    timeline_fig = px.timeline(df_sales, x_start='Tanggal', x_end='Tanggal', y='Nama_Customer',
                               color='Progress', hover_data=['Jenis_Kunjungan', 'Catatan'],
                               color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(timeline_fig)

    # Distribusi Aktivitas
    st.subheader("Distribusi Jenis Kunjungan")
    aktivitas_fig = px.pie(df_sales, names='Jenis_Kunjungan', title="Distribusi Aktivitas Sales",
                           color_discrete_sequence=px.colors.sequential.PuBu)
    st.plotly_chart(aktivitas_fig)

    st.info("\n\n🧠 Rekomendasi AI: \n- Perkuat dokumentasi kunjungan yang membawa deal\n- Berpotensi jadi mentor EAM baru")
