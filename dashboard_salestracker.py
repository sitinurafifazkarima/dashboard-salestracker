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
    with open("overview_metrics.pkl", "rb") as f:
        overview_data = pickle.load(f)

    kontrak_summary = overview_data['nilai_kontrak_breakdown']

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
    st.title("🟦 Leaderboard & Performansi Sales")

    # Load data performa dari pickle utama
    with open("performa_sales.pkl", "rb") as f:
        performa_data = pickle.load(f)

    sales_perf = performa_data['sales_performance']
    low_perf = performa_data['low_performers']
    top_sales = performa_data['top_performer']

    # ==========================
    # Leaderboard Utama
    # ==========================
    st.subheader("📊 Leaderboard Performa Sales (Deal, Kontrak, Closing Rate)")
    st.dataframe(
        sales_perf.reset_index().rename(columns={sales_perf.index.name: 'Nama_Sales'}),
        use_container_width=True
    )

    # Visualisasi performa
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Jumlah Kunjungan vs Jumlah Deal**")
        fig1 = px.bar(
            sales_perf.reset_index(),
            x='Nama_Sales',
            y=['Total_Kunjungan', 'Jumlah_Deal'],
            barmode='group',
            color_discrete_sequence=px.colors.sequential.Teal
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("**Closing Rate per Sales**")
        fig2 = px.bar(
            sales_perf.reset_index(),
            x='Nama_Sales',
            y='Closing_Rate',
            color='Closing_Rate',
            color_continuous_scale='BuGn',
            labels={'Closing_Rate': 'Closing Rate (%)'}
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Nilai Kontrak Aktual vs Prospek")
    fig3 = px.bar(
        sales_perf.reset_index(),
        x='Nama_Sales',
        y=['Nilai_Kontrak_Aktual', 'Prospek_Nilai_Kontrak'],
        title='Nilai Kontrak per Sales',
        barmode='stack',
        color_discrete_sequence=px.colors.sequential.Mint
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ==========================
    # Efisiensi Waktu: Inisiasi ke Deal
    # ==========================
    st.subheader("⏱️ Leaderboard Efisiensi Proses (Dari Inisiasi ke Deal)")

    # Ambil hanya customer yang sampai tahap Paska Deal
    paska_deal_customers = df[df["Progress"] == "Paska Deal"]["ID_Customer"].unique()
    df_paska = df[df["ID_Customer"].isin(paska_deal_customers)].copy().sort_values(["ID_Customer", "Tanggal"])

    # Hitung durasi per customer
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

    best_sales = leaderboard_durasi.iloc[0]["Sales"]
    best_duration = leaderboard_durasi.iloc[0]["Rata-rata Durasi (hari)"]

    st.dataframe(leaderboard_durasi, use_container_width=True)

    fig4 = px.bar(
        leaderboard_durasi,
        y='Sales',
        x='Rata-rata Durasi (hari)',
        orientation='h',
        title="Kecepatan Proses Sales: Inisiasi ke Paska Deal",
        color='Rata-rata Durasi (hari)',
        color_continuous_scale='Greens'
    )
    fig4.update_layout(yaxis=dict(categoryorder='total ascending'))
    st.plotly_chart(fig4, use_container_width=True)

    # ==========================
    # Ketercapaian Target
    # ==========================
    st.subheader("🎯 Leaderboard Ketercapaian Target Sales")

    kontrak_per_sales = df[df["Progress"] == "Paska Deal"].groupby("Nama_Sales")["Nilai_Kontrak"].sum().reset_index()
    kontrak_per_sales.rename(columns={"Nilai_Kontrak": "Total_Kontrak"}, inplace=True)
    target_unique = df[["Nama_Sales", "ID_Customer", "Target_Sales"]].drop_duplicates()
    target_per_sales = target_unique.groupby("Nama_Sales")["Target_Sales"].sum().reset_index()

    df_target = pd.merge(kontrak_per_sales, target_per_sales, on="Nama_Sales", how="left")
    df_target["Ketercapaian (%)"] = (df_target["Total_Kontrak"] / df_target["Target_Sales"]) * 100
    df_target = df_target.sort_values("Ketercapaian (%)", ascending=False).reset_index(drop=True)
    df_target["Rank"] = df_target["Ketercapaian (%)"].rank(method="min", ascending=False).astype(int)

    st.dataframe(df_target[["Rank", "Nama_Sales", "Total_Kontrak", "Target_Sales", "Ketercapaian (%)"]], use_container_width=True)

    fig5 = px.bar(
        df_target,
        y="Nama_Sales",
        x="Ketercapaian (%)",
        orientation="h",
        color="Ketercapaian (%)",
        color_continuous_scale="Blues",
        title="Ketercapaian Target per Sales"
    )
    fig5.update_layout(yaxis=dict(categoryorder='total ascending'))
    st.plotly_chart(fig5, use_container_width=True)

    # ==========================
    # Resume Insight & Rekomendasi Akhir
    # ==========================
    st.subheader("🧠 Resume Insight & Rekomendasi")

    # Top performer (multi-metric)
    top_by_closing = sales_perf['Closing_Rate'].idxmax()
    top_by_kontrak = sales_perf['Nilai_Kontrak_Aktual'].idxmax()
    top_by_target = df_target.iloc[0]['Nama_Sales']
    
    low_names = ', '.join(low_perf.index.tolist()) if not low_perf.empty else "-"

    st.markdown(f"""
    <div style='background-color:#f1f8e9;padding:1.5rem;border-radius:10px;border-left:5px solid #2e7d32;'>
        <h4>🔝 <b>Sales Terbaik</b></h4>
        <ul>
            <li>📈 <b>Closing Rate Tertinggi:</b> {top_by_closing}</li>
            <li>💰 <b>Nilai Kontrak Tertinggi:</b> {top_by_kontrak}</li>
            <li>🎯 <b>Ketercapaian Target Tertinggi:</b> {top_by_target}</li>
            <li>⚡ <b>Proses Paling Cepat (Inisiasi → Deal):</b> {best_sales} ({best_duration:.1f} hari)</li>
        </ul>
        ✅ Disarankan menjadikan mereka sebagai <b>mentor atau role model</b> bagi rekan-rekan lainnya.
    </div>
    """, unsafe_allow_html=True)

    if not low_perf.empty:
        st.markdown(f"""
        <div style='background-color:#fff3e0;padding:1.5rem;border-radius:10px;border-left:5px solid #f57c00;margin-top:1rem;'>
            <h4>🚩 <b>Sales yang Perlu Pendampingan</b></h4>
            <p>📉 Ditemukan sales dengan aktivitas tinggi namun konversi rendah (Closing Rate &lt; 15%):</p>
            <p><b>{low_names}</b></p>
            <p>🔧 Rekomendasi: Lakukan <b>coaching</b> dan evaluasi teknik follow-up atau pendekatan terhadap customer.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success("✅ Tidak ada sales yang perlu pendampingan berdasarkan kriteria performa saat ini.")

    
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
