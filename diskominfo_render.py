import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import datetime
import json

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Visualisasi Data Statistik Garut", layout="wide")

# --- Fungsi untuk mengambil data dari API dengan caching ---
@st.cache_data(ttl=3600)
def get_data_from_api(api_url):
    """
    Mengambil data JSON dari URL API yang diberikan dan menerapkan caching.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error saat mengambil data dari API: {e}")
        return None

# --- URL API untuk setiap dataset ---
API_URLS = {
    "Agama": "https://satudata-api.garutkab.go.id/api/datasets/jumlah-penduduk-kabupaten-garut-berdasarkan-agama-4203/",
    "Pekerjaan": "https://satudata-api.garutkab.go.id/api/datasets/jumlah-penduduk-kabupaten-garut-berdasarkan-pekerjaan-4095/",
    "Perkawinan": "https://satudata-api.garutkab.go.id/api/datasets/jumlah-penduduk-kabupaten-garut-berdasarkan-status-kawin-4203/",
    "Golongan Darah": "https://satudata-api.garutkab.go.id/api/datasets/jumlah-penduduk-kabupaten-garut-berdasarkan-golongan-darah-4167/",
}

# --- Bagian Utama Aplikasi ---
st.title("Visualisasi Data Penduduk Kabupaten Garut")
st.markdown("Data bersumber dari [Garut Satu Data](https://satudata-api.garutkab.go.id)")

# --- Mengambil semua data sekaligus ---
data_aggr = {}
fetch_success = True
for name, url in API_URLS.items():
    raw_api_response = get_data_from_api(url)
    if raw_api_response and 'data' in raw_api_response and 'pivot_data' in raw_api_response['data'] and isinstance(raw_api_response['data']['pivot_data'], list):
        df_raw = pd.DataFrame(raw_api_response['data']['pivot_data'])
        data_aggr[name] = df_raw
    else:
        st.error(f"Gagal mengambil data untuk: {name}. Pastikan URL API benar dan data tersedia.")
        fetch_success = False

if not fetch_success:
    st.stop()

st.write(f"Data diperbarui terakhir pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.success("Data berhasil diambil dari API.")

# Buat tab untuk setiap jenis visualisasi
tabs_list = ["Berdasarkan Agama", "Berdasarkan Kecamatan & Jenis Kelamin", "Berdasarkan Perkawinan", "Berdasarkan Pekerjaan", "Berdasarkan Golongan Darah"]
tabs = st.tabs(tabs_list)

# --- Konten Tab ---
# Tab: Berdasarkan Agama
with tabs[0]:
    st.markdown("### Jumlah Penduduk Berdasarkan Agama")
    df_agama = data_aggr.get("Agama")
    if df_agama is not None:
        try:
            required_cols = ['tahun', 'agama', 'jumlah', 'jenis_kelamin']
            if not all(col in df_agama.columns.tolist() for col in required_cols):
                st.error("Kolom yang dibutuhkan untuk visualisasi Agama tidak ditemukan.")
            else:
                df_agama = df_agama.dropna(subset=required_cols)
                df_agama['tahun'] = df_agama['tahun'].astype(int)
                df_agama['jumlah'] = pd.to_numeric(df_agama['jumlah'])

                list_tahun = sorted(df_agama['tahun'].unique(), reverse=True)
                selected_tahun = st.selectbox("Pilih Tahun:", list_tahun, key='tahun_agama')
                df_filtered_agama = df_agama[df_agama['tahun'] == selected_tahun]

                if not df_filtered_agama.empty:
                    # Ringkasan baru: Jumlah penduduk per agama
                    st.markdown("#### Jumlah Penduduk per Agama")
                    df_sum_agama = df_filtered_agama.groupby('agama')['jumlah'].sum().reset_index()
                    for index, row in df_sum_agama.iterrows():
                        st.write(f"- Agama {row['agama']}: {row['jumlah']:,.0f} jiwa")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_bar_agama = px.bar(df_sum_agama, x='agama', y='jumlah', title=f'Jumlah Penduduk per Agama Tahun {selected_tahun}', labels={'agama': 'Agama', 'jumlah': 'Jumlah Penduduk (jiwa)'}, color='agama')
                        fig_bar_agama.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_tickformat=".2s")
                        st.plotly_chart(fig_bar_agama, use_container_width=True)
                    with col2:
                        fig_pie_agama = px.pie(df_sum_agama, values='jumlah', names='agama', title=f'Proporsi Penduduk Berdasarkan Agama Tahun {selected_tahun}', labels={'agama': 'Agama', 'jumlah': 'Jumlah Penduduk (jiwa)'})
                        fig_pie_agama.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie_agama, use_container_width=True)

                    st.markdown("---")
                    st.markdown("### Tren Jumlah Penduduk Berdasarkan Agama dari Tahun ke Tahun")
                    df_grouped_agama = df_agama.groupby(['tahun', 'agama']).agg({'jumlah': 'sum'}).reset_index()
                    fig_line_agama = px.line(df_grouped_agama, x='tahun', y='jumlah', color='agama', markers=True, title='Tren Jumlah Penduduk Berdasarkan Agama', labels={'tahun': 'Tahun', 'jumlah': 'Jumlah Penduduk (jiwa)', 'agama': 'Agama'})
                    fig_line_agama.update_layout(hovermode="x unified", yaxis_tickformat=".2s")
                    st.plotly_chart(fig_line_agama, use_container_width=True)
                else:
                    st.info("Tidak ada data yang tersedia untuk tahun yang dipilih.")
        except Exception as e:
            st.error(f"Error saat memproses data Agama: {e}")
    else:
        st.info("Data untuk visualisasi Agama tidak tersedia.")

# ---
# Tab: Berdasarkan Kecamatan & Jenis Kelamin
with tabs[1]:
    st.markdown("### Jumlah Penduduk Berdasarkan Kecamatan dan Jenis Kelamin")
    
    df_kecamatan_jk = None
    if data_aggr.get("Agama") is not None and not data_aggr["Agama"].empty:
        df_kecamatan_jk = data_aggr["Agama"]
    elif data_aggr.get("Perkawinan") is not None and not data_aggr["Perkawinan"].empty:
        df_kecamatan_jk = data_aggr["Perkawinan"]
    elif data_aggr.get("Golongan Darah") is not None and not data_aggr["Golongan Darah"].empty:
        df_kecamatan_jk = data_aggr["Golongan Darah"]

    if df_kecamatan_jk is not None:
        try:
            kecamatan_col = 'nama_kecamatan' if 'nama_kecamatan' in df_kecamatan_jk.columns else 'kecamatan'
            required_cols = ['tahun', kecamatan_col, 'jumlah', 'jenis_kelamin']
            
            if not all(col in df_kecamatan_jk.columns.tolist() for col in required_cols):
                st.error("Kolom yang dibutuhkan untuk visualisasi Kecamatan & Jenis Kelamin tidak ditemukan.")
            else:
                df_kecamatan_jk = df_kecamatan_jk.dropna(subset=required_cols)
                df_kecamatan_jk['tahun'] = df_kecamatan_jk['tahun'].astype(int)
                df_kecamatan_jk['jumlah'] = pd.to_numeric(df_kecamatan_jk['jumlah'])

                list_tahun = sorted(df_kecamatan_jk['tahun'].unique(), reverse=True)
                selected_tahun = st.selectbox("Pilih Tahun:", list_tahun, key='tahun_kecamatan_jk')
                df_filtered_kecamatan_jk = df_kecamatan_jk[df_kecamatan_jk['tahun'] == selected_tahun]
                
                if not df_filtered_kecamatan_jk.empty:
                    # Tampilkan total populasi laki-laki dan perempuan dalam bentuk teks
                    st.markdown("#### Total Jumlah Penduduk Berdasarkan Jenis Kelamin")
                    df_total_jk = df_filtered_kecamatan_jk.groupby('jenis_kelamin')['jumlah'].sum().reset_index()
                    for index, row in df_total_jk.iterrows():
                        st.write(f"- {row['jenis_kelamin']}: {row['jumlah']:,.0f} jiwa")
                    st.write(f"**Total Keseluruhan:** {df_total_jk['jumlah'].sum():,.0f} jiwa")
                    st.markdown("---")
                    
                    # Ringkasan baru: Jumlah penduduk per kecamatan
                    st.markdown("#### Jumlah Penduduk per Kecamatan")
                    df_sum_kecamatan = df_filtered_kecamatan_jk.groupby(kecamatan_col)['jumlah'].sum().reset_index()
                    for index, row in df_sum_kecamatan.iterrows():
                        st.write(f"- Kecamatan {row[kecamatan_col]}: {row['jumlah']:,.0f} jiwa")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        df_bar_kecamatan_total = df_filtered_kecamatan_jk.groupby(kecamatan_col)['jumlah'].sum().reset_index()
                        fig_bar_kecamatan_total = px.bar(df_bar_kecamatan_total, x=kecamatan_col, y='jumlah', title=f'Total Jumlah Penduduk per Kecamatan Tahun {selected_tahun}', labels={kecamatan_col: 'Kecamatan', 'jumlah': 'Total Jumlah Penduduk (jiwa)'}, color=kecamatan_col)
                        fig_bar_kecamatan_total.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_tickformat=".2s")
                        st.plotly_chart(fig_bar_kecamatan_total, use_container_width=True)
                    with col2:
                        df_stacked_kecamatan_jk = df_filtered_kecamatan_jk.groupby([kecamatan_col, 'jenis_kelamin'])['jumlah'].sum().reset_index()
                        fig_stacked_kecamatan_jk = px.bar(df_stacked_kecamatan_jk, x=kecamatan_col, y='jumlah', color='jenis_kelamin', title=f'Jumlah Penduduk per Kecamatan Berdasarkan Jenis Kelamin Tahun {selected_tahun}', labels={kecamatan_col: 'Kecamatan', 'jumlah': 'Jumlah Penduduk (jiwa)', 'jenis_kelamin': 'Jenis Kelamin'}, barmode='group')
                        fig_stacked_kecamatan_jk.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_tickformat=".2s")
                        st.plotly_chart(fig_stacked_kecamatan_jk, use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown("### Tren Total Jumlah Penduduk per Kecamatan dari Tahun ke Tahun")
                    df_grouped_kecamatan_total = df_kecamatan_jk.groupby(['tahun', kecamatan_col]).agg({'jumlah': 'sum'}).reset_index()
                    fig_line_kecamatan_total = px.line(df_grouped_kecamatan_total, x='tahun', y='jumlah', color=kecamatan_col, markers=True, title='Tren Total Jumlah Penduduk per Kecamatan', labels={'tahun': 'Tahun', 'jumlah': 'Total Jumlah Penduduk (jiwa)', kecamatan_col: 'Kecamatan'})
                    fig_line_kecamatan_total.update_layout(hovermode="x unified", yaxis_tickformat=".2s")
                    st.plotly_chart(fig_line_kecamatan_total, use_container_width=True)
                else:
                    st.info("Tidak ada data yang tersedia untuk tahun yang dipilih.")
        except Exception as e:
            st.error(f"Error saat memproses data Kecamatan & Jenis Kelamin: {e}")
    else:
        st.info("Data untuk visualisasi Kecamatan & Jenis Kelamin tidak tersedia.")

# ---
# Tab: Berdasarkan Perkawinan
with tabs[2]:
    st.markdown("### Jumlah Penduduk Berdasarkan Status Perkawinan")
    df_kawin = data_aggr.get("Perkawinan")
    if df_kawin is not None:
        try:
            required_cols = ['tahun', 'status_kawin', 'jumlah', 'jenis_kelamin']
            if not all(col in df_kawin.columns.tolist() for col in required_cols):
                st.error("Kolom yang dibutuhkan untuk visualisasi Status Perkawinan tidak ditemukan.")
            else:
                df_kawin = df_kawin.dropna(subset=required_cols)
                df_kawin['tahun'] = df_kawin['tahun'].astype(int)
                df_kawin['jumlah'] = pd.to_numeric(df_kawin['jumlah'])

                list_tahun = sorted(df_kawin['tahun'].unique(), reverse=True)
                selected_tahun = st.selectbox("Pilih Tahun:", list_tahun, key='tahun_kawin')
                df_filtered_kawin = df_kawin[df_kawin['tahun'] == selected_tahun]

                if not df_filtered_kawin.empty:
                    # Ringkasan baru: Jumlah penduduk per status perkawinan
                    st.markdown("#### Jumlah Penduduk Berdasarkan Status Perkawinan")
                    df_sum_kawin = df_filtered_kawin.groupby('status_kawin')['jumlah'].sum().reset_index()
                    for index, row in df_sum_kawin.iterrows():
                        st.write(f"- {row['status_kawin']}: {row['jumlah']:,.0f} jiwa")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_bar_status_kawin = px.bar(df_sum_kawin, x='status_kawin', y='jumlah', title=f'Jumlah Penduduk per Status Perkawinan Tahun {selected_tahun}', labels={'status_kawin': 'Status Perkawinan', 'jumlah': 'Jumlah Penduduk (jiwa)'}, color='status_kawin')
                        fig_bar_status_kawin.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_tickformat=".2s")
                        st.plotly_chart(fig_bar_status_kawin, use_container_width=True)
                    with col2:
                        fig_pie_status_kawin = px.pie(df_sum_kawin, values='jumlah', names='status_kawin', title=f'Proporsi Penduduk Berdasarkan Status Perkawinan Tahun {selected_tahun}', labels={'status_kawin': 'Status Perkawinan', 'jumlah': 'Jumlah Penduduk (jiwa)'})
                        fig_pie_status_kawin.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie_status_kawin, use_container_width=True)

                    st.markdown("---")
                    st.markdown("### Tren Jumlah Penduduk Berdasarkan Status Perkawinan dari Tahun ke Tahun")
                    df_grouped_status_kawin = df_kawin.groupby(['tahun', 'status_kawin']).agg({'jumlah': 'sum'}).reset_index()
                    fig_line_status_kawin = px.line(df_grouped_status_kawin, x='tahun', y='jumlah', color='status_kawin', markers=True, title='Tren Jumlah Penduduk Berdasarkan Status Perkawinan', labels={'tahun': 'Tahun', 'jumlah': 'Jumlah Penduduk (jiwa)', 'status_kawin': 'Status Perkawinan'})
                    fig_line_status_kawin.update_layout(hovermode="x unified", yaxis_tickformat=".2s")
                    st.plotly_chart(fig_line_status_kawin, use_container_width=True)
                else:
                    st.info("Tidak ada data yang tersedia untuk tahun yang dipilih.")
        except Exception as e:
            st.error(f"Error saat memproses data Status Perkawinan: {e}")
    else:
        st.info("Data untuk visualisasi Status Perkawinan tidak tersedia.")

# ---
# Tab: Berdasarkan Pekerjaan
with tabs[3]:
    st.markdown("### Jumlah Penduduk Berdasarkan Pekerjaan")
    df_pekerjaan = data_aggr.get("Pekerjaan")
    if df_pekerjaan is not None:
        try:
            required_cols = ['tahun', 'jenis_pekerjaan', 'jumlah']
            if 'jenis_kelamin' in df_pekerjaan.columns.tolist():
                required_cols.append('jenis_kelamin')
            
            if not all(col in df_pekerjaan.columns.tolist() for col in required_cols):
                st.error("Kolom yang dibutuhkan untuk visualisasi Pekerjaan tidak ditemukan.")
            else:
                df_pekerjaan = df_pekerjaan.dropna(subset=required_cols)
                df_pekerjaan['tahun'] = df_pekerjaan['tahun'].astype(int)
                df_pekerjaan['jumlah'] = pd.to_numeric(df_pekerjaan['jumlah'])

                list_tahun = sorted(df_pekerjaan['tahun'].unique(), reverse=True)
                selected_tahun = st.selectbox("Pilih Tahun:", list_tahun, key='tahun_pekerjaan')
                df_filtered_pekerjaan = df_pekerjaan[df_pekerjaan['tahun'] == selected_tahun]

                if not df_filtered_pekerjaan.empty:
                    if 'jenis_kelamin' in df_filtered_pekerjaan.columns.tolist():
                         st.info("Visualisasi total penduduk berdasarkan jenis kelamin tidak tersedia untuk dataset ini.")

                    # Ringkasan baru: Jumlah penduduk per pekerjaan
                    st.markdown("#### Jumlah Penduduk Berdasarkan Pekerjaan")
                    df_sum_pekerjaan = df_filtered_pekerjaan.groupby('jenis_pekerjaan')['jumlah'].sum().reset_index()
                    for index, row in df_sum_pekerjaan.iterrows():
                        st.write(f"- {row['jenis_pekerjaan']}: {row['jumlah']:,.0f} jiwa")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_bar_pekerjaan = px.bar(df_sum_pekerjaan, x='jenis_pekerjaan', y='jumlah', title=f'Jumlah Penduduk per Pekerjaan Tahun {selected_tahun}', labels={'jenis_pekerjaan': 'Pekerjaan', 'jumlah': 'Jumlah Penduduk (jiwa)'}, color='jenis_pekerjaan')
                        fig_bar_pekerjaan.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_tickformat=".2s")
                        st.plotly_chart(fig_bar_pekerjaan, use_container_width=True)
                    with col2:
                        fig_pie_pekerjaan = px.pie(df_sum_pekerjaan, values='jumlah', names='jenis_pekerjaan', title=f'Proporsi Penduduk Berdasarkan Pekerjaan Tahun {selected_tahun}', labels={'jenis_pekerjaan': 'Pekerjaan', 'jumlah': 'Jumlah Penduduk (jiwa)'})
                        fig_pie_pekerjaan.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie_pekerjaan, use_container_width=True)

                    st.markdown("---")
                    st.markdown("### Tren Jumlah Penduduk Berdasarkan Pekerjaan dari Tahun ke Tahun")
                    df_grouped_pekerjaan = df_pekerjaan.groupby(['tahun', 'jenis_pekerjaan']).agg({'jumlah': 'sum'}).reset_index()
                    fig_line_pekerjaan = px.line(df_grouped_pekerjaan, x='tahun', y='jumlah', color='jenis_pekerjaan', markers=True, title='Tren Jumlah Penduduk Berdasarkan Pekerjaan', labels={'tahun': 'Tahun', 'jumlah': 'Jumlah Penduduk (jiwa)', 'jenis_pekerjaan': 'Pekerjaan'})
                    fig_line_pekerjaan.update_layout(hovermode="x unified", yaxis_tickformat=".2s")
                    st.plotly_chart(fig_line_pekerjaan, use_container_width=True)
                else:
                    st.info("Tidak ada data yang tersedia untuk tahun yang dipilih.")
        except Exception as e:
            st.error(f"Error saat memproses data Pekerjaan: {e}")
    else:
        st.info("Data untuk visualisasi Pekerjaan tidak tersedia.")

# ---
# Tab: Berdasarkan Golongan Darah
with tabs[4]:
    st.markdown("### Jumlah Penduduk Berdasarkan Golongan Darah")
    df_goldarah = data_aggr.get("Golongan Darah")
    if df_goldarah is not None:
        try:
            required_cols = ['tahun', 'gol_drh', 'jumlah', 'jenis_kelamin']
            if not all(col in df_goldarah.columns.tolist() for col in required_cols):
                st.error("Kolom yang dibutuhkan untuk visualisasi Golongan Darah tidak ditemukan.")
            else:
                df_goldarah = df_goldarah.dropna(subset=required_cols)
                df_goldarah['tahun'] = df_goldarah['tahun'].astype(int)
                df_goldarah['jumlah'] = pd.to_numeric(df_goldarah['jumlah'])

                list_tahun = sorted(df_goldarah['tahun'].unique(), reverse=True)
                selected_tahun = st.selectbox("Pilih Tahun:", list_tahun, key='tahun_goldarah')
                df_filtered_goldarah = df_goldarah[df_goldarah['tahun'] == selected_tahun]

                if not df_filtered_goldarah.empty:
                    # Ringkasan baru: Jumlah penduduk per golongan darah
                    st.markdown("#### Jumlah Penduduk Berdasarkan Golongan Darah")
                    df_sum_goldarah = df_filtered_goldarah.groupby('gol_drh')['jumlah'].sum().reset_index()
                    for index, row in df_sum_goldarah.iterrows():
                        st.write(f"- Golongan Darah {row['gol_drh']}: {row['jumlah']:,.0f} jiwa")
                    st.markdown("---")

                    col1, col2 = st.columns(2)
                    with col1:
                        fig_bar_gol_darah = px.bar(df_sum_goldarah, x='gol_drh', y='jumlah', title=f'Jumlah Penduduk per Golongan Darah Tahun {selected_tahun}', labels={'gol_drh': 'Golongan Darah', 'jumlah': 'Jumlah Penduduk (jiwa)'}, color='gol_drh')
                        fig_bar_gol_darah.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_tickformat=".2s")
                        st.plotly_chart(fig_bar_gol_darah, use_container_width=True)
                    with col2:
                        fig_pie_gol_darah = px.pie(df_sum_goldarah, values='jumlah', names='gol_drh', title=f'Proporsi Penduduk Berdasarkan Golongan Darah Tahun {selected_tahun}', labels={'gol_drh': 'Golongan Darah', 'jumlah': 'Jumlah Penduduk (jiwa)'})
                        fig_pie_gol_darah.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie_gol_darah, use_container_width=True)

                    st.markdown("---")
                    st.markdown("### Tren Jumlah Penduduk Berdasarkan Golongan Darah dari Tahun ke Tahun")
                    df_grouped_gol_darah = df_goldarah.groupby(['tahun', 'gol_drh']).agg({'jumlah': 'sum'}).reset_index()
                    fig_line_gol_darah = px.line(df_grouped_gol_darah, x='tahun', y='jumlah', color='gol_drh', markers=True, title='Tren Jumlah Penduduk Berdasarkan Golongan Darah', labels={'tahun': 'Tahun', 'jumlah': 'Jumlah Penduduk (jiwa)', 'gol_drh': 'Golongan Darah'})
                    fig_line_gol_darah.update_layout(hovermode="x unified", yaxis_tickformat=".2s")
                    st.plotly_chart(fig_line_gol_darah, use_container_width=True)
                else:
                    st.info("Tidak ada data yang tersedia untuk tahun yang dipilih.")
        except Exception as e:
            st.error(f"Error saat memproses data Golongan Darah: {e}")
    else:
        st.info("Data untuk visualisasi Golongan Darah tidak tersedia.")