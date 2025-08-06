-----

# Website Visualisasi Data Menggunakan Streamlit

Proyek ini adalah sebuah website interaktif untuk **visualisasi data** yang dibangun menggunakan **Python** dengan framework **Streamlit**. Website ini memungkinkan pengguna untuk melihat atau memuat data, melakukan eksplorasi, dan menghasilkan visualisasi data yang menarik dengan mudah.

## Fitur Utama

  * **Antarmuka Pengguna Sederhana:** Dibuat dengan Streamlit, antarmuka ini sangat intuitif dan mudah digunakan.
  * **Visualisasi Interaktif:** Menghasilkan berbagai jenis grafik dan diagram yang interaktif.
  * **Kompatibel dengan Berbagai Sumber Data:** Mampu memuat data dari file lokal atau sumber data eksternal.

## Instalasi

Untuk menjalankan proyek ini di mesin lokal Anda, ikuti langkah-langkah instalasi di bawah ini.

### Prasyarat

Pastikan Anda sudah menginstal **Python** versi 3.7 atau yang lebih baru.

### Langkah-langkah

1.  **Klon Repositori**

    Pertama, klon repositori ini ke komputer Anda menggunakan Git:

    ```bash
    git clone https://github.com/zefrifahlevi/visualisasi_data_diskominfo.git
    cd visualisasi_data_diskominfo
    ```

2.  **Instal Dependensi**

    Instal semua pustaka (library) yang diperlukan menggunakan `pip`. Berdasarkan skrip Anda, dependensinya adalah:

    ```bash
    pip install streamlit requests pandas plotly-express
    ```

    *(Catatan: `plotly-express` sudah termasuk dalam `plotly`, jadi Anda bisa menginstal `plotly` saja jika diperlukan.)*

    Anda juga bisa membuat file `requirements.txt` terlebih dahulu untuk mempermudah instalasi. Cukup buat file dengan nama tersebut dan isi dengan daftar pustaka:

    `requirements.txt`

    ```
    streamlit
    requests
    pandas
    plotly-express
    ```

    Lalu, instal dengan perintah ini:

    ```bash
    pip install -r requirements.txt
    ```

## Cara Menjalankan Aplikasi

Setelah semua dependensi terinstal, jalankan aplikasi Streamlit dengan perintah berikut:

```bash
streamlit run nama_file_anda.py
```

*Ganti `nama_file_anda.py` dengan nama file Python utama Anda.*

Aplikasi akan berjalan di *browser* Anda secara otomatis pada alamat `http://localhost:8501`.
