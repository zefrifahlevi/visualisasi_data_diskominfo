import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import datetime
import json # Import json for potential debugging display

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Visualisasi Data Statistik Garut", layout="wide")

# --- Fungsi untuk mengambil data dari API dengan caching ---
@st.cache_data(ttl=3600)  # Cache data selama 1 jam (misalnya 1 jam)
def get_data_from_api(api_url):
    """
    Mengambil data JSON dari URL API yang diberikan dan menerapkan caching.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Akan memunculkan HTTPError untuk respons status kode yang buruk (4xx atau 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error saat mengambil data dari API: {e}")
        return None

# --- Bagian Utama Aplikasi ---
st.title("Visualisasi Data Penduduk Kabupaten Garut Berdasarkan Pekerjaan & Kecamatan")
st.markdown("Data bersumber dari [Garut Satu Data](https://satudata-api.garutkab.go.id)")

# URL API yang akan digunakan (sudah diperbarui untuk data pekerjaan)
API_URL = "https://satudata-api.garutkab.go.id/api/datasets/jumlah-penduduk-kabupaten-garut-berdasarkan-pekerjaan-4095/"
raw_api_response = get_data_from_api(API_URL)

if raw_api_response:
    st.write(f"Data diperbarui terakhir pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # PENTING: Mengambil data dari kunci 'data.pivot_data'
        if 'data' in raw_api_response and 'pivot_data' in raw_api_response['data'] and \
           isinstance(raw_api_response['data']['pivot_data'], list):
            df_raw = pd.DataFrame(raw_api_response['data']['pivot_data'])
            st.success("Data berhasil diambil dari kunci 'data.pivot_data'.")
        else:
            st.error("Struktur data API tidak seperti yang diharapkan. Pastikan ada kunci 'data.pivot_data' yang berisi list.")
            st.info("Berikut adalah respons API mentah untuk membantu debugging:")
            st.json(raw_api_response) # Tampilkan respons API mentah untuk debugging
            st.stop()  # Hentikan eksekusi jika data tidak dapat diproses

        # --- Memastikan Kolom yang Dibutuhkan Ada ---
        # Kolom yang dibutuhkan untuk visualisasi pekerjaan DAN kecamatan
        # 'jenis_kelamin' tidak tersedia di API ini, jadi dihapus dari required_cols
        required_cols_pekerjaan = ['tahun', 'jenis_pekerjaan', 'jumlah']
        required_cols_kecamatan = ['tahun', 'kecamatan', 'jumlah'] # Hanya kecamatan dan jumlah
        
        # Gabungkan semua kolom yang dibutuhkan
        all_required_cols = list(set(required_cols_pekerjaan + required_cols_kecamatan))

        existing_cols = df_raw.columns.tolist()

        missing_cols = [col for col in all_required_cols if col not in existing_cols]
        if missing_cols:
            st.error(f"Kolom yang dibutuhkan tidak ditemukan: {', '.join(missing_cols)}")
            st.warning(f"Kolom yang tersedia dalam data: {', '.join(existing_cols)}")
            st.info("Silakan periksa kembali struktur 'pivot_data' di API atau sesuaikan nama kolom di script.")
            st.stop() # Hentikan eksekusi jika kolom tidak lengkap

        # Drop baris dengan nilai NaN pada kolom kunci dan ubah tipe data
        df_raw = df_raw.dropna(subset=all_required_cols)
        df_raw['tahun'] = df_raw['tahun'].astype(int)
        df_raw['jumlah'] = pd.to_numeric(df_raw['jumlah']) # Pastikan kolom 'jumlah' adalah numerik

        with st.expander("Lihat Data Mentah yang Sudah Diproses"):
            st.dataframe(df_raw)

        # Buat dropdown untuk memilih tahun
        list_tahun = sorted(df_raw['tahun'].unique(), reverse=True)
        selected_tahun = st.selectbox("Pilih Tahun:", list_tahun)
        df_filtered = df_raw[df_raw['tahun'] == selected_tahun]

        # --- Tab untuk Visualisasi ---
        if not df_filtered.empty:
            tab1, tab2 = st.tabs(["Berdasarkan Pekerjaan", "Berdasarkan Kecamatan"]) # Nama tab disesuaikan

            with tab1:
                st.markdown(f"### Jumlah Penduduk Berdasarkan Pekerjaan Tahun {selected_tahun}")

                # Buat dua kolom untuk Bar Chart dan Pie Chart
                col1_tab1, col2_tab1 = st.columns(2)

                with col1_tab1:
                    # Visualisasi Bar Chart Pekerjaan
                    df_bar_pekerjaan_data = df_filtered.groupby('jenis_pekerjaan')['jumlah'].sum().reset_index()
                    fig_bar_pekerjaan = px.bar(
                        df_bar_pekerjaan_data,
                        x='jenis_pekerjaan',
                        y='jumlah',
                        title=f'Jumlah Penduduk per Pekerjaan',
                        labels={'jenis_pekerjaan': 'Pekerjaan', 'jumlah': 'Jumlah Penduduk'},
                        color='jenis_pekerjaan'
                    )
                    fig_bar_pekerjaan.update_layout(
                        xaxis={'categoryorder':'total descending'},
                        yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                    )
                    st.plotly_chart(fig_bar_pekerjaan, use_container_width=True)

                with col2_tab1:
                    # Visualisasi Pie Chart Pekerjaan
                    # st.markdown(f"### Proporsi Penduduk Berdasarkan Pekerjaan") # Judul lebih singkat karena di kolom
                    fig_pie_pekerjaan = px.pie(
                        df_bar_pekerjaan_data, # Menggunakan data yang sudah diagregasi dari bar chart
                        values='jumlah',
                        names='jenis_pekerjaan',
                        title=f'Proporsi Penduduk Berdasarkan Pekerjaan Tahun {selected_tahun}',
                        labels={'jenis_pekerjaan': 'Pekerjaan', 'jumlah': 'Jumlah Penduduk'}
                    )
                    fig_pie_pekerjaan.update_traces(textposition='inside', textinfo='percent+label') # Menampilkan persentase dan label di dalam pie
                    st.plotly_chart(fig_pie_pekerjaan, use_container_width=True)

                st.markdown("---") # Garis pemisah setelah kolom

                # Visualisasi Line Chart Pekerjaan (tetap full width)
                st.markdown("### Tren Jumlah Penduduk Berdasarkan Pekerjaan dari Tahun ke Tahun")
                df_grouped_pekerjaan = df_raw.groupby(['tahun', 'jenis_pekerjaan']).agg({'jumlah': 'sum'}).reset_index()
                fig_line_pekerjaan = px.line(
                    df_grouped_pekerjaan,
                    x='tahun',
                    y='jumlah',
                    color='jenis_pekerjaan',
                    markers=True,
                    title='Tren Jumlah Penduduk Berdasarkan Pekerjaan',
                    labels={'tahun': 'Tahun', 'jumlah': 'Jumlah Penduduk', 'jenis_pekerjaan': 'Pekerjaan'}
                )
                fig_line_pekerjaan.update_layout(
                    hovermode="x unified",
                    yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                )
                st.plotly_chart(fig_line_pekerjaan, use_container_width=True)

            with tab2:
                st.markdown(f"### Jumlah Penduduk Berdasarkan Kecamatan Tahun {selected_tahun}") # Judul disesuaikan

                # Visualisasi Bar Chart Jumlah Penduduk per Kecamatan (Total)
                # Menggunakan kolom 'kecamatan'
                df_bar_kecamatan_total = df_filtered.groupby('kecamatan')['jumlah'].sum().reset_index()
                fig_bar_kecamatan_total = px.bar(
                    df_bar_kecamatan_total,
                    x='kecamatan',
                    y='jumlah',
                    title=f'Total Jumlah Penduduk per Kecamatan',
                    labels={'kecamatan': 'Kecamatan', 'jumlah': 'Total Jumlah Penduduk'},
                    color='kecamatan'
                )
                fig_bar_kecamatan_total.update_layout(
                    xaxis={'categoryorder':'total descending'},
                    yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                )
                st.plotly_chart(fig_bar_kecamatan_total, use_container_width=True)

                st.markdown("---") # Garis pemisah

                # Visualisasi Line Chart Tren Jumlah Penduduk per Kecamatan dari Tahun ke Tahun
                st.markdown("### Tren Total Jumlah Penduduk per Kecamatan dari Tahun ke Tahun")
                # Menggunakan kolom 'kecamatan'
                df_grouped_kecamatan_total = df_raw.groupby(['tahun', 'kecamatan']).agg({'jumlah': 'sum'}).reset_index()
                fig_line_kecamatan_total = px.line(
                    df_grouped_kecamatan_total,
                    x='tahun',
                    y='jumlah',
                    color='kecamatan',
                    markers=True,
                    title='Tren Total Jumlah Penduduk per Kecamatan',
                    labels={'tahun': 'Tahun', 'jumlah': 'Total Jumlah Penduduk', 'kecamatan': 'Kecamatan'}
                )
                fig_line_kecamatan_total.update_layout(
                    hovermode="x unified",
                    yaxis_tickformat=".2s" # Format angka menjadi SI-prefix (e.g., 10K, 1M)
                )
                st.plotly_chart(fig_line_kecamatan_total, use_container_width=True)

                # Menghapus stacked bar chart karena tidak ada kolom 'jenis_kelamin'
                st.info("Visualisasi berdasarkan jenis kelamin tidak tersedia untuk dataset ini karena kolom 'jenis_kelamin' tidak ditemukan.")

        else:
            st.info("Tidak ada data yang tersedia untuk tahun yang dipilih.")

    except (KeyError, TypeError, ValueError) as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
        st.info("Berikut adalah respons API mentah untuk membantu debugging:")
        st.json(raw_api_response)
else:
    st.info("Gagal mengambil data dari API. Pastikan URL API benar dan koneksi internet stabil.")
    