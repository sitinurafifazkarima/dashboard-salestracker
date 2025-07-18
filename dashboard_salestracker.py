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

page = st.sidebar.radio("Pilih Halaman", ["🟦 Aktivitas Sales", "🟦 Performansi Sales", "🟦 Profil Sales", "🟦 Insight & Rekomendasi"])

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
    st.header("📊 Performa Sales - Leaderboard & Analisis")

    # --- Load dataset utama ---
    @st.cache_data

    def load_main():
        with open("performa_sales_closingrate.pkl", "rb") as f:
            data = pickle.load(f)
        return data

    data = load_main()
    sales_df = data['sales_performance']
    low_perf = data['low_performers']
    top_sales = data['top_performer']

#    --- Visualisasi Performa Leaderboard ---
    st.subheader("🏆 Leaderboard: Closing Rate & Konversi")
    fig1 = px.bar(sales_df.reset_index(), 
              x='Nama_Sales', y=['Total_Kunjungan', 'Jumlah_Deal'], 
              barmode='group', 
              color_discrete_sequence=['#90CAF9', '#42A5F5'])
    fig1.update_layout(title="Total Kunjungan vs Jumlah Deal per Sales")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(sales_df.reset_index(), x='Nama_Sales', y='Closing_Rate', color='Closing_Rate', 
              color_continuous_scale='Blues', title="Closing Rate per Sales")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(sales_df.reset_index(), 
              x='Nama_Sales', 
              y=['Nilai_Kontrak_Aktual', 'Prospek_Nilai_Kontrak'], 
              barmode='stack', 
              color_discrete_sequence=['#81C784', '#C8E6C9'],
              title="Nilai Kontrak Aktual & Prospek")
    st.plotly_chart(fig3, use_container_width=True)

# --- Analisis Efisiensi Waktu ---
    st.subheader("⏱️ Efisiensi Waktu: Inisiasi ke Paska Deal")

# Hitung ulang tanpa bergantung pada file pkl
    st.info("Menghitung ulang data efisiensi waktu dari dataframe...")
    df = st.session_state['df']
    paska_deal_customers = df[df["Progress"] == "Paska Deal"]["ID_Customer"].unique()
    df_paska = df[df["ID_Customer"].isin(paska_deal_customers)]
    df_paska = df_paska.sort_values(["ID_Customer", "Tanggal"])

    def get_duration(group):
        inisiasi_date = group[group["Progress"] == "Inisiasi"]["Tanggal"].min()
        paska_deal_date = group[group["Progress"] == "Paska Deal"]["Tanggal"].max()
        if pd.notnull(inisiasi_date) and pd.notnull(paska_deal_date):
            duration = (paska_deal_date - inisiasi_date).days
            return pd.Series({
                "Nama_Sales": group["Nama_Sales"].iloc[0],
                "Durasi_Proses_Sales (hari)": duration
            })
        else:
            return pd.Series()

    durasi_per_customer = df_paska.groupby("ID_Customer").apply(get_duration).dropna()
    durasi_per_sales = durasi_per_customer.groupby("Nama_Sales")["Durasi_Proses_Sales (hari)"].mean()

    leaderboard_df = durasi_per_sales.reset_index().rename(columns={
        "Nama_Sales": "Sales",
        "Durasi_Proses_Sales (hari)": "Rata-rata Durasi (hari)"
    })
    leaderboard_df["Rank"] = leaderboard_df["Rata-rata Durasi (hari)"].rank(method="min").astype(int)
    leaderboard_df = leaderboard_df.sort_values("Rank").reset_index(drop=True)

    best_sales = leaderboard_df.iloc[0]["Sales"]
    best_duration = leaderboard_df.iloc[0]["Rata-rata Durasi (hari)"]

    insight = {
        "sales_tercepat": best_sales,
        "durasi_rata2": best_duration,
        "pesan": f"Sales dengan proses tercepat adalah {best_sales} ({best_duration:.1f} hari). Jadikan sebagai mentor dan acuan pola kerja."
    }

    fig_durasi = px.bar(leaderboard_df, x="Rata-rata Durasi (hari)", y="Sales", orientation="h", 
                    color='Rata-rata Durasi (hari)', color_continuous_scale='Tealgrn',
                    title="Kecepatan Proses Sales")
    fig_durasi.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_durasi, use_container_width=True)

    st.markdown(f"**📌 Insight:** {insight['pesan']}")

# --- Analisis Ketercapaian Target ---
    st.subheader("🎯 Ketercapaian Target per Sales")

    if "Target_Sales" in st.session_state['df'].columns:
        df = st.session_state['df']

        kontrak_per_sales = df[df["Progress"] == "Paska Deal"].groupby("Nama_Sales")["Nilai_Kontrak"].sum().reset_index()
        kontrak_per_sales.rename(columns={"Nilai_Kontrak": "Total_Kontrak"}, inplace=True)

        target_unique = df[["Nama_Sales", "ID_Customer", "Target_Sales"]].drop_duplicates(subset=["Nama_Sales", "ID_Customer"])
        target_per_sales = target_unique.groupby("Nama_Sales")["Target_Sales"].sum().reset_index()

        df_target = pd.merge(kontrak_per_sales, target_per_sales, on="Nama_Sales", how="left")
        df_target["Ketercapaian (%)"] = (df_target["Total_Kontrak"] / df_target["Target_Sales"]) * 100
        df_target["Rank"] = df_target["Ketercapaian (%)"].rank(method="min", ascending=False).astype(int)
        df_target = df_target.sort_values("Rank")

        fig_target = px.bar(df_target, x="Ketercapaian (%)", y="Nama_Sales", orientation="h", 
                        color="Ketercapaian (%)", color_continuous_scale="Blues_r",
                        title="Ketercapaian Target per Sales")
        st.plotly_chart(fig_target, use_container_width=True)

        if not df_target.empty:
            top_sales_target = df_target.iloc[0]
            st.markdown(f"**📌 Insight:** {top_sales_target['Nama_Sales']} mencapai {top_sales_target['Ketercapaian (%)']:.1f}% dari targetnya. Jadikan contoh pola pendekatannya.")
    else:
        st.warning("Kolom Target_Sales tidak ditemukan di dataframe. Tidak bisa menghitung ketercapaian.")


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