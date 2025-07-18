import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import pickle

# Custom soft & elegant CSS
st.markdown("""
    <style>
    .main {background-color: #f7f9fa;}
    .block-container {padding-top:2rem;}
    .stMetric {background: #e3f2fd; border-radius: 10px; box-shadow: 0 2px 8px #e0e0e0;}
    .stButton>button {background-color: #e3f2fd; color: #333; border-radius: 8px;}
    .stRadio>div {background: #f0f4f8; border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

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

page = st.sidebar.radio("Pilih Halaman", ["🟦 Overview", "🟦 Funnel & Konversi", "🟦 Profil Sales", "🟦 Insight & Rekomendasi"])

if page == "🟦 Overview":
    st.title("🟦 Dashboard Aktivitas & Kinerja Tim Sales")

    # Load metrik ringkasan tambahan dari pickle
    with open("overview_metrics.pkl", "rb") as f:
        overview_data = pickle.load(f)

    kontrak_summary = overview_data['nilai_kontrak_breakdown']

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
        color_discrete_sequence=px.colors.sequential.Teal
    )
    st.plotly_chart(funnel_fig)

        # 🎯 Analisis Funnel Sales Lanjutan
    st.subheader("📌 Insight Funnel Sales Tambahan")

    tahapan_funnel = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi', 'Paska Deal']
    
    # Hitung jumlah customer per tahapan funnel
    funnel_overall = {
        tahap: filtered_df[filtered_df['Progress'] == tahap]['ID_Customer'].nunique()
        for tahap in tahapan_funnel
    }

    # Hitung konversi antar tahap
    konversi_tahap = {}
    for i in range(len(tahapan_funnel) - 1):
        current = tahapan_funnel[i]
        next_ = tahapan_funnel[i + 1]
        if funnel_overall[current] > 0:
            konversi = (funnel_overall[next_] / funnel_overall[current]) * 100
            konversi_tahap[f"{current} → {next_}"] = konversi

    # Identifikasi drop-off terbesar
    drop_offs = {
        f"{tahapan_funnel[i]} → {tahapan_funnel[i+1]}":
            funnel_overall[tahapan_funnel[i]] - funnel_overall[tahapan_funnel[i+1]]
        for i in range(len(tahapan_funnel) - 1)
    }
    max_drop = max(drop_offs.items(), key=lambda x: x[1])

    # Tampilkan dalam format info box
    with st.expander("📊 Rincian Konversi Funnel dan Drop-off"):
        st.markdown("**🔄 Konversi Antar Tahap (%):**")
        for tahap, persen in konversi_tahap.items():
            st.markdown(f"- **{tahap}**: {persen:.1f}%")

        st.markdown("**⛔ Tahap dengan Drop-off Terbesar:**")
        st.warning(f"{max_drop[0]} dengan {max_drop[1]} customer drop.")

    # Analisis Funnel per Segmen
    funnel_segmen = {}
    for seg in filtered_df['Segmen'].dropna().unique():
        df_seg = filtered_df[filtered_df['Segmen'] == seg]
        funnel_segmen[seg] = {
            tahap: df_seg[df_seg['Progress'] == tahap]['ID_Customer'].nunique()
            for tahap in tahapan_funnel
        }

    segmen_df = pd.DataFrame(funnel_segmen).T.fillna(0).astype(int)
    st.subheader("🧭 Funnel per Segmen")
    st.dataframe(segmen_df.style.background_gradient(cmap="PuBuGn"))

    # Distribusi Segmen & Status
    st.subheader("📊 Distribusi Segmen & Status Customer")
    col1, col2 = st.columns(2)
    with col1:
        seg_fig = px.pie(filtered_df, names='Segmen', title='Distribusi Segmen',
                         color_discrete_sequence=px.colors.sequential.BuGn)
        st.plotly_chart(seg_fig)
    with col2:
        stat_fig = px.pie(filtered_df, names='Status_Customer', title='Status Customer',
                          color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(stat_fig)

    # Breakdown Nilai Kontrak Terakhir
        # Breakdown Nilai Kontrak Terakhir (warna diselaraskan)
    st.subheader("📌 Breakdown Nilai Kontrak (Customer Terakhir)")
    kontrak_labels = [
        f"Pendapatan Riil\nRp {kontrak_summary['pendapatan_riil']:,.0f}",
        f"Prospek (Forecast)\nRp {kontrak_summary['prospek']:,.0f}",
        f"Lost/Cancel\nRp {kontrak_summary['lost']:,.0f}"
    ]
    fig_kontrak = px.pie(
        names=['Riil', 'Prospek', 'Lost'],
        values=[
            kontrak_summary['pendapatan_riil'],
            kontrak_summary['prospek'],
            kontrak_summary['lost']
        ],
        title='Breakdown Nilai Kontrak (Latest per Customer)',
        color_discrete_sequence=['#26a69a', '#b2dfdb', '#80cbc4'],  # Warna lembut selaras
        hole=0.4
    )
    fig_kontrak.update_traces(textinfo='percent+label', textfont_size=14)
    st.plotly_chart(fig_kontrak)

    st.markdown(f"""
        <div style='background-color:#e8f5e9;padding:1rem;border-radius:10px;margin-top:1rem;'>
        <b>📈 Total Nilai Project:</b> Rp {kontrak_summary['total_project']:,.0f}<br>
        <b>✅ Pendapatan Riil:</b> {kontrak_summary['persen_riil']:.1f}%<br>
        <b>📊 Prospek:</b> {kontrak_summary['persen_prospek']:.1f}%<br>
        <b>❌ Lost:</b> {kontrak_summary['persen_lost']:.1f}%
        </div>
    """, unsafe_allow_html=True)

    # Heatmap Segmen vs Tahapan
    st.subheader("Heatmap Segmen vs Tahapan")
    heatmap_df = pd.crosstab(filtered_df['Segmen'], filtered_df['Progress'])
    st.dataframe(heatmap_df.style.background_gradient(cmap="PuBuGn"))

elif page == "🟦 Funnel & Konversi":
    st.title("🟦 Funnel & Konversi Detail")

    # Funnel per Sales
    st.subheader("Funnel Komparatif per Sales")
    funnel_sales = filtered_df.groupby(['Nama_Sales', 'Progress']).size().reset_index(name='Jumlah')
    fig = px.bar(funnel_sales, x='Progress', y='Jumlah', color='Nama_Sales', barmode='group',
                 color_discrete_sequence=px.colors.sequential.Teal)
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
                             color_discrete_sequence=px.colors.sequential.Mint)
    st.plotly_chart(scatter_fig)

    # Jeda antar kunjungan
    st.subheader("Rata-rata Jeda antar Kunjungan")
    jeda_df = filtered_df.sort_values(['ID_Customer', 'Tanggal'])
    jeda_df['Prev'] = jeda_df.groupby('ID_Customer')['Tanggal'].shift()
    jeda_df['Jeda_Hari'] = (jeda_df['Tanggal'] - jeda_df['Prev']).dt.days
    jeda_summary = jeda_df.groupby('Nama_Sales')['Jeda_Hari'].mean().reset_index()
    bar_jeda = px.bar(jeda_summary, x='Nama_Sales', y='Jeda_Hari', title="Jeda Rata-rata (Hari) per Sales",
                      color='Nama_Sales', color_discrete_sequence=px.colors.sequential.BuGn)
    st.plotly_chart(bar_jeda)

    # Analisis Durasi & Kunjungan
    st.subheader("⏳ Analisis Durasi & Frekuensi Kunjungan")
    # Durasi per customer
    customer_duration = filtered_df.groupby('ID_Customer').agg(
        Durasi_Total=('Tanggal', lambda x: (x.max() - x.min()).days),
        Progress_Akhir=('Progress', 'last')
    ).reset_index()
    deal_duration = customer_duration[customer_duration['Progress_Akhir'] == 'Paska Deal']['Durasi_Total']
    avg_gap = filtered_df.sort_values(['ID_Customer', 'Tanggal']).groupby('ID_Customer')['Tanggal'].diff().dt.days.dropna().mean()
    median_gap = filtered_df.sort_values(['ID_Customer', 'Tanggal']).groupby('ID_Customer')['Tanggal'].diff().dt.days.dropna().median()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rata-rata Durasi Closing (Paska Deal)", f"{deal_duration.mean():.1f} hari")
        st.caption(f"Median: {deal_duration.median():.1f} hari")
    with col2:
        st.metric("Rata-rata Jeda antar Kunjungan", f"{avg_gap:.1f} hari")
        st.caption(f"Median: {median_gap:.1f} hari")
    # Visualisasi distribusi durasi
    import plotly.graph_objects as go
    fig_durasi = go.Figure()
    fig_durasi.add_trace(go.Histogram(x=deal_duration, marker_color='#b2dfdb', name='Durasi Closing'))
    fig_durasi.update_layout(title="Distribusi Durasi Mencapai Paska Deal", xaxis_title="Durasi (hari)", yaxis_title="Frekuensi", template="plotly_white")
    st.plotly_chart(fig_durasi)
    # Visualisasi distribusi jeda kunjungan
    gaps = filtered_df.sort_values(['ID_Customer', 'Tanggal']).groupby('ID_Customer')['Tanggal'].diff().dt.days.dropna()
    fig_gap = go.Figure()
    fig_gap.add_trace(go.Histogram(x=gaps, marker_color='#80cbc4', name='Jeda Kunjungan'))
    fig_gap.update_layout(title="Distribusi Jeda antar Kunjungan", xaxis_title="Jeda (hari)", yaxis_title="Frekuensi", template="plotly_white")
    st.plotly_chart(fig_gap)

    # Leaderboard Sales
    st.subheader("🏆 Leaderboard Sales")
    sales_performance = filtered_df.groupby('Nama_Sales').agg(
        Total_Kunjungan=('ID_Customer', 'count'),
        Total_Nilai_Kontrak=('Nilai_Kontrak', 'sum'),
        Jumlah_Customer=('ID_Customer', 'nunique')
    )
    deals_per_sales = filtered_df[filtered_df['Progress'] == 'Paska Deal'].groupby('Nama_Sales')['ID_Customer'].nunique()
    sales_performance['Jumlah_Deal'] = deals_per_sales.fillna(0).astype(int)
    sales_performance['Closing_Rate'] = (sales_performance['Jumlah_Deal'] / sales_performance['Jumlah_Customer'] * 100).fillna(0).round(2)
    # Efisiensi waktu: rata-rata durasi closing per sales
    durasi_sales = filtered_df[filtered_df['Progress'] == 'Paska Deal'].groupby('Nama_Sales').apply(
        lambda x: (x.groupby('ID_Customer')['Tanggal'].max() - x.groupby('ID_Customer')['Tanggal'].min()).dt.days.mean()
    )
    sales_performance['Efisiensi_Waktu'] = durasi_sales.round(1)
    sales_performance['Efisiensi_Waktu'] = sales_performance['Efisiensi_Waktu'].fillna(0)
    # Ketercapaian target: deal/kunjungan
    sales_performance['Ketercapaian_Target'] = (sales_performance['Jumlah_Deal'] / sales_performance['Total_Kunjungan'] * 100).fillna(0).round(2)
    sales_performance = sales_performance.sort_values(['Jumlah_Deal', 'Closing_Rate', 'Ketercapaian_Target'], ascending=False)
    st.dataframe(sales_performance.style.background_gradient(cmap="PuBuGn"))
    # Visualisasi leaderboard
    fig_leader = go.Figure()
    fig_leader.add_trace(go.Bar(x=sales_performance.index, y=sales_performance['Jumlah_Deal'], name='Jumlah Deal', marker_color='#26a69a'))
    fig_leader.add_trace(go.Bar(x=sales_performance.index, y=sales_performance['Closing_Rate'], name='Closing Rate (%)', marker_color='#b2dfdb'))
    fig_leader.add_trace(go.Bar(x=sales_performance.index, y=sales_performance['Ketercapaian_Target'], name='Ketercapaian Target (%)', marker_color='#80cbc4'))
    fig_leader.update_layout(barmode='group', title="Leaderboard Sales: Deal, Closing Rate, Target", template="plotly_white")
    st.plotly_chart(fig_leader)

elif page == "🟦 Profil Sales":
    st.title("🟦 Profil Individu Sales")
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
                            color_discrete_sequence=px.colors.sequential.Mint)
    st.plotly_chart(timeline2)

    # Jenis Aktivitas
    st.subheader("🔄 Distribusi Jenis Aktivitas")
    aktivitas = px.pie(data_sales, names='Jenis_Kunjungan', title='Distribusi Aktivitas',
                       color_discrete_sequence=px.colors.sequential.BuGn)
    st.plotly_chart(aktivitas)

    st.subheader("📘 Rekomendasi Pribadi")
    st.info("\n- Perkuat dokumentasi kunjungan yang membawa deal.\n- Berpotensi jadi mentor EAM baru.")

# Halaman Insight & Rekomendasi
elif page == "🟦 Insight & Rekomendasi":
    st.title("🟦 Insight & Rekomendasi Otomatis")
    try:
        with open("rekomendasi.pkl", "rb") as f:
            rekom = pickle.load(f)
        st.subheader("🔍 Insights Utama")
        for insight in rekom['insights']:
            st.info(insight)
        st.subheader("📋 Rekomendasi")
        for rec in rekom['recommendations']:
            st.success(rec)
        st.subheader("✅ To-Do List Prioritas")
        for todo in rekom['todo_list']:
            st.warning(todo)
    except Exception as e:
        st.error(f"Gagal memuat insight & rekomendasi: {e}")