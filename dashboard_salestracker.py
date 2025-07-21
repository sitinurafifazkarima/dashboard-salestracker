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

page = st.sidebar.radio("Pilih Halaman", ["🟦 Aktivitas Sales", "🟦 Performansi Sales", "🟦 Profil Sales"])

if page == "🟦 Aktivitas Sales":
    st.title("🟦 Dashboard Aktivitas & Kinerja Tim Sales")

# Load metrik ringkasan tambahan dari pickle
    try:
        with open("overview_metrics.pkl", "rb") as f:
            overview_data = pickle.load(f)
        kontrak_summary = overview_data.get('nilai_kontrak_breakdown', {
            'pendapatan_riil': 0, 'prospek': 0, 'lost': 0, 'total_project': 0,
            'persen_riil': 0, 'persen_prospek': 0, 'persen_lost': 0
        })
    except:
        # Fallback calculation if pickle file doesn't exist or doesn't have the required data
        latest_contracts = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last()
        
        pendapatan_riil = latest_contracts[
            (latest_contracts['Progress'] == 'Paska Deal') & 
            (latest_contracts['Status_Kontrak'] == 'deal')
        ]['Nilai_Kontrak'].sum()
        
        prospek = latest_contracts[
            (latest_contracts['Progress'] != 'Paska Deal') & 
            (latest_contracts['Status_Kontrak'] == 'Berpotensi Deal')
        ]['Nilai_Kontrak'].sum()
        
        lost = latest_contracts[
            latest_contracts['Status_Kontrak'].isin(['Cancel', 'Batal'])
        ]['Nilai_Kontrak'].sum()
        
        total_project = pendapatan_riil + prospek + lost
        
        kontrak_summary = {
            'pendapatan_riil': pendapatan_riil,
            'prospek': prospek,
            'lost': lost,
            'total_project': total_project,
            'persen_riil': (pendapatan_riil / total_project * 100) if total_project > 0 else 0,
            'persen_prospek': (prospek / total_project * 100) if total_project > 0 else 0,
            'persen_lost': (lost / total_project * 100) if total_project > 0 else 0
        }

    # KPI Ringkasan
    col1, col2, col3 = st.columns(3)
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

# --- Metrik Tambahan (2 kolom tengah) ---
    col_spacer1, col4, col5, col_spacer2 = st.columns([1, 2, 2, 1])  # center alignment
    with col4:
        deal_count = filtered_df[filtered_df['Progress'] == 'Paska Deal']['ID_Customer'].nunique()
        deal_percent = (deal_count / total_cust * 100) if total_cust else 0
        st.metric("Customer Deal", f"{deal_count} ({deal_percent:.0f}%)")
        st.caption("Konversi ke deal")
    with col5:
        avg_progress = filtered_df['Progress_Score'].mean()
        st.metric("Rata-rata Progress", f"{avg_progress:.1f} / 5")
        st.caption("Tahapan funnel rata-rata")
    
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

        # 🎯 Analisis Funnel Lanjutan
    st.subheader("📌 Insight Visual Funnel Sales")

    tahapan_funnel = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi', 'Paska Deal']

    # Funnel keseluruhan
    funnel_overall = {
        tahap: filtered_df[filtered_df['Progress'] == tahap]['ID_Customer'].nunique()
        for tahap in tahapan_funnel
    }

    # Konversi antar tahap
    konversi_tahap = {}
    for i in range(len(tahapan_funnel) - 1):
        tahap_now = tahapan_funnel[i]
        tahap_next = tahapan_funnel[i + 1]
        val_now = funnel_overall[tahap_now]
        val_next = funnel_overall[tahap_next]
        konversi = (val_next / val_now) * 100 if val_now else 0
        konversi_tahap[f"{tahap_now} → {tahap_next}"] = konversi

    # Drop-off terbesar
    drop_offs = {
        f"{tahapan_funnel[i]} → {tahapan_funnel[i+1]}":
        funnel_overall[tahapan_funnel[i]] - funnel_overall[tahapan_funnel[i+1]]
        for i in range(len(tahapan_funnel) - 1)
    }
    max_drop = max(drop_offs.items(), key=lambda x: x[1])

    # 2️⃣ Bar Chart - Konversi Antar Tahap
    konversi_df = pd.DataFrame({
        'Tahapan': list(konversi_tahap.keys()),
        'Konversi (%)': list(konversi_tahap.values())
    })
    bar_konversi = px.bar(
        konversi_df, x='Tahapan', y='Konversi (%)',
        title="Tingkat Konversi Antar Tahapan Funnel",
        color='Konversi (%)',
        color_continuous_scale=px.colors.sequential.Mint
    )
    st.plotly_chart(bar_konversi, use_container_width=True)

    # 3️⃣ Stacked Bar - Funnel per Segmen
    funnel_segmen = {}
    for seg in filtered_df['Segmen'].dropna().unique():
        df_seg = filtered_df[filtered_df['Segmen'] == seg]
        funnel_segmen[seg] = {
            tahap: df_seg[df_seg['Progress'] == tahap]['ID_Customer'].nunique()
            for tahap in tahapan_funnel
        }

    df_segmen_funnel = pd.DataFrame(funnel_segmen).T.fillna(0).astype(int)
    df_segmen_funnel = df_segmen_funnel.reset_index().melt(id_vars='index', var_name='Tahapan', value_name='Jumlah')
    df_segmen_funnel = df_segmen_funnel.rename(columns={'index': 'Segmen'})

    fig_stacked = px.bar(
        df_segmen_funnel, x='Segmen', y='Jumlah',
        color='Tahapan', barmode='stack',
        title="Distribusi Funnel per Segmen",
        color_discrete_sequence=px.colors.sequential.BuGn
    )
    st.plotly_chart(fig_stacked, use_container_width=True)

    # ℹ️ Insight drop-off
    st.info(f"🔻 Drop-off terbesar terjadi di tahap **{max_drop[0]}**, sebanyak **{max_drop[1]} customer** tidak lanjut ke tahap berikutnya.")

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

elif page == "🟦 Performansi Sales":
    st.title("🟦 Dashboard Performansi & Analisis Sales")

    # Load data performa dari pickle utama
    try:
        with open("performa_sales.pkl", "rb") as f:
            performa_data = pickle.load(f)
        sales_perf = performa_data.get('sales_performance', pd.DataFrame())
        low_perf = performa_data.get('low_performers', pd.DataFrame())
        top_sales = performa_data.get('top_performer', 'N/A')
    except:
        # Fallback jika file pickle tidak ada
        sales_perf = pd.DataFrame()
        low_perf = pd.DataFrame()
        top_sales = 'N/A'

    # ==========================
    # 1. FUNNEL KOMPARATIF PER SALES (Layer Pertama)
    # ==========================
    st.subheader("📊 Funnel Komparatif per Sales")
    
    # Hitung funnel per sales
    tahapan_funnel = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi', 'Paska Deal']
    funnel_sales = {}
    
    for sales in filtered_df['Nama_Sales'].unique():
        df_sales = filtered_df[filtered_df['Nama_Sales'] == sales]
        funnel_sales[sales] = {
            tahap: df_sales[df_sales['Progress'] == tahap]['ID_Customer'].nunique()
            for tahap in tahapan_funnel
        }
    
    # Convert to DataFrame untuk visualisasi
    df_funnel_sales = pd.DataFrame(funnel_sales).T.fillna(0).astype(int)
    df_funnel_melt = df_funnel_sales.reset_index().melt(
        id_vars='index', var_name='Tahapan', value_name='Jumlah_Customer'
    ).rename(columns={'index': 'Nama_Sales'})
    
    # Stacked bar chart untuk funnel komparatif
    fig_funnel_comp = px.bar(
        df_funnel_melt, x='Nama_Sales', y='Jumlah_Customer',
        color='Tahapan', barmode='stack',
        title='Funnel Komparatif: Jumlah Customer per Tahapan per Sales',
        color_discrete_sequence=px.colors.sequential.Teal
    )
    fig_funnel_comp.update_layout(height=500)
    st.plotly_chart(fig_funnel_comp, use_container_width=True)

    # Konversi rate per sales
    konversi_sales = {}
    for sales in df_funnel_sales.index:
        if df_funnel_sales.loc[sales, 'Inisiasi'] > 0:
            konversi_sales[sales] = (df_funnel_sales.loc[sales, 'Paska Deal'] / 
                                   df_funnel_sales.loc[sales, 'Inisiasi'] * 100)
        else:
            konversi_sales[sales] = 0
    
    konversi_df = pd.DataFrame(list(konversi_sales.items()), 
                              columns=['Nama_Sales', 'Konversi_Rate'])
    
    fig_konversi = px.bar(
        konversi_df, x='Nama_Sales', y='Konversi_Rate',
        title='Conversion Rate: Inisiasi → Paska Deal (%)',
        color='Konversi_Rate', color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_konversi, use_container_width=True)

    # ==========================
    # 2. LEADERBOARD & PERFORMANSI SALES (Layer Kedua)
    # ==========================
    st.subheader("🏆 Leaderboard Performa Sales Komprehensif")
    
    # Menghitung metrik lengkap per sales dari filtered data
    sales_metrics = {}
    
    for sales in filtered_df['Nama_Sales'].unique():
        df_sales = filtered_df[filtered_df['Nama_Sales'] == sales]
        
        # Ambil data kontrak terbaru per customer
        latest_per_customer = df_sales.sort_values('Tanggal').groupby('ID_Customer').last()
        
        # Hitung metrik
        total_kunjungan = len(df_sales)
        total_customer = df_sales['ID_Customer'].nunique()
        
        # Deal berdasarkan Progress = Paska Deal
        deals = latest_per_customer[latest_per_customer['Progress'] == 'Paska Deal']
        jumlah_deal = len(deals)
        
        # Nilai kontrak berdasarkan logika bisnis yang benar
        nilai_aktual = latest_per_customer[
            (latest_per_customer['Progress'] == 'Paska Deal') & 
            (latest_per_customer['Status_Kontrak'] == 'deal')
        ]['Nilai_Kontrak'].sum()
        
        nilai_prospek = latest_per_customer[
            (latest_per_customer['Progress'] != 'Paska Deal') & 
            (latest_per_customer['Status_Kontrak'] == 'Berpotensi Deal')
        ]['Nilai_Kontrak'].sum()
        
        # Target vs realisasi
        target_total = df_sales['Target_Sales'].sum()  # Total target untuk semua customer
        realisasi_persen = (nilai_aktual / target_total * 100) if target_total > 0 else 0
        
        # Closing rate
        closing_rate = (jumlah_deal / total_customer * 100) if total_customer > 0 else 0
        
        # Average Handling Time (AHT) - rata-rata durasi per customer
        aht_list = []
        for customer_id in df_sales['ID_Customer'].unique():
            cust_data = df_sales[df_sales['ID_Customer'] == customer_id].sort_values('Tanggal')
            if len(cust_data) > 1:
                durasi = (cust_data['Tanggal'].max() - cust_data['Tanggal'].min()).days
                aht_list.append(durasi)
        
        avg_handling_time = np.mean(aht_list) if aht_list else 0
        
        # Frekuensi kunjungan per customer
        avg_freq = total_kunjungan / total_customer if total_customer > 0 else 0
        
        sales_metrics[sales] = {
            'Total_Kunjungan': total_kunjungan,
            'Total_Customer': total_customer,
            'Jumlah_Deal': jumlah_deal,
            'Nilai_Aktual': nilai_aktual,
            'Nilai_Prospek': nilai_prospek,
            'Target_Total': target_total,
            'Realisasi_Persen': realisasi_persen,
            'Closing_Rate': closing_rate,
            'Avg_Handling_Time': avg_handling_time,
            'Avg_Freq_Kunjungan': avg_freq
        }
    
    # Convert ke DataFrame
    performance_df = pd.DataFrame(sales_metrics).T
    performance_df = performance_df.sort_values('Jumlah_Deal', ascending=False)
    
    # Display leaderboard
    st.dataframe(performance_df.round(2), use_container_width=True)

    # ==========================
    # 3. AVERAGE HANDLING TIME ANALYSIS
    # ==========================
    st.subheader("⏱️ Average Handling Time (AHT) Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # AHT per Sales
        aht_fig = px.bar(
            performance_df.reset_index(), x='index', y='Avg_Handling_Time',
            title='Average Handling Time per Sales (Hari)',
            color='Avg_Handling_Time', color_continuous_scale='Oranges'
        )
        aht_fig.update_xaxes(title='Sales')
        st.plotly_chart(aht_fig, use_container_width=True)
    
    with col2:
        # Scatter: AHT vs Closing Rate
        scatter_aht = px.scatter(
            performance_df.reset_index(), x='Avg_Handling_Time', y='Closing_Rate',
            size='Jumlah_Deal', hover_name='index',
            title='Korelasi AHT vs Closing Rate',
            color='Closing_Rate', color_continuous_scale='Viridis'
        )
        st.plotly_chart(scatter_aht, use_container_width=True)

    # Insight AHT
    best_aht = performance_df['Avg_Handling_Time'].min()
    worst_aht = performance_df['Avg_Handling_Time'].max()
    best_aht_sales = performance_df['Avg_Handling_Time'].idxmin()
    
    st.info(f"💡 **AHT Terbaik**: {best_aht_sales} ({best_aht:.1f} hari) | **AHT Terburuk**: {worst_aht:.1f} hari")

    # ==========================
    # 4. TARGET vs REALISASI ANALYSIS
    # ==========================
    st.subheader("🎯 Analisis Target vs Realisasi")
    
    # Per Sales
    target_vs_real = performance_df[['Target_Total', 'Nilai_Aktual', 'Realisasi_Persen']].copy()
    target_vs_real = target_vs_real.reset_index()
    
    fig_target = px.bar(
        target_vs_real, x='index', y=['Target_Total', 'Nilai_Aktual'],
        title='Target vs Realisasi per Sales (Nilai Kontrak)',
        barmode='group', color_discrete_sequence=['#ff7f0e', '#2ca02c']
    )
    fig_target.update_xaxes(title='Sales')
    st.plotly_chart(fig_target, use_container_width=True)
    
    # Achievement percentage
    achievement_fig = px.bar(
        target_vs_real, x='index', y='Realisasi_Persen',
        title='Persentase Pencapaian Target per Sales (%)',
        color='Realisasi_Persen', color_continuous_scale='RdYlGn'
    )
    achievement_fig.add_hline(y=100, line_dash="dash", line_color="red", 
                             annotation_text="Target 100%")
    st.plotly_chart(achievement_fig, use_container_width=True)

    # ==========================
    # 5. ANALISIS PER SEGMEN
    # ==========================
    st.subheader("📈 Analisis Target vs Realisasi per Segmen")
    
    # Target vs Realisasi per Segmen
    segmen_metrics = {}
    for segmen in filtered_df['Segmen'].dropna().unique():
        df_segmen = filtered_df[filtered_df['Segmen'] == segmen]
        latest_segmen = df_segmen.sort_values('Tanggal').groupby('ID_Customer').last()
        
        target_segmen = df_segmen['Target_Sales'].sum()
        realisasi_segmen = latest_segmen[
            (latest_segmen['Progress'] == 'Paska Deal') & 
            (latest_segmen['Status_Kontrak'] == 'deal')
        ]['Nilai_Kontrak'].sum()
        
        achievement_segmen = (realisasi_segmen / target_segmen * 100) if target_segmen > 0 else 0
        
        segmen_metrics[segmen] = {
            'Target': target_segmen,
            'Realisasi': realisasi_segmen,
            'Achievement_Persen': achievement_segmen,
            'Customer_Count': df_segmen['ID_Customer'].nunique(),
            'Deal_Count': len(latest_segmen[latest_segmen['Progress'] == 'Paska Deal'])
        }
    
    segmen_df = pd.DataFrame(segmen_metrics).T.reset_index()
    segmen_df.columns = ['Segmen', 'Target', 'Realisasi', 'Achievement_Persen', 'Customer_Count', 'Deal_Count']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_segmen_target = px.bar(
            segmen_df, x='Segmen', y=['Target', 'Realisasi'],
            title='Target vs Realisasi per Segmen', barmode='group',
            color_discrete_sequence=['#ff7f0e', '#2ca02c']
        )
        st.plotly_chart(fig_segmen_target, use_container_width=True)
    
    with col2:
        fig_segmen_achievement = px.bar(
            segmen_df, x='Segmen', y='Achievement_Persen',
            title='Achievement Rate per Segmen (%)',
            color='Achievement_Persen', color_continuous_scale='RdYlGn'
        )
        fig_segmen_achievement.add_hline(y=100, line_dash="dash", line_color="red")
        st.plotly_chart(fig_segmen_achievement, use_container_width=True)

    # ==========================
    # 6. ANALISIS AKTIVITAS & PRODUKTIVITAS
    # ==========================
    st.subheader("📊 Analisis Aktivitas & Produktivitas Sales")
    
    # Customer per Sales Ratio
    performance_df['Customer_per_Visit'] = performance_df['Total_Customer'] / performance_df['Total_Kunjungan']
    performance_df['Deal_per_Visit'] = performance_df['Jumlah_Deal'] / performance_df['Total_Kunjungan']
    
    col1, col2 = st.columns(2)
    
    with col1:
        productivity_fig = px.scatter(
            performance_df.reset_index(), x='Total_Kunjungan', y='Jumlah_Deal',
            size='Nilai_Aktual', hover_name='index',
            title='Produktivitas: Kunjungan vs Deal',
            color='Closing_Rate', color_continuous_scale='Turbo'
        )
        st.plotly_chart(productivity_fig, use_container_width=True)
    
    with col2:
        efficiency_df = performance_df[['Deal_per_Visit', 'Customer_per_Visit']].reset_index()
        efficiency_fig = px.bar(
            efficiency_df, x='index', y=['Deal_per_Visit', 'Customer_per_Visit'],
            title='Efisiensi: Deal & Customer per Kunjungan', barmode='group',
            color_discrete_sequence=['#1f77b4', '#ff7f0e']
        )
        efficiency_fig.update_xaxes(title='Sales')
        st.plotly_chart(efficiency_fig, use_container_width=True)

    # ==========================
    # 7. ANALISIS PIPELINE & FORECASTING
    # ==========================
    st.subheader("🔮 Pipeline Analysis & Sales Forecasting")
    
    # Pipeline per Sales
    pipeline_data = []
    for sales in filtered_df['Nama_Sales'].unique():
        df_sales = filtered_df[filtered_df['Nama_Sales'] == sales]
        latest_sales = df_sales.sort_values('Tanggal').groupby('ID_Customer').last()
        
        for tahap in tahapan_funnel:
            customer_in_stage = latest_sales[latest_sales['Progress'] == tahap]
            nilai_stage = customer_in_stage[
                customer_in_stage['Status_Kontrak'] == 'Berpotensi Deal'
            ]['Nilai_Kontrak'].sum()
            
            pipeline_data.append({
                'Sales': sales,
                'Tahap': tahap,
                'Nilai_Pipeline': nilai_stage,
                'Customer_Count': len(customer_in_stage)
            })
    
    pipeline_df = pd.DataFrame(pipeline_data)
    
    # Pipeline value per stage
    pipeline_summary = pipeline_df.groupby('Tahap')['Nilai_Pipeline'].sum().reset_index()
    pipeline_fig = px.funnel(
        pipeline_summary, x='Nilai_Pipeline', y='Tahap',
        title='Pipeline Value per Tahapan (Rp)',
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    st.plotly_chart(pipeline_fig, use_container_width=True)
    
    # Forecasting berdasarkan conversion rate historis
    total_pipeline = pipeline_df[pipeline_df['Tahap'] != 'Paska Deal']['Nilai_Pipeline'].sum()
    avg_conversion = performance_df['Closing_Rate'].mean() / 100
    forecasted_revenue = total_pipeline * avg_conversion
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pipeline Value", f"Rp {total_pipeline/1e6:.1f}M")
    with col2:
        st.metric("Avg Conversion Rate", f"{avg_conversion*100:.1f}%")
    with col3:
        st.metric("Forecasted Revenue", f"Rp {forecasted_revenue/1e6:.1f}M")

    # ==========================
    # 8. EFISIENSI WAKTU & PROSES
    # ==========================
    st.subheader("⏱️ Analisis Efisiensi Waktu & Proses")
    
    # Waktu rata-rata per tahap untuk setiap sales
    stage_time_data = []
    for sales in filtered_df['Nama_Sales'].unique():
        df_sales = filtered_df[filtered_df['Nama_Sales'] == sales]
        
        for customer_id in df_sales['ID_Customer'].unique():
            customer_data = df_sales[df_sales['ID_Customer'] == customer_id].sort_values('Tanggal')
            customer_stages = customer_data['Progress'].unique()
            
            for i, stage in enumerate(customer_stages[:-1]):
                if i < len(customer_stages) - 1:
                    current_stage_date = customer_data[customer_data['Progress'] == stage]['Tanggal'].min()
                    next_stage_date = customer_data[customer_data['Progress'] == customer_stages[i+1]]['Tanggal'].min()
                    
                    if pd.notnull(current_stage_date) and pd.notnull(next_stage_date):
                        time_diff = (next_stage_date - current_stage_date).days
                        if time_diff >= 0:
                            stage_time_data.append({
                                'Sales': sales,
                                'From_Stage': stage,
                                'To_Stage': customer_stages[i+1],
                                'Days': time_diff
                            })
    
    if stage_time_data:
        stage_time_df = pd.DataFrame(stage_time_data)
        avg_stage_time = stage_time_df.groupby(['Sales', 'From_Stage'])['Days'].mean().reset_index()
        
        # Heatmap waktu per tahap per sales
        heatmap_data = avg_stage_time.pivot(index='Sales', columns='From_Stage', values='Days').fillna(0)
        
        fig_heatmap = px.imshow(
            heatmap_data, 
            title='Average Days per Stage Transition (Heatmap)',
            color_continuous_scale='RdYlBu_r',
            aspect='auto'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # ==========================
    # 9. INSIGHTS & RECOMMENDATIONS
    # ==========================
    st.subheader("🧠 Comprehensive Insights & Strategic Recommendations")
    
    # Top performers identification
    top_closing = performance_df['Closing_Rate'].idxmax()
    top_revenue = performance_df['Nilai_Aktual'].idxmax() 
    top_efficiency = performance_df['Deal_per_Visit'].idxmax()
    best_aht_performer = performance_df['Avg_Handling_Time'].idxmin()
    
    # Underperformers
    low_closing = performance_df[performance_df['Closing_Rate'] < performance_df['Closing_Rate'].median()]
    high_aht = performance_df[performance_df['Avg_Handling_Time'] > performance_df['Avg_Handling_Time'].median()]
    
    # Target achievement analysis
    underachievers = performance_df[performance_df['Realisasi_Persen'] < 80]
    
    st.markdown(f"""
    <div style='background-color:#f1f8e9;padding:1.5rem;border-radius:10px;border-left:5px solid #2e7d32;'>
        <h4>🏆 <b>Top Performers Identification</b></h4>
        <ul>
            <li>🎯 <b>Highest Closing Rate:</b> {top_closing} ({performance_df.loc[top_closing, 'Closing_Rate']:.1f}%)</li>
            <li>💰 <b>Highest Revenue:</b> {top_revenue} (Rp {performance_df.loc[top_revenue, 'Nilai_Aktual']/1e6:.1f}M)</li>
            <li>⚡ <b>Most Efficient:</b> {top_efficiency} ({performance_df.loc[top_efficiency, 'Deal_per_Visit']:.3f} deals/visit)</li>
            <li>⏱️ <b>Best AHT:</b> {best_aht_performer} ({performance_df.loc[best_aht_performer, 'Avg_Handling_Time']:.1f} days)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if len(underachievers) > 0:
        st.markdown(f"""
        <div style='background-color:#fff3e0;padding:1.5rem;border-radius:10px;border-left:5px solid #f57c00;margin-top:1rem;'>
            <h4>🚨 <b>Performance Alerts</b></h4>
            <p><b>Target Underachievers (&lt;80%):</b> {', '.join(underachievers.index.tolist())}</p>
            <p><b>High AHT Concerns:</b> {', '.join(high_aht.index.tolist())}</p>
            <p><b>Low Closing Rate:</b> {', '.join(low_closing.index.tolist())}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Strategic recommendations
    best_segmen = segmen_df.loc[segmen_df['Achievement_Persen'].idxmax(), 'Segmen']
    worst_segmen = segmen_df.loc[segmen_df['Achievement_Persen'].idxmin(), 'Segmen']
    
    st.markdown(f"""
    <div style='background-color:#e3f2fd;padding:1.5rem;border-radius:10px;border-left:5px solid #1976d2;margin-top:1rem;'>
        <h4>� <b>Strategic Recommendations</b></h4>
        <ol>
            <li><b>Focus Segmentation:</b> Prioritize "{best_segmen}" segment (highest achievement) while developing strategy for "{worst_segmen}" segment</li>
            <li><b>Process Optimization:</b> Implement best practices from {top_efficiency} to improve deal/visit ratio across team</li>
            <li><b>AHT Improvement:</b> Conduct time management training for sales with AHT > {performance_df['Avg_Handling_Time'].median():.1f} days</li>
            <li><b>Pipeline Acceleration:</b> Focus on converting Rp {total_pipeline/1e6:.1f}M pipeline value with targeted interventions</li>
            <li><b>Target Recalibration:</b> Review targets for underperforming segments and provide additional support</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # ==========================
    # 10. DURASI PROSES SALES ANALYSIS (existing code refined)
    # ==========================
    st.subheader("⏱️ Sales Process Duration Analysis")
    
    # Existing duration analysis code but enhanced
    paska_deal_customers = filtered_df[filtered_df["Progress"] == "Paska Deal"]["ID_Customer"].unique()
    df_paska = filtered_df[filtered_df["ID_Customer"].isin(paska_deal_customers)].copy().sort_values(["ID_Customer", "Tanggal"])

    def get_duration(group):
        inisiasi_date = group[group["Progress"] == "Inisiasi"]["Tanggal"].min()
        deal_date = group[group["Progress"] == "Paska Deal"]["Tanggal"].max()
        if pd.notnull(inisiasi_date) and pd.notnull(deal_date):
            return pd.Series({
                "Nama_Sales": group["Nama_Sales"].iloc[0],
                "Durasi_Proses_Sales (hari)": (deal_date - inisiasi_date).days
            })

    durasi_per_customer = df_paska.groupby("ID_Customer").apply(get_duration).dropna()
    durasi_per_sales = durasi_per_customer.groupby("Nama_Sales")["Durasi_Proses_Sales (hari)"].mean()
    leaderboard_durasi = durasi_per_sales.reset_index().rename(columns={
        "Nama_Sales": "Sales",
        "Durasi_Proses_Sales (hari)": "Rata-rata Durasi (hari)"
    }).sort_values("Rata-rata Durasi (hari)").reset_index(drop=True)
    leaderboard_durasi["Rank"] = leaderboard_durasi["Rata-rata Durasi (hari)"].rank(method="min").astype(int)

    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(leaderboard_durasi, use_container_width=True)
    
    with col2:
        fig4 = px.bar(
            leaderboard_durasi,
            y='Sales',
            x='Rata-rata Durasi (hari)',
            orientation='h',
            title="Speed to Close: Inisiasi → Paska Deal",
            color='Rata-rata Durasi (hari)',
            color_continuous_scale='Greens'
        )
        fig4.update_layout(yaxis=dict(categoryorder='total ascending'))
        st.plotly_chart(fig4, use_container_width=True)

    
elif page == "🟦 Profil Sales":
    import matplotlib.pyplot as plt
    import seaborn as sns

    st.title("🟦 Profil Individu Sales")
    nama = st.selectbox("Pilih Sales", options=filtered_df['Nama_Sales'].unique())
    data_sales = filtered_df[filtered_df['Nama_Sales'] == nama].sort_values(['ID_Customer', 'Tanggal'])

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

    # Rata-rata durasi closing yang sudah diperbaiki (dari Inisiasi ke Paska Deal)
    st.subheader("⏱️ Durasi Proses Closing (Inisiasi → Deal)")
    deal_customers = data_sales[data_sales['Progress'] == 'Paska Deal']['ID_Customer'].unique()
    data_deal = data_sales[data_sales['ID_Customer'].isin(deal_customers)]

    durasi_per_customer = []
    for cust_id, group in data_deal.groupby('ID_Customer'):
        group = group.sort_values('Tanggal')
        tanggal_inisiasi = group[group['Progress'] == 'Inisiasi']['Tanggal'].min()
        tanggal_deal = group[group['Progress'] == 'Paska Deal']['Tanggal'].max()
        if pd.notnull(tanggal_inisiasi) and pd.notnull(tanggal_deal):
            durasi = (tanggal_deal - tanggal_inisiasi).days
            if durasi >= 0:
                durasi_per_customer.append(durasi)

    if durasi_per_customer:
        rata2_durasi = np.mean(durasi_per_customer)
        median_durasi = np.median(durasi_per_customer)
    else:
        rata2_durasi = 0
        median_durasi = 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rata-rata Durasi Closing", f"{rata2_durasi:.1f} Hari")
    with col2:
        st.caption(f"Median Durasi Closing: {median_durasi:.1f} Hari")

    # Analisis Tambahan Matplotlib
    st.subheader("📊 Analisis Visual Sales (Advanced)")

    # Urutan tahapan
    progress_order = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi', 'Paska Deal']
    progress_score_mapping = {p: i + 1 for i, p in enumerate(progress_order)}
    data_sales['Progress_Score'] = data_sales['Progress'].map(progress_score_mapping)

    timeline = data_sales.groupby('Tanggal').size()
    distrib_jenis = data_sales['Jenis_Kunjungan'].value_counts()
    max_stage = data_sales.groupby('ID_Customer')['Progress_Score'].max().mean()
    top_notes = data_sales['Catatan'].value_counts().head(5)

    funnel_data = {
        stage: data_sales[data_sales['Progress'] == stage]['ID_Customer'].nunique()
        for stage in progress_order
    }
    funnel_series = pd.Series(funnel_data)

    # Durasi antar tahap
    stage_durations = []
    for cust_id, group in data_sales.groupby('ID_Customer'):
        group = group.sort_values('Tanggal')
        stage_dates = {}
        for _, row in group.iterrows():
            stage = row['Progress']
            if stage not in stage_dates:
                stage_dates[stage] = row['Tanggal']
        for s1, s2 in zip(progress_order[:-1], progress_order[1:]):
            if s1 in stage_dates and s2 in stage_dates:
                delta = (stage_dates[s2] - stage_dates[s1]).days
                if delta >= 0:
                    stage_durations.append({'From': s1, 'To': s2, 'Days': delta})

    durasi_df = pd.DataFrame(stage_durations)
    avg_durasi = durasi_df.groupby(['From', 'To'])['Days'].mean().reset_index()

    # Plotting
    fig, axs = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f"Analisis Sales: {nama}", fontsize=18)

    # Timeline
    axs[0, 0].plot(timeline.index, timeline.values)
    axs[0, 0].set_title('Timeline Kunjungan')
    axs[0, 0].set_ylabel('Jumlah')

    # Jenis kunjungan
    distrib_jenis.plot(kind='bar', color='orange', ax=axs[0, 1])
    axs[0, 1].set_title('Distribusi Jenis Kunjungan')
    axs[0, 1].tick_params(axis='x', rotation=45)

    # Tahap tertinggi rata-rata
    axs[0, 2].bar(['Tahap Tertinggi Rata-rata'], [max_stage], color='green')
    axs[0, 2].set_ylim(0, 5)
    axs[0, 2].set_title('Rata-rata Tahapan Tertinggi')

    # Top notes
    top_notes.plot(kind='barh', color='purple', ax=axs[1, 0])
    axs[1, 0].invert_yaxis()
    axs[1, 0].set_title('Top 5 Catatan Kunjungan')

    # Funnel
    funnel_series[progress_order].plot(kind='bar', color='teal', ax=axs[1, 1])
    axs[1, 1].set_title('Progress Funnel (Customer per Tahap)')

    # Durasi antar tahap
    if not avg_durasi.empty:
        sns.barplot(data=avg_durasi, x='From', y='Days', hue='To', palette='Set2', ax=axs[1, 2])
        axs[1, 2].set_title('Durasi Rata-Rata Antar Tahap')
        axs[1, 2].set_ylabel('Durasi (hari)')
    else:
        axs[1, 2].text(0.5, 0.5, 'Tidak cukup data', ha='center')
        axs[1, 2].axis('off')

    st.pyplot(fig)

    # Insight tambahan
    st.subheader("📘 Rekomendasi & Insight Pribadi")
    st.info(f"- Rata-rata tahap tertinggi per customer: {max_stage:.2f}")
    penyusutan = [f"{progress_order[i]} → {progress_order[i+1]}: {funnel_series[progress_order[i+1]]}/{funnel_series[progress_order[i]]} customer"
                  for i in range(len(progress_order) - 1) if funnel_series[progress_order[i]] > 0]
    for p in penyusutan:
        st.write("📉", p)

    if not durasi_df.empty:
        slowest = avg_durasi.sort_values('Days', ascending=False).iloc[0]
        st.warning(f"⏱ Transisi terlama rata-rata: {slowest['From']} → {slowest['To']} ({slowest['Days']:.1f} hari)")

    top_catatan = top_notes.idxmax()
    deal_notes = data_sales[data_sales['Status_Kontrak'] == 'Deal']['Catatan'].value_counts()
    if not deal_notes.empty:
        catatan_efektif = deal_notes.idxmax()
        st.success(f"✅ Catatan efektif saat Deal: “{catatan_efektif}”")
    else:
        st.success(f"✅ Catatan paling umum: “{top_catatan}”")
