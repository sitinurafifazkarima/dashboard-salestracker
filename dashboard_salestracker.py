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

page = st.sidebar.radio("Pilih Halaman", [
    "🏠 Dashboard Utama", 
    "� Segment Analysis", 
    "🏆 Sales Performance", 
    "� Progress Analysis",
    "🔍 Factor Analysis",
    "📅 Timeline Analysis",
    "� Profil Sales"
])

if page == "🏠 Dashboard Utama":
    st.title("🏠 Dashboard Aktivitas & Kinerja Tim Sales")
    st.markdown("### 📋 Ringkasan Eksekutif")

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
            latest_contracts['Status_Kontrak'] == 'Deal'
        ]['Nilai_Kontrak'].sum()
        
        prospek = latest_contracts[
            latest_contracts['Status_Kontrak'] == 'Berpotensi Deal'
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

    # Tambahan informasi dan penjelasan logika bisnis
    st.markdown("""
    <div style='background-color:#e8f5e9;padding:1rem;border-radius:10px;margin-top:1rem;'>
    <h4>� <b>Catatan Logika Perhitungan:</b></h4>
    <ul>
        <li><b>Nilai Kontrak:</b> Berdasarkan data terbaru per customer (1 customer = 1 nilai kontrak)</li>
        <li><b>Pendapatan Riil:</b> Status_Kontrak = 'Deal' (kontrak sudah ditandatangani)</li>
        <li><b>Prospek:</b> Status_Kontrak = 'Berpotensi Deal' (masih dalam pipeline)</li>
        <li><b>Lost/Cancel:</b> Status_Kontrak = 'Cancel/Batal' (opportunity hilang)</li>
        <li><b>Target Sales:</b> Berdasarkan target terbaru per customer</li>
    </ul>
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

elif page == "� Segment Analysis":
    st.title("📊 Segment Analysis - Analisis Mendalam per Segmen")
    st.markdown("### 🎯 Insight: Optimasi Strategi Segmentasi untuk Meningkatkan Profitabilitas")
    
    # Segment Performance Overview
    st.subheader("🔍 1. Segment Performance Overview")
    
    # Hitung metrik per segmen
    segment_metrics = {}
    for segmen in filtered_df['Segmen'].dropna().unique():
        df_seg = filtered_df[filtered_df['Segmen'] == segmen]
        latest_seg = df_seg.sort_values('Tanggal').groupby('ID_Customer').last()
        
        # Metrik dasar
        total_customer = df_seg['ID_Customer'].nunique()
        total_visits = len(df_seg)
        total_deals = len(latest_seg[latest_seg['Progress'] == 'Paska Deal'])
        
        # Nilai kontrak - Fixed: Use 'Deal' instead of 'deal'
        nilai_riil = latest_seg[latest_seg['Status_Kontrak'] == 'Deal']['Nilai_Kontrak'].sum()
        nilai_prospek = latest_seg[latest_seg['Status_Kontrak'] == 'Berpotensi Deal']['Nilai_Kontrak'].sum()
        target_total = latest_seg['Target_Sales'].sum()
        
        # Performance metrics
        conversion_rate = (total_deals / total_customer * 100) if total_customer > 0 else 0
        avg_deal_size = nilai_riil / total_deals if total_deals > 0 else 0
        target_achievement = (nilai_riil / target_total * 100) if target_total > 0 else 0
        
        # Efficiency metrics (replacing ROI)
        avg_visits_per_customer = total_visits / total_customer if total_customer > 0 else 0
        revenue_per_visit = nilai_riil / total_visits if total_visits > 0 else 0
        customer_lifetime_value = nilai_riil / total_customer if total_customer > 0 else 0
        
        segment_metrics[segmen] = {
            'Total_Customer': total_customer,
            'Total_Visits': total_visits,
            'Total_Deals': total_deals,
            'Nilai_Riil': nilai_riil,
            'Nilai_Prospek': nilai_prospek,
            'Target_Total': target_total,
            'Conversion_Rate': conversion_rate,
            'Avg_Deal_Size': avg_deal_size,
            'Target_Achievement': target_achievement,
            'Avg_Visits_per_Customer': avg_visits_per_customer,
            'Revenue_per_Visit': revenue_per_visit,
            'Customer_LTV': customer_lifetime_value
        }
    
    segment_df = pd.DataFrame(segment_metrics).T
    
    # Display segment metrics table
    st.dataframe(segment_df.round(2), use_container_width=True)
    
    # Visualisasi segment comparison
    col1, col2 = st.columns(2)
    
    with col1:
        fig_conversion = px.bar(
            segment_df.reset_index(), x='index', y='Conversion_Rate',
            title='Conversion Rate per Segmen (%)',
            color='Conversion_Rate', color_continuous_scale='Viridis'
        )
        fig_conversion.update_xaxes(title='Segmen')
        st.plotly_chart(fig_conversion, use_container_width=True)
    
    with col2:
        fig_deal_size = px.bar(
            segment_df.reset_index(), x='index', y='Avg_Deal_Size',
            title='Average Deal Size per Segmen (Rp)',
            color='Avg_Deal_Size', color_continuous_scale='Plasma'
        )
        fig_deal_size.update_xaxes(title='Segmen')
        st.plotly_chart(fig_deal_size, use_container_width=True)
    
    # Segment Efficiency Analysis (replacing ROI)
    st.subheader("� 2. Segment Efficiency & Profitability Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_efficiency = px.scatter(
            segment_df.reset_index(), x='Avg_Visits_per_Customer', y='Revenue_per_Visit',
            size='Total_Customer', color='Conversion_Rate',
            hover_name='index', title='Segment Efficiency Matrix',
            labels={'Avg_Visits_per_Customer': 'Avg Visits per Customer', 
                   'Revenue_per_Visit': 'Revenue per Visit (Rp)'}
        )
        st.plotly_chart(fig_efficiency, use_container_width=True)
    
    with col2:
        fig_target = px.bar(
            segment_df.reset_index(), x='index', y='Target_Achievement',
            title='Target Achievement per Segmen (%)',
            color='Target_Achievement', color_continuous_scale='RdYlGn'
        )
        fig_target.add_hline(y=100, line_dash="dash", line_color="red")
        fig_target.update_xaxes(title='Segmen')
        st.plotly_chart(fig_target, use_container_width=True)
    
    # Segment Funnel Analysis
    st.subheader("� 3. Segment Funnel Performance")
    
    tahapan_funnel = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi', 'Paska Deal']
    
    # Hitung funnel per segmen
    funnel_segmen = {}
    for segmen in filtered_df['Segmen'].dropna().unique():
        df_seg = filtered_df[filtered_df['Segmen'] == segmen]
        funnel_segmen[segmen] = {
            tahap: df_seg[df_seg['Progress'] == tahap]['ID_Customer'].nunique()
            for tahap in tahapan_funnel
        }
    
    funnel_seg_df = pd.DataFrame(funnel_segmen).T.fillna(0)
    
    # Stacked funnel chart
    funnel_melt = funnel_seg_df.reset_index().melt(
        id_vars='index', var_name='Tahapan', value_name='Customer_Count'
    ).rename(columns={'index': 'Segmen'})
    
    fig_funnel_seg = px.bar(
        funnel_melt, x='Segmen', y='Customer_Count',
        color='Tahapan', barmode='stack',
        title='Funnel Distribution per Segmen',
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig_funnel_seg, use_container_width=True)
    
    # Segment Insights & Recommendations
    st.subheader("💡 4. Segment Insights & Strategic Recommendations")
    
    # Identify best and worst segments
    best_conversion_seg = segment_df['Conversion_Rate'].idxmax()
    best_efficiency_seg = segment_df['Revenue_per_Visit'].idxmax()
    best_ltv_seg = segment_df['Customer_LTV'].idxmax()
    worst_conversion_seg = segment_df['Conversion_Rate'].idxmin()
    highest_potential_seg = segment_df['Nilai_Prospek'].idxmax()
    
    st.markdown(f"""
    <div style='background-color:#e8f5e9;padding:1.5rem;border-radius:10px;border-left:5px solid #2e7d32;'>
        <h4>🏆 <b>Top Performing Segments</b></h4>
        <ul>
            <li>🎯 <b>Highest Conversion:</b> {best_conversion_seg} ({segment_df.loc[best_conversion_seg, 'Conversion_Rate']:.1f}%)</li>
            <li>� <b>Best Efficiency:</b> {best_efficiency_seg} (Rp {segment_df.loc[best_efficiency_seg, 'Revenue_per_Visit']:,.0f} per visit)</li>
            <li>💰 <b>Highest Customer Value:</b> {best_ltv_seg} (Rp {segment_df.loc[best_ltv_seg, 'Customer_LTV']:,.0f} per customer)</li>
            <li>🚀 <b>Highest Potential:</b> {highest_potential_seg} (Rp {segment_df.loc[highest_potential_seg, 'Nilai_Prospek']/1e6:.1f}M pipeline)</li>
        </ul>
        <p><b>Recommendation:</b> Increase resource allocation to these high-performing segments</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background-color:#fff3e0;padding:1.5rem;border-radius:10px;border-left:5px solid #f57c00;margin-top:1rem;'>
        <h4>⚠️ <b>Improvement Opportunities</b></h4>
        <ul>
            <li>📉 <b>Lowest Conversion:</b> {worst_conversion_seg} ({segment_df.loc[worst_conversion_seg, 'Conversion_Rate']:.1f}%)</li>
            <li>🔄 <b>Action Required:</b> Review sales approach and customer needs analysis</li>
            <li>📈 <b>Optimization Strategy:</b> Implement targeted training and refined value propositions</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

elif page == "🏆 Sales Performance":
    st.title("🏆 Sales Performance - Comprehensive Individual Analysis")
    st.markdown("### 🎯 Insight: Identifikasi Top Performer dan Opportunity untuk Growth")

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
        
        # Nilai kontrak berdasarkan logika bisnis yang benar (per customer terbaru)
        nilai_aktual = latest_per_customer[
            latest_per_customer['Status_Kontrak'] == 'Deal'
        ]['Nilai_Kontrak'].sum()
        
        nilai_prospek = latest_per_customer[
            latest_per_customer['Status_Kontrak'] == 'Berpotensi Deal'
        ]['Nilai_Kontrak'].sum()
        
        # Target vs realisasi (per customer terbaru)
        target_total = latest_per_customer['Target_Sales'].sum()  # Target per customer terbaru
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
    
    # Performance visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        fig_deals = px.bar(
            performance_df.reset_index(), x='index', y='Jumlah_Deal',
            title='Number of Deals per Sales Person',
            color='Jumlah_Deal', color_continuous_scale='Viridis'
        )
        fig_deals.update_xaxes(title='Sales Person', tickangle=45)
        st.plotly_chart(fig_deals, use_container_width=True)
    
    with col2:
        fig_revenue = px.bar(
            performance_df.reset_index(), x='index', y='Nilai_Aktual',
            title='Actual Revenue per Sales Person (Rp)',
            color='Nilai_Aktual', color_continuous_scale='Plasma'
        )
        fig_revenue.update_xaxes(title='Sales Person', tickangle=45)
        st.plotly_chart(fig_revenue, use_container_width=True)

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
        
        target_segmen = latest_segmen['Target_Sales'].sum()  # Target per customer terbaru
        realisasi_segmen = latest_segmen[
            latest_segmen['Status_Kontrak'] == 'Deal'
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
            # Hanya ambil nilai kontrak untuk customer yang berpotensi deal (belum close/cancel)
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

elif page == "📈 Progress Analysis":
    st.title("📈 Progress Analysis - Deep Dive Customer Journey")
    st.markdown("### 🎯 Insight: Optimasi Customer Journey untuk Meningkatkan Conversion Rate")
    
    # Progress Distribution Analysis
    st.subheader("🔍 1. Progress Distribution & Conversion Analysis")
    
    tahapan_funnel = ['Inisiasi', 'Presentasi', 'Penawaran Harga', 'Negosiasi', 'Paska Deal']
    
    # Current progress distribution
    current_progress = filtered_df.groupby('ID_Customer')['Progress'].last().value_counts()
    current_progress = current_progress.reindex(tahapan_funnel, fill_value=0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_current = px.pie(
            values=current_progress.values, names=current_progress.index,
            title='Current Customer Distribution by Progress',
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig_current, use_container_width=True)
    
    with col2:
        # Conversion rates between stages
        conversion_rates = {}
        for i in range(len(tahapan_funnel)-1):
            current_stage = current_progress[tahapan_funnel[i]]
            next_stage = current_progress[tahapan_funnel[i+1]]
            conversion = (next_stage / current_stage * 100) if current_stage > 0 else 0
            conversion_rates[f"{tahapan_funnel[i]} → {tahapan_funnel[i+1]}"] = conversion
        
        conv_df = pd.DataFrame(list(conversion_rates.items()), columns=['Transition', 'Rate'])
        fig_conv = px.bar(
            conv_df, x='Transition', y='Rate',
            title='Stage Conversion Rates (%)',
            color='Rate', color_continuous_scale='RdYlGn'
        )
        fig_conv.update_xaxes(tickangle=45)
        st.plotly_chart(fig_conv, use_container_width=True)
    
    # Progress Velocity Analysis
    st.subheader("⚡ 2. Progress Velocity & Time Analysis")
    
    # Calculate average time per stage
    stage_durations = []
    for customer_id in filtered_df['ID_Customer'].unique():
        customer_data = filtered_df[filtered_df['ID_Customer'] == customer_id].sort_values('Tanggal')
        stages = customer_data['Progress'].unique()
        
        for i in range(len(stages)-1):
            current_stage = stages[i]
            next_stage = stages[i+1]
            
            current_date = customer_data[customer_data['Progress'] == current_stage]['Tanggal'].min()
            next_date = customer_data[customer_data['Progress'] == next_stage]['Tanggal'].min()
            
            if pd.notnull(current_date) and pd.notnull(next_date):
                duration = (next_date - current_date).days
                if duration >= 0:
                    stage_durations.append({
                        'From_Stage': current_stage,
                        'To_Stage': next_stage,
                        'Duration_Days': duration,
                        'Customer_ID': customer_id
                    })
    
    if stage_durations:
        duration_df = pd.DataFrame(stage_durations)
        avg_durations = duration_df.groupby(['From_Stage', 'To_Stage'])['Duration_Days'].agg(['mean', 'median', 'std']).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_duration = px.bar(
                avg_durations, x='From_Stage', y='mean',
                title='Average Days per Stage Transition',
                color='mean', color_continuous_scale='Plasma'
            )
            fig_duration.update_xaxes(title='Stage Transition')
            fig_duration.update_yaxes(title='Average Days')
            st.plotly_chart(fig_duration, use_container_width=True)
        
        with col2:
            # Stage bottleneck analysis
            bottleneck_stages = avg_durations.nlargest(3, 'mean')[['From_Stage', 'mean']]
            fig_bottleneck = px.bar(
                bottleneck_stages, x='From_Stage', y='mean',
                title='Top 3 Bottleneck Stages',
                color='mean', color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_bottleneck, use_container_width=True)
    
    # Progress Success Patterns
    st.subheader("🎯 3. Success Pattern Analysis")
    
    # Analyze successful vs unsuccessful patterns
    successful_customers = filtered_df[filtered_df['Progress'] == 'Paska Deal']['ID_Customer'].unique()
    
    success_patterns = {}
    unsuccessful_patterns = {}
    
    for customer_id in filtered_df['ID_Customer'].unique():
        customer_journey = filtered_df[filtered_df['ID_Customer'] == customer_id].sort_values('Tanggal')['Progress'].tolist()
        journey_str = ' → '.join(customer_journey)
        
        if customer_id in successful_customers:
            success_patterns[journey_str] = success_patterns.get(journey_str, 0) + 1
        else:
            unsuccessful_patterns[journey_str] = unsuccessful_patterns.get(journey_str, 0) + 1
    
    # Top success patterns
    top_success = sorted(success_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
    top_unsuccessful = sorted(unsuccessful_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏆 Top 5 Successful Journey Patterns:**")
        for i, (pattern, count) in enumerate(top_success, 1):
            st.write(f"{i}. {pattern} ({count} customers)")
    
    with col2:
        st.markdown("**❌ Top 5 Unsuccessful Journey Patterns:**")
        for i, (pattern, count) in enumerate(top_unsuccessful, 1):
            st.write(f"{i}. {pattern} ({count} customers)")
    
    # Progress Insights & Recommendations
    st.subheader("💡 4. Progress Insights & Optimization Recommendations")
    
    # Calculate key metrics
    total_customers = filtered_df['ID_Customer'].nunique()
    successful_customers_count = len(successful_customers)
    overall_success_rate = (successful_customers_count / total_customers * 100) if total_customers > 0 else 0
    
    if stage_durations:
        longest_stage = avg_durations.loc[avg_durations['mean'].idxmax(), 'From_Stage']
        avg_longest_duration = avg_durations['mean'].max()
    else:
        longest_stage = "N/A"
        avg_longest_duration = 0
    
    st.markdown(f"""
    <div style='background-color:#e3f2fd;padding:1.5rem;border-radius:10px;border-left:5px solid #1976d2;'>
        <h4>📊 <b>Key Progress Metrics</b></h4>
        <ul>
            <li>📈 <b>Overall Success Rate:</b> {overall_success_rate:.1f}% ({successful_customers_count}/{total_customers} customers)</li>
            <li>⏳ <b>Biggest Bottleneck:</b> {longest_stage} stage ({avg_longest_duration:.1f} days average)</li>
            <li>🎯 <b>Optimal Journey:</b> {top_success[0][0] if top_success else 'N/A'}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background-color:#fff3e0;padding:1.5rem;border-radius:10px;border-left:5px solid #f57c00;margin-top:1rem;'>
        <h4>🚀 <b>Optimization Recommendations</b></h4>
        <ol>
            <li><b>Focus on {longest_stage} Stage:</b> Reduce average duration through process optimization</li>
            <li><b>Replicate Success Patterns:</b> Train team on most successful customer journey patterns</li>
            <li><b>Early Intervention:</b> Identify customers following unsuccessful patterns for proactive support</li>
            <li><b>Stage-Specific Training:</b> Develop targeted training for bottleneck stages</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

elif page == "🔍 Factor Analysis":
    st.title("🔍 Factor Analysis - Deep Dive Success Drivers")
    st.markdown("### 🎯 Insight: Identifikasi Faktor Kunci Keberhasilan Sales")
    
    # Customer Profile Analysis
    st.subheader("👤 1. Customer Profile Success Factors")
    
    # Analyze success by customer characteristics
    latest_customer_data = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last()
    
    # Success by Status Customer
    status_success = latest_customer_data.groupby('Status_Customer').agg({
        'ID_Customer': 'count',
        'Progress': lambda x: (x == 'Paska Deal').sum()
    }).rename(columns={'ID_Customer': 'Total', 'Progress': 'Success'})
    status_success['Success_Rate'] = (status_success['Success'] / status_success['Total'] * 100)
    
    # Success by Segmen
    segmen_success = latest_customer_data.groupby('Segmen').agg({
        'ID_Customer': 'count',
        'Progress': lambda x: (x == 'Paska Deal').sum()
    }).rename(columns={'ID_Customer': 'Total', 'Progress': 'Success'})
    segmen_success['Success_Rate'] = (segmen_success['Success'] / segmen_success['Total'] * 100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_status = px.bar(
            status_success.reset_index(), x='Status_Customer', y='Success_Rate',
            title='Success Rate by Customer Status (%)',
            color='Success_Rate', color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        fig_segmen = px.bar(
            segmen_success.reset_index(), x='Segmen', y='Success_Rate',
            title='Success Rate by Segment (%)',
            color='Success_Rate', color_continuous_scale='Plasma'
        )
        st.plotly_chart(fig_segmen, use_container_width=True)
    
    # Sales Activity Factors
    st.subheader("📊 2. Sales Activity Success Factors")
    
    # Visit frequency analysis
    visit_frequency = filtered_df.groupby('ID_Customer').size()
    customer_success = filtered_df.groupby('ID_Customer')['Progress'].last() == 'Paska Deal'
    
    frequency_success = pd.DataFrame({
        'Visit_Count': visit_frequency,
        'Success': customer_success
    })
    
    # Categorize visit frequency
    frequency_success['Frequency_Category'] = pd.cut(
        frequency_success['Visit_Count'], 
        bins=[0, 2, 4, 6, float('inf')], 
        labels=['Low (1-2)', 'Medium (3-4)', 'High (5-6)', 'Very High (7+)']
    )
    
    freq_analysis = frequency_success.groupby('Frequency_Category').agg({
        'Visit_Count': 'count',
        'Success': 'sum'
    }).rename(columns={'Visit_Count': 'Total_Customers', 'Success': 'Successful_Customers'})
    freq_analysis['Success_Rate'] = (freq_analysis['Successful_Customers'] / freq_analysis['Total_Customers'] * 100)
    
    # Visit type analysis
    visit_type_success = {}
    for visit_type in filtered_df['Jenis_Kunjungan'].unique():
        customers_with_type = filtered_df[filtered_df['Jenis_Kunjungan'] == visit_type]['ID_Customer'].unique()
        success_count = len([c for c in customers_with_type if customer_success.get(c, False)])
        total_count = len(customers_with_type)
        visit_type_success[visit_type] = {
            'Total': total_count,
            'Success': success_count,
            'Success_Rate': (success_count / total_count * 100) if total_count > 0 else 0
        }
    
    visit_type_df = pd.DataFrame(visit_type_success).T
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_freq = px.bar(
            freq_analysis.reset_index(), x='Frequency_Category', y='Success_Rate',
            title='Success Rate by Visit Frequency (%)',
            color='Success_Rate', color_continuous_scale='Greens'
        )
        st.plotly_chart(fig_freq, use_container_width=True)
    
    with col2:
        fig_type = px.bar(
            visit_type_df.reset_index(), x='index', y='Success_Rate',
            title='Success Rate by Visit Type (%)',
            color='Success_Rate', color_continuous_scale='Blues'
        )
        fig_type.update_xaxes(title='Visit Type')
        st.plotly_chart(fig_type, use_container_width=True)
    
    # Sales Performance Factors
    st.subheader("🏅 3. Sales Team Performance Factors")
    
    # Success rate by sales level
    sales_level_success = filtered_df.groupby(['Nama_Sales', 'Level_Sales']).agg({
        'ID_Customer': 'nunique'
    }).reset_index()
    
    # Get success count per sales
    sales_success_count = latest_customer_data[latest_customer_data['Progress'] == 'Paska Deal'].groupby('Nama_Sales').size()
    sales_total_count = latest_customer_data.groupby('Nama_Sales').size()
    sales_success_rate = (sales_success_count / sales_total_count * 100).fillna(0)
    
    # Merge with level data
    sales_performance = pd.DataFrame({
        'Nama_Sales': sales_success_rate.index,
        'Success_Rate': sales_success_rate.values
    })
    
    level_mapping = filtered_df.groupby('Nama_Sales')['Level_Sales'].first()
    sales_performance['Level_Sales'] = sales_performance['Nama_Sales'].map(level_mapping)
    
    # Level performance analysis
    level_performance = sales_performance.groupby('Level_Sales')['Success_Rate'].agg(['mean', 'count']).reset_index()
    level_performance.columns = ['Level_Sales', 'Avg_Success_Rate', 'Count']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_level = px.bar(
            level_performance, x='Level_Sales', y='Avg_Success_Rate',
            title='Average Success Rate by Sales Level (%)',
            color='Avg_Success_Rate', color_continuous_scale='Oranges'
        )
        st.plotly_chart(fig_level, use_container_width=True)
    
    with col2:
        fig_individual = px.scatter(
            sales_performance, x='Level_Sales', y='Success_Rate',
            size=[10]*len(sales_performance), hover_name='Nama_Sales',
            title='Individual Sales Success Rate by Level',
            color='Success_Rate', color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_individual, use_container_width=True)
    
    # Factor Insights & Recommendations
    st.subheader("💡 4. Factor Analysis Insights & Recommendations")
    
    # Identify key success factors
    best_status = status_success['Success_Rate'].idxmax()
    best_segmen = segmen_success['Success_Rate'].idxmax()
    best_frequency = freq_analysis['Success_Rate'].idxmax()
    best_visit_type = visit_type_df['Success_Rate'].idxmax()
    best_level = level_performance.loc[level_performance['Avg_Success_Rate'].idxmax(), 'Level_Sales']
    
    st.markdown(f"""
    <div style='background-color:#e8f5e9;padding:1.5rem;border-radius:10px;border-left:5px solid #2e7d32;'>
        <h4>🔍 <b>Key Success Factors Identified</b></h4>
        <ul>
            <li>👤 <b>Best Customer Profile:</b> {best_status} status, {best_segmen} segment</li>
            <li>📊 <b>Optimal Visit Strategy:</b> {best_frequency} visit frequency, {best_visit_type} visit type</li>
            <li>🏅 <b>Top Performing Level:</b> {best_level} ({level_performance.loc[level_performance['Level_Sales']==best_level, 'Avg_Success_Rate'].iloc[0]:.1f}% success rate)</li>
            <li>📈 <b>Success Pattern:</b> Higher visit frequency correlates with better outcomes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background-color:#e3f2fd;padding:1.5rem;border-radius:10px;border-left:5px solid #1976d2;margin-top:1rem;'>
        <h4>🎯 <b>Strategic Recommendations</b></h4>
        <ol>
            <li><b>Target Customer Focus:</b> Prioritize {best_status} customers in {best_segmen} segment</li>
            <li><b>Visit Strategy Optimization:</b> Implement {best_frequency} visit frequency as standard</li>
            <li><b>Visit Type Prioritization:</b> Increase {best_visit_type} activities for better conversion</li>
            <li><b>Team Development:</b> Promote best practices from {best_level} level sales to other levels</li>
            <li><b>Resource Allocation:</b> Invest more in high-success-rate factors and customer profiles</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

elif page == "📅 Timeline Analysis":
    st.title("📅 Timeline Analysis - Temporal Patterns & Trends")
    st.markdown("### 🎯 Insight: Optimasi Timing Strategi untuk Maksimal Impact")
    
    # Time-based Performance Analysis
    st.subheader("📈 1. Sales Performance Over Time")
    
    # Daily/Weekly/Monthly trends
    filtered_df['Week'] = filtered_df['Tanggal'].dt.to_period('W')
    filtered_df['Month'] = filtered_df['Tanggal'].dt.to_period('M')
    filtered_df['DayOfWeek'] = filtered_df['Tanggal'].dt.day_name()
    filtered_df['Hour'] = filtered_df['Tanggal'].dt.hour
    
    # Weekly visits trend
    weekly_visits = filtered_df.groupby('Week').size()
    weekly_deals = filtered_df[filtered_df['Progress'] == 'Paska Deal'].groupby('Week').size()
    
    # Monthly revenue trend
    monthly_revenue = filtered_df.groupby(['Month', 'ID_Customer'])['Nilai_Kontrak'].last().groupby('Month').sum()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_weekly = px.line(
            x=weekly_visits.index.astype(str), y=weekly_visits.values,
            title='Weekly Visit Trends',
            labels={'x': 'Week', 'y': 'Number of Visits'}
        )
        fig_weekly.update_traces(mode='lines+markers')
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    with col2:
        fig_monthly = px.bar(
            x=monthly_revenue.index.astype(str), y=monthly_revenue.values,
            title='Monthly Revenue Trends (Rp)',
            labels={'x': 'Month', 'y': 'Revenue'}
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Day of Week Analysis
    st.subheader("📅 2. Day-of-Week Performance Patterns")
    
    dow_analysis = filtered_df.groupby('DayOfWeek').agg({
        'ID_Customer': 'count',
        'Progress': lambda x: (x == 'Paska Deal').sum(),
        'Nilai_Kontrak': 'sum'
    }).rename(columns={'ID_Customer': 'Total_Visits', 'Progress': 'Deals'})
    
    dow_analysis['Success_Rate'] = (dow_analysis['Deals'] / dow_analysis['Total_Visits'] * 100)
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_analysis = dow_analysis.reindex(day_order)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_dow_visits = px.bar(
            dow_analysis.reset_index(), x='DayOfWeek', y='Total_Visits',
            title='Visit Distribution by Day of Week',
            color='Total_Visits', color_continuous_scale='Blues'
        )
        fig_dow_visits.update_xaxes(tickangle=45)
        st.plotly_chart(fig_dow_visits, use_container_width=True)
    
    with col2:
        fig_dow_success = px.bar(
            dow_analysis.reset_index(), x='DayOfWeek', y='Success_Rate',
            title='Success Rate by Day of Week (%)',
            color='Success_Rate', color_continuous_scale='Greens'
        )
        fig_dow_success.update_xaxes(tickangle=45)
        st.plotly_chart(fig_dow_success, use_container_width=True)
    
    # Sales Cycle Analysis
    st.subheader("🔄 3. Sales Cycle Timeline Analysis")
    
    # Calculate average sales cycle duration
    sales_cycles = []
    for customer_id in filtered_df['ID_Customer'].unique():
        customer_data = filtered_df[filtered_df['ID_Customer'] == customer_id].sort_values('Tanggal')
        first_contact = customer_data['Tanggal'].min()
        last_activity = customer_data['Tanggal'].max()
        final_status = customer_data['Progress'].iloc[-1]
        
        cycle_duration = (last_activity - first_contact).days
        sales_cycles.append({
            'Customer_ID': customer_id,
            'Cycle_Duration': cycle_duration,
            'Final_Status': final_status,
            'First_Contact': first_contact,
            'Last_Activity': last_activity
        })
    
    cycles_df = pd.DataFrame(sales_cycles)
    
    # Successful vs unsuccessful cycle durations
    successful_cycles = cycles_df[cycles_df['Final_Status'] == 'Paska Deal']['Cycle_Duration']
    unsuccessful_cycles = cycles_df[cycles_df['Final_Status'] != 'Paska Deal']['Cycle_Duration']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_cycle_hist = px.histogram(
            cycles_df, x='Cycle_Duration', color='Final_Status',
            title='Sales Cycle Duration Distribution',
            nbins=20, barmode='overlay'
        )
        fig_cycle_hist.update_xaxes(title='Duration (Days)')
        st.plotly_chart(fig_cycle_hist, use_container_width=True)
    
    with col2:
        cycle_stats = pd.DataFrame({
            'Metric': ['Successful Avg', 'Unsuccessful Avg', 'Successful Median', 'Unsuccessful Median'],
            'Value': [
                successful_cycles.mean() if len(successful_cycles) > 0 else 0,
                unsuccessful_cycles.mean() if len(unsuccessful_cycles) > 0 else 0,
                successful_cycles.median() if len(successful_cycles) > 0 else 0,
                unsuccessful_cycles.median() if len(unsuccessful_cycles) > 0 else 0
            ]
        })
        
        fig_cycle_stats = px.bar(
            cycle_stats, x='Metric', y='Value',
            title='Sales Cycle Statistics (Days)',
            color='Value', color_continuous_scale='Viridis'
        )
        fig_cycle_stats.update_xaxes(tickangle=45)
        st.plotly_chart(fig_cycle_stats, use_container_width=True)
    
    # Seasonal Analysis
    st.subheader("🌊 4. Seasonal & Temporal Insights")
    
    # Monthly performance comparison
    monthly_performance = filtered_df.groupby('Month').agg({
        'ID_Customer': 'nunique',
        'Progress': lambda x: (x == 'Paska Deal').sum(),
        'Nilai_Kontrak': 'sum'
    }).rename(columns={'ID_Customer': 'Unique_Customers', 'Progress': 'Deals'})
    
    monthly_performance['Deals_per_Customer'] = monthly_performance['Deals'] / monthly_performance['Unique_Customers']
    monthly_performance['Revenue_per_Customer'] = monthly_performance['Nilai_Kontrak'] / monthly_performance['Unique_Customers']
    
    fig_seasonal = px.line(
        monthly_performance.reset_index(), x='Month', y=['Deals_per_Customer', 'Revenue_per_Customer'],
        title='Monthly Performance Efficiency Trends'
    )
    fig_seasonal.update_xaxes(title='Month')
    st.plotly_chart(fig_seasonal, use_container_width=True)
    
    # Timeline Insights & Recommendations
    st.subheader("💡 5. Timeline Insights & Optimization Recommendations")
    
    # Calculate key temporal metrics
    best_day = dow_analysis['Success_Rate'].idxmax()
    worst_day = dow_analysis['Success_Rate'].idxmin()
    avg_successful_cycle = successful_cycles.mean() if len(successful_cycles) > 0 else 0
    avg_unsuccessful_cycle = unsuccessful_cycles.mean() if len(unsuccessful_cycles) > 0 else 0
    best_month = monthly_performance['Deals_per_Customer'].idxmax()
    
    st.markdown(f"""
    <div style='background-color:#e8f5e9;padding:1.5rem;border-radius:10px;border-left:5px solid #2e7d32;'>
        <h4>⏰ <b>Temporal Success Patterns</b></h4>
        <ul>
            <li>📅 <b>Best Performance Day:</b> {best_day} ({dow_analysis.loc[best_day, 'Success_Rate']:.1f}% success rate)</li>
            <li>📉 <b>Challenging Day:</b> {worst_day} ({dow_analysis.loc[best_day, 'Success_Rate']:.1f}% success rate)</li>
            <li>⏱️ <b>Optimal Sales Cycle:</b> {avg_successful_cycle:.1f} days for successful deals</li>
            <li>📈 <b>Peak Month:</b> {best_month} (highest deals per customer ratio)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background-color:#fff3e0;padding:1.5rem;border-radius:10px;border-left:5px solid #f57c00;margin-top:1rem;'>
        <h4>🎯 <b>Timeline Optimization Strategies</b></h4>
        <ol>
            <li><b>Focus on {best_day}:</b> Schedule important meetings and follow-ups on high-performance days</li>
            <li><b>Improve {worst_day} Performance:</b> Analyze and address factors causing lower success rates</li>
            <li><b>Optimize Sales Cycle:</b> Target {avg_successful_cycle:.0f}-day cycles for better success probability</li>
            <li><b>Seasonal Planning:</b> Prepare resources and campaigns around peak performance periods</li>
            <li><b>Early Warning System:</b> Flag deals exceeding {avg_successful_cycle + 14:.0f} days for intervention</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

elif page == "👤 Profil Sales":
    st.title("👤 Profil Sales - Individual Performance Analysis")
    st.markdown("### 🎯 Insight: Analisis Mendalam Performa Individual untuk Optimasi Tim")
    
    # Sales Selection for detailed analysis
    st.subheader("🔍 Select Sales for Detailed Analysis")
    selected_sales = st.selectbox(
        "Pilih Sales untuk Analisis Detail:",
        options=filtered_df['Nama_Sales'].unique(),
        index=0
    )
    
    sales_data = filtered_df[filtered_df['Nama_Sales'] == selected_sales]
    
    # Sales Profile Overview
    st.subheader(f"📊 Profile Overview - {selected_sales}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_customers = sales_data['ID_Customer'].nunique()
        st.metric("Total Customers", total_customers)
    
    with col2:
        total_visits = len(sales_data)
        st.metric("Total Visits", total_visits)
    
    with col3:
        avg_visits_per_customer = total_visits / total_customers if total_customers > 0 else 0
        st.metric("Avg Visits/Customer", f"{avg_visits_per_customer:.1f}")
    
    with col4:
        success_rate = (sales_data.groupby('ID_Customer')['Progress'].last() == 'Paska Deal').mean() * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Individual Performance Metrics
    st.subheader("🏅 Individual Performance Metrics")
    
    # Sales activity distribution
    activity_dist = sales_data['Jenis_Kunjungan'].value_counts()
    progress_dist = sales_data.groupby('ID_Customer')['Progress'].last().value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_activity = px.pie(
            values=activity_dist.values, names=activity_dist.index,
            title=f'{selected_sales} - Activity Distribution',
            color_discrete_sequence=px.colors.sequential.Set3
        )
        st.plotly_chart(fig_activity, use_container_width=True)
    
    with col2:
        fig_progress = px.pie(
            values=progress_dist.values, names=progress_dist.index,
            title=f'{selected_sales} - Customer Progress Distribution',
            color_discrete_sequence=px.colors.sequential.Pastel1
        )
        st.plotly_chart(fig_progress, use_container_width=True)
    
    # Performance vs Team Comparison
    st.subheader("📈 Performance vs Team Comparison")
    
    # Calculate team benchmarks
    team_metrics = filtered_df.groupby('Nama_Sales').agg({
        'ID_Customer': 'nunique',
        'Nilai_Kontrak': 'sum'
    }).rename(columns={'ID_Customer': 'Total_Customers', 'Nilai_Kontrak': 'Total_Revenue'})
    
    # Success rate calculation
    team_success_rates = []
    for sales in team_metrics.index:
        sales_customer_data = filtered_df[filtered_df['Nama_Sales'] == sales]
        success_rate = (sales_customer_data.groupby('ID_Customer')['Progress'].last() == 'Paska Deal').mean() * 100
        team_success_rates.append(success_rate)
    
    team_metrics['Success_Rate'] = team_success_rates
    team_metrics['Revenue_per_Customer'] = team_metrics['Total_Revenue'] / team_metrics['Total_Customers']
    
    # Individual vs team comparison
    individual_stats = team_metrics.loc[selected_sales]
    team_avg = team_metrics.mean()
    
    comparison_data = pd.DataFrame({
        'Metric': ['Total Customers', 'Success Rate (%)', 'Revenue per Customer (Rp)', 'Total Revenue (Rp)'],
        'Individual': [
            individual_stats['Total_Customers'],
            individual_stats['Success_Rate'],
            individual_stats['Revenue_per_Customer'],
            individual_stats['Total_Revenue']
        ],
        'Team Average': [
            team_avg['Total_Customers'],
            team_avg['Success_Rate'],
            team_avg['Revenue_per_Customer'],
            team_avg['Total_Revenue']
        ]
    })
    
    comparison_data['Performance_Ratio'] = comparison_data['Individual'] / comparison_data['Team Average']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_comparison = px.bar(
            comparison_data, x='Metric', y=['Individual', 'Team Average'],
            title=f'{selected_sales} vs Team Performance',
            barmode='group'
        )
        fig_comparison.update_xaxes(tickangle=45)
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    with col2:
        # Performance radar chart
        fig_radar = px.line_polar(
            comparison_data, r='Performance_Ratio', theta='Metric',
            title=f'{selected_sales} Performance Ratio vs Team',
            line_close=True
        )
        fig_radar.update_traces(fill='toself')
        st.plotly_chart(fig_radar, use_container_width=True)
    
    # Time-based Performance Analysis
    st.subheader("📅 Time-based Performance Analysis")
    
    # Daily/weekly performance
    sales_data['Week'] = sales_data['Tanggal'].dt.to_period('W')
    weekly_performance = sales_data.groupby('Week').agg({
        'ID_Customer': 'nunique',
        'Jenis_Kunjungan': 'count'
    }).rename(columns={'ID_Customer': 'Unique_Customers', 'Jenis_Kunjungan': 'Total_Activities'})
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_weekly_customers = px.line(
            weekly_performance.reset_index(), x='Week', y='Unique_Customers',
            title=f'{selected_sales} - Weekly Customer Reach',
            markers=True
        )
        fig_weekly_customers.update_xaxes(title='Week')
        st.plotly_chart(fig_weekly_customers, use_container_width=True)
    
    with col2:
        fig_weekly_activities = px.line(
            weekly_performance.reset_index(), x='Week', y='Total_Activities',
            title=f'{selected_sales} - Weekly Activities',
            markers=True
        )
        fig_weekly_activities.update_xaxes(title='Week')
        st.plotly_chart(fig_weekly_activities, use_container_width=True)
    
    # Customer Journey Analysis
    st.subheader("🛤️ Customer Journey Analysis")
    
    # Successful customer journeys
    successful_customers = sales_data[sales_data['Progress'] == 'Paska Deal']['ID_Customer'].unique()
    
    journey_patterns = {}
    for customer_id in sales_data['ID_Customer'].unique():
        customer_journey = sales_data[sales_data['ID_Customer'] == customer_id].sort_values('Tanggal')
        journey_steps = customer_journey['Progress'].unique()
        journey_str = ' → '.join(journey_steps)
        
        is_successful = customer_id in successful_customers
        if journey_str not in journey_patterns:
            journey_patterns[journey_str] = {'successful': 0, 'total': 0}
        
        journey_patterns[journey_str]['total'] += 1
        if is_successful:
            journey_patterns[journey_str]['successful'] += 1
    
    # Convert to DataFrame
    journey_df = pd.DataFrame([
        {
            'Journey': journey,
            'Total_Customers': data['total'],
            'Successful_Customers': data['successful'],
            'Success_Rate': (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
        }
        for journey, data in journey_patterns.items()
    ]).sort_values('Total_Customers', ascending=False)
    
    st.dataframe(journey_df, use_container_width=True)
    
    # Individual Insights & Recommendations
    st.subheader("💡 Individual Insights & Development Recommendations")
    
    # Performance assessment
    performance_assessment = []
    
    if individual_stats['Success_Rate'] > team_avg['Success_Rate']:
        performance_assessment.append("✅ Above average success rate")
    else:
        performance_assessment.append("⚠️ Below average success rate")
    
    if individual_stats['Revenue_per_Customer'] > team_avg['Revenue_per_Customer']:
        performance_assessment.append("✅ Above average revenue per customer")
    else:
        performance_assessment.append("⚠️ Below average revenue per customer")
    
    if individual_stats['Total_Customers'] > team_avg['Total_Customers']:
        performance_assessment.append("✅ Above average customer reach")
    else:
        performance_assessment.append("⚠️ Below average customer reach")
    
    # Get best performing journey for this sales
    best_journey = journey_df.loc[journey_df['Success_Rate'].idxmax(), 'Journey'] if len(journey_df) > 0 else "N/A"
    
    st.markdown(f"""
    <div style='background-color:#e8f5e9;padding:1.5rem;border-radius:10px;border-left:5px solid #2e7d32;'>
        <h4>📊 <b>Performance Assessment - {selected_sales}</b></h4>
        <ul>
            {"".join(f"<li>{assessment}</li>" for assessment in performance_assessment)}
            <li>🎯 <b>Most Successful Journey Pattern:</b> {best_journey}</li>
            <li>📈 <b>Performance Ratio vs Team:</b> {comparison_data['Performance_Ratio'].mean():.2f}x</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Personalized recommendations
    recommendations = []
    
    if individual_stats['Success_Rate'] < team_avg['Success_Rate']:
        recommendations.append("Focus on improving conversion techniques and follow-up strategies")
    
    if individual_stats['Revenue_per_Customer'] < team_avg['Revenue_per_Customer']:
        recommendations.append("Work on upselling and cross-selling opportunities")
    
    if individual_stats['Total_Customers'] < team_avg['Total_Customers']:
        recommendations.append("Increase prospecting activities and customer outreach")
    
    if avg_visits_per_customer < 3:
        recommendations.append("Increase customer touchpoints and relationship building")
    
    recommendations.append(f"Replicate successful journey pattern: {best_journey}")
    
    st.markdown(f"""
    <div style='background-color:#e3f2fd;padding:1.5rem;border-radius:10px;border-left:5px solid #1976d2;margin-top:1rem;'>
        <h4>🚀 <b>Personalized Development Plan</b></h4>
        <ol>
            {"".join(f"<li>{rec}</li>" for rec in recommendations)}
        </ol>
    </div>
    """, unsafe_allow_html=True)

elif page == "🏅 Sales Performance":
    st.title("🏅 Sales Performance - Team & Individual Excellence Analysis")
    st.markdown("### 🎯 Insight: Optimasi Performa Team Sales untuk Mencapai Target Maksimal")
    
    # Team Performance Overview
    st.subheader("🏆 Team Performance Overview")
    
    # Calculate comprehensive team metrics
    team_performance = filtered_df.groupby('Nama_Sales').agg({
        'ID_Customer': 'nunique',
        'Jenis_Kunjungan': 'count',
        'Nilai_Kontrak': 'sum'
    }).rename(columns={
        'ID_Customer': 'Total_Customers',
        'Jenis_Kunjungan': 'Total_Visits',
        'Nilai_Kontrak': 'Total_Revenue'
    })
    
    # Add success rate and efficiency metrics
    success_rates = []
    avg_cycle_times = []
    
    for sales in team_performance.index:
        sales_data = filtered_df[filtered_df['Nama_Sales'] == sales]
        
        # Success rate calculation
        success_rate = (sales_data.groupby('ID_Customer')['Progress'].last() == 'Paska Deal').mean() * 100
        success_rates.append(success_rate)
        
        # Average cycle time calculation
        successful_customers = sales_data[sales_data['Progress'] == 'Paska Deal']['ID_Customer'].unique()
        cycle_times = []
        
        for customer_id in successful_customers:
            customer_data = sales_data[sales_data['ID_Customer'] == customer_id].sort_values('Tanggal')
            first_contact = customer_data['Tanggal'].min()
            deal_date = customer_data[customer_data['Progress'] == 'Paska Deal']['Tanggal'].max()
            cycle_time = (deal_date - first_contact).days
            if cycle_time >= 0:
                cycle_times.append(cycle_time)
        
        avg_cycle_time = np.mean(cycle_times) if cycle_times else 0
        avg_cycle_times.append(avg_cycle_time)
    
    team_performance['Success_Rate'] = success_rates
    team_performance['Avg_Cycle_Time'] = avg_cycle_times
    team_performance['Visits_per_Customer'] = team_performance['Total_Visits'] / team_performance['Total_Customers']
    team_performance['Revenue_per_Customer'] = team_performance['Total_Revenue'] / team_performance['Total_Customers']
    team_performance['Efficiency_Score'] = (team_performance['Success_Rate'] / 100) * (team_performance['Revenue_per_Customer'] / 1000000)
    
    # Add sales level information
    level_mapping = filtered_df.groupby('Nama_Sales')['Level_Sales'].first()
    team_performance['Level_Sales'] = team_performance.index.map(level_mapping)
    
    # Top performers section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        top_revenue = team_performance['Total_Revenue'].idxmax()
        st.metric("Top Revenue", top_revenue, f"Rp {team_performance.loc[top_revenue, 'Total_Revenue']:,.0f}")
    
    with col2:
        top_success = team_performance['Success_Rate'].idxmax()
        st.metric("Highest Success Rate", top_success, f"{team_performance.loc[top_success, 'Success_Rate']:.1f}%")
    
    with col3:
        most_customers = team_performance['Total_Customers'].idxmax()
        st.metric("Most Customers", most_customers, f"{team_performance.loc[most_customers, 'Total_Customers']:.0f}")
    
    with col4:
        fastest_cycle = team_performance[team_performance['Avg_Cycle_Time'] > 0]['Avg_Cycle_Time'].idxmin()
        st.metric("Fastest Cycle", fastest_cycle, f"{team_performance.loc[fastest_cycle, 'Avg_Cycle_Time']:.1f} days")
    
    # Performance Ranking & Comparison
    st.subheader("📊 Performance Ranking & Analysis")
    
    # Performance metrics visualization
    col1, col2 = st.columns(2)
    
    with col1:
        # Success rate by sales
        fig_success = px.bar(
            team_performance.sort_values('Success_Rate', ascending=True).reset_index(),
            x='Success_Rate', y='Nama_Sales',
            title='Success Rate by Sales Person (%)',
            color='Success_Rate', color_continuous_scale='Viridis',
            orientation='h'
        )
        st.plotly_chart(fig_success, use_container_width=True)
    
    with col2:
        # Revenue per customer
        fig_revenue = px.bar(
            team_performance.sort_values('Revenue_per_Customer', ascending=True).reset_index(),
            x='Revenue_per_Customer', y='Nama_Sales',
            title='Revenue per Customer by Sales (Rp)',
            color='Revenue_per_Customer', color_continuous_scale='Plasma',
            orientation='h'
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Performance by Level Analysis
    st.subheader("🏅 Performance by Sales Level")
    
    level_analysis = team_performance.groupby('Level_Sales').agg({
        'Success_Rate': ['mean', 'std'],
        'Revenue_per_Customer': ['mean', 'std'],
        'Total_Customers': 'sum',
        'Efficiency_Score': 'mean'
    }).round(2)
    
    level_analysis.columns = ['Avg_Success_Rate', 'Std_Success_Rate', 'Avg_Revenue_per_Customer', 'Std_Revenue_per_Customer', 'Total_Customers', 'Avg_Efficiency_Score']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_level_success = px.bar(
            level_analysis.reset_index(),
            x='Level_Sales', y='Avg_Success_Rate',
            title='Average Success Rate by Level (%)',
            color='Avg_Success_Rate', color_continuous_scale='Greens'
        )
        st.plotly_chart(fig_level_success, use_container_width=True)
    
    with col2:
        fig_level_revenue = px.bar(
            level_analysis.reset_index(),
            x='Level_Sales', y='Avg_Revenue_per_Customer',
            title='Average Revenue per Customer by Level (Rp)',
            color='Avg_Revenue_per_Customer', color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_level_revenue, use_container_width=True)
    
    # Performance Distribution Analysis
    st.subheader("📈 Performance Distribution & Benchmarking")
    
    # Scatter plot: Success rate vs Revenue per customer
    fig_scatter = px.scatter(
        team_performance.reset_index(),
        x='Success_Rate', y='Revenue_per_Customer',
        size='Total_Customers', color='Level_Sales',
        hover_name='Nama_Sales',
        title='Success Rate vs Revenue per Customer (Size = Total Customers)',
        labels={'Success_Rate': 'Success Rate (%)', 'Revenue_per_Customer': 'Revenue per Customer (Rp)'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Performance benchmarking table
    st.subheader("📋 Detailed Performance Benchmarking")
    
    # Calculate percentile rankings
    team_performance['Success_Rate_Rank'] = team_performance['Success_Rate'].rank(method='dense', ascending=False)
    team_performance['Revenue_Rank'] = team_performance['Revenue_per_Customer'].rank(method='dense', ascending=False)
    team_performance['Efficiency_Rank'] = team_performance['Efficiency_Score'].rank(method='dense', ascending=False)
    team_performance['Overall_Rank'] = (team_performance['Success_Rate_Rank'] + team_performance['Revenue_Rank'] + team_performance['Efficiency_Rank']) / 3
    
    # Display comprehensive performance table
    performance_display = team_performance.reset_index()[['Nama_Sales', 'Level_Sales', 'Total_Customers', 'Success_Rate', 'Revenue_per_Customer', 'Avg_Cycle_Time', 'Efficiency_Score', 'Overall_Rank']].round(2)
    performance_display = performance_display.sort_values('Overall_Rank')
    
    st.dataframe(performance_display, use_container_width=True)
    
    # Performance Insights & Recommendations
    st.subheader("💡 Team Performance Insights & Strategic Recommendations")
    
    # Calculate key insights
    best_performer = team_performance.loc[team_performance['Overall_Rank'].idxmin()]
    worst_performer = team_performance.loc[team_performance['Overall_Rank'].idxmax()]
    best_level = level_analysis['Avg_Efficiency_Score'].idxmax()
    improvement_needed = team_performance[team_performance['Success_Rate'] < team_performance['Success_Rate'].median()]
    
    st.markdown(f"""
    <div style='background-color:#e8f5e9;padding:1.5rem;border-radius:10px;border-left:5px solid #2e7d32;'>
        <h4>🏆 <b>Top Performance Insights</b></h4>
        <ul>
            <li>🥇 <b>Overall Best Performer:</b> {best_performer.name} (Level: {best_performer['Level_Sales']}, Success Rate: {best_performer['Success_Rate']:.1f}%)</li>
            <li>🏅 <b>Top Performing Level:</b> {best_level} (Average efficiency: {level_analysis.loc[best_level, 'Avg_Efficiency_Score']:.2f})</li>
            <li>📊 <b>Team Average Success Rate:</b> {team_performance['Success_Rate'].mean():.1f}%</li>
            <li>💰 <b>Team Average Revenue per Customer:</b> Rp {team_performance['Revenue_per_Customer'].mean():,.0f}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background-color:#fff3e0;padding:1.5rem;border-radius:10px;border-left:5px solid #f57c00;margin-top:1rem;'>
        <h4>🎯 <b>Strategic Development Recommendations</b></h4>
        <ol>
            <li><b>Best Practice Sharing:</b> Have {best_performer.name} mentor team members on successful techniques</li>
            <li><b>Level-Based Training:</b> Focus on developing {best_level} level practices across all levels</li>
            <li><b>Performance Improvement Plan:</b> {len(improvement_needed)} sales members need focused coaching</li>
            <li><b>Cycle Time Optimization:</b> Target reducing average cycle time to {team_performance['Avg_Cycle_Time'].min():.0f} days</li>
            <li><b>Revenue Enhancement:</b> Focus on upselling strategies to reach top performer benchmarks</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

elif page == "🟦 Sales Performance":
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
