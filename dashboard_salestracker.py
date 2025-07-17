
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

st.set_page_config(page_title="Sales Tracker Dashboard", layout="wide")
st.markdown("""
<h1 style='text-align:center; color:#2E86C1;'>📊 Dashboard Analisis Sales Tracker</h1>
<p style='text-align:center;'>Pantau performa sales, pipeline, dan insight strategi secara real-time.</p>
""", unsafe_allow_html=True)

# Sidebar filter
with st.sidebar:
    st.header("Filter Data")
    # Load data
    try:
        df = pd.read_csv("sales_visits_finalbgt_enriched.csv")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()
    sales_list = df['Nama_Sales'].unique()
    selected_sales = st.multiselect("Pilih Sales", sales_list, default=sales_list)
    segmen_list = df['Segmen'].unique() if 'Segmen' in df.columns else []
    selected_segmen = st.multiselect("Pilih Segmen", segmen_list, default=segmen_list)
    status_list = df['Status_Kontrak'].unique()
    selected_status = st.multiselect("Status Kontrak", status_list, default=status_list)

filtered_df = df[
    df['Nama_Sales'].isin(selected_sales) &
    (df['Segmen'].isin(selected_segmen) if 'Segmen' in df.columns else True) &
    df['Status_Kontrak'].isin(selected_status)
]

# Tabs for dashboard sections
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "KPI & Target", "Pipeline & Heatmap", "Root Cause", "Prioritas", "Analisis Lanjutan", "Insight"
])

# --- Root Cause (tab3) ---
with tab3:
    st.subheader("Aktivitas Sales vs Ketercapaian Target")
    # Kunjungan per sales
    kunjungan_per_sales = filtered_df.groupby('Nama_Sales')['ID_Kunjungan'].nunique()
    deal_df = filtered_df[filtered_df['Status_Kontrak'].str.lower() == 'deal']
    nilai_kontrak_per_sales = deal_df.groupby('Nama_Sales')['Nilai_Kontrak'].sum()
    target_sales_per_sales = filtered_df.groupby('Nama_Sales')['Target_Sales'].sum()
    ketercapaian_target = (nilai_kontrak_per_sales / target_sales_per_sales).fillna(0)
    compare_df = pd.DataFrame({
        'Kunjungan': kunjungan_per_sales,
        'Ketercapaian_Target': ketercapaian_target
    }).fillna(0)
    fig4, ax4 = plt.subplots(figsize=(7,5))
    ax4.scatter(compare_df['Kunjungan'], compare_df['Ketercapaian_Target'], alpha=0.7, color='#1ABC9C')
    ax4.set_xlabel('Jumlah Kunjungan/FU')
    ax4.set_ylabel('Rasio Ketercapaian Target')
    ax4.set_title('Aktivitas Sales vs Ketercapaian Target')
    ax4.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig4)

    st.markdown("---")
    st.subheader("Durasi per Tahap untuk Customer Tidak Deal")
    if 'Progress' in filtered_df.columns:
        last_progress = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last().reset_index()
        non_deal = last_progress[last_progress['Status_Kontrak'].str.lower() != 'deal']
        non_deal_ids = non_deal['ID_Customer'].unique() if not non_deal.empty else []
        non_deal_durasi = filtered_df[filtered_df['ID_Customer'].isin(non_deal_ids)].copy()
        if not non_deal_durasi.empty:
            non_deal_durasi['Tanggal'] = pd.to_datetime(non_deal_durasi['Tanggal'])
            def durasi_per_tahap(df_cust):
                df_cust = df_cust.sort_values('Tanggal')
                df_cust['Next_Tanggal'] = df_cust['Tanggal'].shift(-1)
                df_cust['Durasi_Tahap'] = (df_cust['Next_Tanggal'] - df_cust['Tanggal']).dt.days
                return df_cust
            non_deal_durasi = non_deal_durasi.groupby('ID_Customer').apply(durasi_per_tahap)
            durasi_tahap = non_deal_durasi.groupby('Progress')['Durasi_Tahap'].mean().sort_values(ascending=False)
            fig5, ax5 = plt.subplots(figsize=(8,3))
            durasi_tahap.plot(kind='bar', color='#F1948A', edgecolor='black', ax=ax5)
            ax5.set_ylabel('Rata-rata Durasi (hari)')
            ax5.set_title('Rata-rata Durasi di Setiap Tahap (Customer Tidak Deal)')
            ax5.set_xticklabels(ax5.get_xticklabels(), rotation=30)
            st.pyplot(fig5)
        else:
            st.info('Tidak ada data durasi untuk customer tidak deal.')
    else:
        st.info('Kolom Progress tidak tersedia.')

# --- KPI & Target (tab1) ---
with tab1:
    st.subheader("KPI Utama & Target")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_deal = filtered_df[filtered_df['Status_Kontrak'].str.lower() == 'deal']['Nilai_Kontrak'].sum()
        st.metric("Total Nilai Deal", f"Rp {total_deal:,.0f}")
    with col2:
        conversion = (filtered_df['Status_Kontrak'].str.lower() == 'deal').mean() * 100
        st.metric("Conversion Rate", f"{conversion:.1f}%")
    with col3:
        total_prospek = filtered_df['ID_Kunjungan'].nunique()
        st.metric("Total Prospek", f"{total_prospek}")
    with col4:
        rata2_durasi = None
        if 'Tanggal' in filtered_df.columns and 'ID_Customer' in filtered_df.columns:
            try:
                filtered_df['Tanggal'] = pd.to_datetime(filtered_df['Tanggal'])
                deal_df = filtered_df[filtered_df['Status_Kontrak'].str.lower() == 'deal']
                durasi_list = []
                for cust in deal_df['ID_Customer'].unique():
                    cust_data = filtered_df[filtered_df['ID_Customer'] == cust].sort_values('Tanggal')
                    t_awal = cust_data['Tanggal'].min()
                    t_deal = cust_data[cust_data['Status_Kontrak'].str.lower() == 'deal']['Tanggal'].min()
                    if pd.notnull(t_awal) and pd.notnull(t_deal):
                        durasi = (t_deal - t_awal).days
                        durasi_list.append(durasi)
                if durasi_list:
                    rata2_durasi = np.mean(durasi_list)
                    st.metric("Rata-rata Durasi Deal (hari)", f"{rata2_durasi:.1f}")
                else:
                    st.metric("Rata-rata Durasi Deal (hari)", "-")
            except Exception:
                st.metric("Rata-rata Durasi Deal (hari)", "-")
        else:
            st.metric("Rata-rata Durasi Deal (hari)", "-")

    st.markdown("---")
    st.subheader("Ketercapaian Target per Sales")
    deal_df = filtered_df[filtered_df['Status_Kontrak'].str.lower() == 'deal']
    nilai_kontrak_per_sales = deal_df.groupby('Nama_Sales')['Nilai_Kontrak'].sum()
    target_sales_per_sales = filtered_df.groupby('Nama_Sales')['Target_Sales'].sum()
    ketercapaian_target = (nilai_kontrak_per_sales / target_sales_per_sales).fillna(0)
    ketercapaian_target = ketercapaian_target.sort_values(ascending=False)
    fig1, ax1 = plt.subplots(figsize=(10,4))
    ketercapaian_target.plot(kind='bar', color='skyblue', edgecolor='black', ax=ax1)
    ax1.set_ylabel('Rasio Ketercapaian Target')
    ax1.set_title('Ketercapaian Target per Sales (Nilai Kontrak Deal / Target Sales)')
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    st.pyplot(fig1)

    st.markdown("---")
    st.subheader("Conversion Rate per Sales")
    prospek_per_sales = filtered_df.groupby('Nama_Sales')['ID_Kunjungan'].nunique()
    deal_per_sales = deal_df.groupby('Nama_Sales')['ID_Kunjungan'].nunique()
    conversion_rate_sales = (deal_per_sales / prospek_per_sales * 100).fillna(0)
    fig2, ax2 = plt.subplots(figsize=(10,4))
    conversion_rate_sales.sort_values(ascending=False).plot(kind='bar', color='orange', edgecolor='black', ax=ax2)
    ax2.set_ylabel('Conversion Rate (%)')
    ax2.set_title('Conversion Rate per Sales')
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    st.pyplot(fig2)

# --- Pipeline & Heatmap (tab2) ---
with tab2:
    st.subheader("Heatmap Tahap Berhenti per Sales")
    if 'Progress' in filtered_df.columns:
        last_progress = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last().reset_index()
        non_deal = last_progress[last_progress['Status_Kontrak'].str.lower() != 'deal']
        if not non_deal.empty:
            pivot_berhenti = non_deal.pivot_table(index='Nama_Sales', columns='Progress', values='ID_Customer', aggfunc='count', fill_value=0)
            fig3, ax3 = plt.subplots(figsize=(10,6))
            sns.heatmap(pivot_berhenti, annot=True, fmt='d', cmap='Reds', ax=ax3)
            ax3.set_title('Jumlah Customer Berhenti di Setiap Tahap per Sales')
            ax3.set_ylabel('Nama Sales')
            ax3.set_xlabel('Tahap Progress')
            st.pyplot(fig3)
        else:
            st.info('Tidak ada data non-deal untuk heatmap.')
    else:
        st.info('Kolom Progress tidak tersedia.')

with tab4:
    st.subheader("Prioritas & Rekomendasi Follow-up")
    st.dataframe(filtered_df[['Nama_Customer','Nama_Sales','Progress','Status_Kontrak','Nilai_Kontrak']].head(30))
    st.markdown("---")
    st.subheader("Wordcloud Alasan Lost")
    if 'Catatan' in filtered_df.columns and 'Status_Kontrak' in filtered_df.columns:
        last_progress = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last().reset_index()
        lost_notes = last_progress[last_progress['Status_Kontrak'].str.lower() != 'deal']['Catatan'].dropna().astype(str)
        text = ' '.join(lost_notes)
        import re
        from collections import Counter
        stopwords = set([
            'yang','dan','dalam','untuk','dengan','pada','di','ke','dari','sebagai','ada','ini','itu',
            'karena','sudah','belum','tidak','jadi','akan','oleh','atau','masih','saja','hanya','sangat','lebih','kurang','klien'
        ])
        words = re.findall(r'\b\w+\b', text.lower())
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        freq = Counter(filtered)
        if freq:
            wc = WordCloud(width=700, height=300, background_color='white', colormap='cool').generate_from_frequencies(freq)
            fig6, ax6 = plt.subplots(figsize=(8,3))
            ax6.imshow(wc, interpolation='bilinear')
            ax6.axis('off')
            st.pyplot(fig6)
        else:
            st.info('Tidak ada alasan lost yang cukup dominan.')
    else:
        st.info('Kolom Catatan tidak tersedia.')

with tab5:
    st.subheader("Analisis Pola Follow-up")
    if 'Kunjungan_Ke' in filtered_df.columns and 'ID_Customer' in filtered_df.columns:
        followup_count = filtered_df.groupby('ID_Customer')['Kunjungan_Ke'].max()
        last_status = filtered_df.sort_values('Tanggal').groupby('ID_Customer').last().reset_index()
        followup_count = followup_count.reindex(last_status['ID_Customer'])
        followup_df = pd.DataFrame({
            'Followup_Count': followup_count,
            'Status_Kontrak': last_status['Status_Kontrak'].values
        })
        mean_deal = followup_df[followup_df['Status_Kontrak'].str.lower() == 'deal']['Followup_Count'].mean()
        mean_lost = followup_df[followup_df['Status_Kontrak'].str.lower() != 'deal']['Followup_Count'].mean()
        st.write(f'Rata-rata follow-up sebelum DEAL: {mean_deal:.2f}')
        st.write(f'Rata-rata follow-up sebelum LOST: {mean_lost:.2f}')
        fig7, ax7 = plt.subplots(figsize=(7,3))
        ax7.hist(followup_df[followup_df['Status_Kontrak'].str.lower() == 'deal']['Followup_Count'], bins=range(1,10), alpha=0.7, label='Deal')
        ax7.hist(followup_df[followup_df['Status_Kontrak'].str.lower() != 'deal']['Followup_Count'], bins=range(1,10), alpha=0.7, label='Lost')
        ax7.set_xlabel('Jumlah Follow-up')
        ax7.set_ylabel('Jumlah Customer')
        ax7.set_title('Distribusi Jumlah Follow-up: Deal vs Lost')
        ax7.legend()
        st.pyplot(fig7)
        if mean_deal > mean_lost:
            st.success('Customer yang deal cenderung melakukan lebih banyak follow-up.')
        else:
            st.warning('Customer yang deal cenderung melakukan lebih sedikit follow-up.')
    else:
        st.info('Kolom Kunjungan_Ke/ID_Customer tidak tersedia.')
    st.markdown("---")
    st.subheader("Analisis Waktu Respons")
    if 'Kunjungan_Ke' in filtered_df.columns and 'Tanggal' in filtered_df.columns:
        resp_list = []
        for cust, group in filtered_df.groupby('ID_Customer'):
            group = group.sort_values('Tanggal')
            if group['Kunjungan_Ke'].max() > 1:
                t_awal = group[group['Kunjungan_Ke'] == 1]['Tanggal'].min()
                t_fu1 = group[group['Kunjungan_Ke'] == 2]['Tanggal'].min()
                if pd.notnull(t_awal) and pd.notnull(t_fu1):
                    delta = (pd.to_datetime(t_fu1) - pd.to_datetime(t_awal)).days
                    status = group['Status_Kontrak'].iloc[-1]
                    resp_list.append({'ID_Customer': cust, 'Waktu_Respons': delta, 'Status_Kontrak': status})
        resp_df = pd.DataFrame(resp_list)
        mean_resp_deal = resp_df[resp_df['Status_Kontrak'].str.lower() == 'deal']['Waktu_Respons'].mean()
        mean_resp_lost = resp_df[resp_df['Status_Kontrak'].str.lower() != 'deal']['Waktu_Respons'].mean()
        st.write(f'Rata-rata waktu respons (hari) sebelum DEAL: {mean_resp_deal:.2f}')
        st.write(f'Rata-rata waktu respons (hari) sebelum LOST: {mean_resp_lost:.2f}')
        fig8, ax8 = plt.subplots(figsize=(7,3))
        ax8.hist(resp_df[resp_df['Status_Kontrak'].str.lower() == 'deal']['Waktu_Respons'], bins=range(0,31), alpha=0.7, label='Deal')
        ax8.hist(resp_df[resp_df['Status_Kontrak'].str.lower() != 'deal']['Waktu_Respons'], bins=range(0,31), alpha=0.7, label='Lost')
        ax8.set_xlabel('Waktu Respons (hari)')
        ax8.set_ylabel('Jumlah Customer')
        ax8.set_title('Distribusi Waktu Respons: Deal vs Lost')
        ax8.legend()
        st.pyplot(fig8)
        if mean_resp_deal < mean_resp_lost:
            st.success('Customer yang deal cenderung mendapat respons lebih cepat.')
        else:
            st.warning('Customer yang deal cenderung mendapat respons lebih lambat.')
    else:
        st.info('Kolom Kunjungan_Ke/Tanggal tidak tersedia.')
    st.markdown("---")
    st.subheader("Perbandingan Sales Baru vs Senior")
    if 'Level_Sales' in filtered_df.columns:
        conv_by_level = filtered_df.groupby('Level_Sales').apply(lambda x: (x['Status_Kontrak'].str.lower() == 'deal').mean()).sort_values(ascending=False)
        target_by_level = filtered_df.groupby('Level_Sales').apply(lambda x: (x[x['Status_Kontrak'].str.lower() == 'deal']['Nilai_Kontrak'].sum() / x['Target_Sales'].sum()) if x['Target_Sales'].sum() > 0 else 0)
        fig9, ax9 = plt.subplots(figsize=(7,3))
        conv_by_level.plot(kind='bar', color='#58D68D', edgecolor='black', ax=ax9)
        ax9.set_ylabel('Conversion Rate')
        ax9.set_title('Conversion Rate per Level Sales')
        ax9.set_xticklabels(ax9.get_xticklabels(), rotation=0)
        st.pyplot(fig9)
        fig10, ax10 = plt.subplots(figsize=(7,3))
        target_by_level.plot(kind='bar', color='#5DADE2', edgecolor='black', ax=ax10)
        ax10.set_ylabel('Rasio Ketercapaian Target')
        ax10.set_title('Ketercapaian Target per Level Sales')
        ax10.set_xticklabels(ax10.get_xticklabels(), rotation=0)
        st.pyplot(fig10)
        st.success(f'Level sales dengan conversion rate tertinggi: {conv_by_level.idxmax()}')
        st.success(f'Level sales dengan ketercapaian target tertinggi: {target_by_level.idxmax()}')
    else:
        st.info('Kolom Level_Sales tidak tersedia.')

with tab6:
    st.subheader("Insight Otomatis & Rekomendasi")
    st.info("""
    - Sales dengan aktivitas rendah cenderung tidak capai target.
    - Tahap tertentu (misal: Presentasi atau Negosiasi) menjadi bottleneck, banyak customer berhenti di sana.
    - Durasi lama di tahap tertentu menandakan perlunya perbaikan proses/follow-up.
    - Heatmap menunjukkan pola kegagalan spesifik per sales dan tahap.
    - Conversion rate dan pipeline value dapat digunakan untuk menentukan prioritas follow-up.
    - Analisis lost reason membantu perbaikan proses sales.
    - Customer yang deal cenderung melakukan lebih banyak follow-up dan mendapat respons lebih cepat.
    - Level sales senior cenderung memiliki conversion rate dan ketercapaian target lebih tinggi.
    """)
    st.download_button("Download Data Filtered", filtered_df.to_csv(index=False), "filtered_data.csv")
    st.caption("© 2025 Tim Data Analytics")
