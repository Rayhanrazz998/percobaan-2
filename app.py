import streamlit as st
import pandas as pd
import json
import os
import io  # <--- ini penting ditambahkan
from datetime import datetime
from fpdf import FPDF  # kalau kamu ingin buat PDF



# ---------- Fungsi Pengelolaan User ----------
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open("users.json", "w") as f:
        json.dump(users, f)


# ---------- Fungsi Registrasi ----------
def register():
    st.image("images/logo.png", width=100)
    st.title("Registrasi Akun Kasir Sayur Sawi")

    username = st.text_input("Username Baru")
    password = st.text_input("Password Baru", type="password")
    confirm_password = st.text_input("Konfirmasi Password", type="password")

    if st.button("Daftar"):
        if not username or not password or not confirm_password:
            st.error("Semua kolom harus diisi.")
        elif password != confirm_password:
            st.error("Password dan konfirmasi tidak cocok.")
        else:
            users = load_users()
            if username in users:
                st.error("Username sudah terdaftar.")
            else:
                save_user(username, password)
                st.success("Registrasi berhasil! Silakan login.")
                st.session_state.page = "login"
                st.rerun()

# ---------- Fungsi Login ----------
def login():
    st.image("images/logo.png", width=100)
    st.title("Login Kasir Sayur Sawi")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()
        if username in users and users[username] == password:
            st.success("Login berhasil!")
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Username atau password salah.")

    if st.button("Daftar Akun Baru"):
        st.session_state.page = "register"
        st.rerun()

# Tambahkan fungsi ini di atas halaman_kasir()
def get_nomor_nota():
    nota_path = "data/nomor_nota.json"
    today = datetime.now().strftime("%d%m%y")

    if not os.path.exists(nota_path):
        nomor = 1
    else:
        with open(nota_path, "r") as f:
            data = json.load(f)
        if data.get("tanggal") == today:
            nomor = data.get("nomor", 0) + 1
        else:
            nomor = 1

    with open(nota_path, "w") as f:
        json.dump({"tanggal": today, "nomor": nomor}, f)

    return f"CS/{today}/{str(nomor).zfill(4)}"

# ---------- Fungsi Kasir ----------
def halaman_kasir():
    st.subheader("🛒 Kasir Sayur Sawi")

    if not os.path.exists("data/produk.csv"):
        os.makedirs("data", exist_ok=True)
        pd.DataFrame(columns=["nama", "harga", "stok", "gambar"]).to_csv("data/produk.csv", index=False)

    df = pd.read_csv("data/produk.csv")
    df = df[df["stok"] > 0]

    if "keranjang" not in st.session_state:
        st.session_state.keranjang = []

    if not df.empty:
        for i, row in df.iterrows():
            col_img, col1, col2, col3 = st.columns([1.5, 3, 2, 1])
            with col_img:
                if pd.notna(row.get("gambar", None)) and os.path.exists(row["gambar"]):
                    st.image(row["gambar"], width=60)
                else:
                    st.empty()

            with col1:
                st.markdown(f"**{row['nama']}**")
                st.caption(f"Rp{row['harga']:,} | Stok: {int(row['stok'])}")

            with col2:
                jumlah = st.number_input(f"Jumlah {row['nama']}", min_value=0, max_value=int(row["stok"]), key=f"jumlah_{i}")

            with col3:
                if st.button("Tambah", key=f"btn_{i}"):
                    if jumlah > 0:
                        st.session_state.keranjang.append((row["nama"], row["harga"], jumlah))
                        st.success(f"{row['nama']} ditambahkan!")
    else:
        st.info("Belum ada produk tersedia atau stok habis.")


    if st.session_state.keranjang:
        st.write("### Keranjang Belanja")
        total = 0
        for nama, harga, qty in st.session_state.keranjang:
            st.write(f"{nama} x {qty} = Rp{harga * qty}")
            total += harga * qty
        st.write(f"### Total: Rp{total}")

    if st.button("🧾 Cetak Struk"):
        df = pd.read_csv("data/produk.csv")
        stok_kurang = False

        for nama, harga, qty in st.session_state.keranjang:
            index = df[df["nama"] == nama].index
            if not index.empty:
                if df.at[index[0], "stok"] >= qty:
                    df.at[index[0], "stok"] -= qty
                else:
                    st.error(f"Stok {nama} tidak cukup!")
                    stok_kurang = True
                    break

        if not stok_kurang:
            df.to_csv("data/produk.csv", index=False)

            now = datetime.now()
            waktu_str = now.strftime("%d %b %y %H:%M")
            nomor_nota = get_nomor_nota()

            total = sum(harga * qty for _, harga, qty in st.session_state.keranjang)

            # Tampilkan di text_area
            struk_lines = []
            struk_lines.append("         Sayur tomat")
            struk_lines.append("=" * 30)
            struk_lines.append(f"No Nota : {nomor_nota}")
            struk_lines.append(f"Waktu   : {waktu_str}")
            struk_lines.append("-" * 30)

            for nama, harga, qty in st.session_state.keranjang:
                total_item = harga * qty
                struk_lines.append(f"{qty} {nama:<20} {total_item:>7,}".replace(",", "."))

            struk_lines.append("-" * 30)
            struk_lines.append(f"Subtotal {len(st.session_state.keranjang)} Produk    {total:>7,}".replace(",", "."))
            struk_lines.append(f"Total Tagihan               {total:>7,}".replace(",", "."))
            struk_lines.append("")
            struk_lines.append("Kartu Debit/Kredit")
            struk_lines.append(f"Total Bayar                 {total:>7,}".replace(",", "."))
            struk_lines.append("=" * 30)
            struk_lines.append(f"Terbayar {waktu_str}")
            struk_lines.append("dicetak: Kasir")

            struk = "\n".join(struk_lines)
            st.text_area("🧾 Struk Transaksi", struk, height=300)
            st.download_button("📥 Unduh Struk TXT", data=struk, file_name="struk_pembelian.txt", mime="text/plain")

            # === Buat versi PDF ===
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Courier", size=10)
            for line in struk_lines:
                pdf.cell(0, 10, txt=line, ln=1)

            pdf_bytes = pdf.output(dest="S").encode("latin-1")
            pdf_buffer = io.BytesIO(pdf_bytes)

            st.download_button("📄 Unduh Struk PDF", data=pdf_buffer, file_name="struk_pembelian.pdf", mime="application/pdf")

            # Simpan riwayat
            riwayat_path = "data/riwayat.csv"
            os.makedirs("data", exist_ok=True)
            if os.path.exists(riwayat_path):
                riwayat_df = pd.read_csv(riwayat_path)
            else:
                riwayat_df = pd.DataFrame(columns=["nama", "harga", "qty", "kasir", "waktu", "nota"])

            for nama, harga, qty in st.session_state.keranjang:
                new_row = pd.DataFrame({
                    "nama": [nama],
                    "harga": [harga],
                    "qty": [qty],
                    "kasir": [st.session_state.username],
                    "waktu": [now],
                    "nota": [nomor_nota]
                })
                riwayat_df = pd.concat([riwayat_df, new_row], ignore_index=True)

            riwayat_df.to_csv(riwayat_path, index=False)

            st.success("Pembelian berhasil!")
            st.session_state.keranjang = []

# ----------- Reset Data Produk -------------
def reset_data():
    if st.sidebar.button("🧹 Reset Data Produk"):
        pd.DataFrame(columns=["nama", "harga", "stok"]).to_csv("data/produk.csv", index=False)
        st.success("Data produk berhasil direset!")

# ---------- Fungsi Tambah Produk ----------
def halaman_tambah_produk():
    st.title("Tambah Produk Baru")

    nama = st.text_input("Nama Produk")
    harga_str = st.text_input("Harga (contoh: 5000)")
    stok = st.number_input("Stok", min_value=0, step=1)
    gambar = st.file_uploader("Gambar Produk", type=["jpg", "jpeg", "png"])

    if st.button("Simpan"):
        try:
            harga = int(harga_str.replace('.', '').replace(',', ''))
        except ValueError:
            st.error("Harga tidak valid. Harap isi angka seperti: 5.000")
            return

        # Simpan gambar
        gambar_path = ""
        if gambar:
            os.makedirs("images/produk", exist_ok=True)
            gambar_path = f"images/produk/{nama.replace(' ', '_')}.png"
            with open(gambar_path, "wb") as f:
                f.write(gambar.read())

        # Cek dan simpan ke CSV
        if not os.path.exists("data/produk.csv"):
            df = pd.DataFrame(columns=["nama", "harga", "stok", "gambar"])
        else:
            df = pd.read_csv("data/produk.csv")
            if "gambar" not in df.columns:
                df["gambar"] = ""

        df.loc[len(df)] = [nama, harga, stok, gambar_path]
        df.to_csv("data/produk.csv", index=False)
        st.success("Produk berhasil ditambahkan!")


# ---------- Fungsi Hapus Produk Satuan ----------
def hapus_produk():
    st.subheader("🗑️ Hapus Produk")

    df = pd.read_csv("data/produk.csv")
    if df.empty:
        st.info("Tidak ada produk yang tersedia.")
        return

    produk_list = df["nama"].tolist()
    produk_dipilih = st.selectbox("Pilih produk yang ingin dihapus:", produk_list)

    if st.button("Hapus Produk"):
        df = df[df["nama"] != produk_dipilih]
        df.to_csv("data/produk.csv", index=False)
        st.success(f"Produk '{produk_dipilih}' berhasil dihapus.")

# ---------- edit Produk -----------

def edit_produk():
    st.subheader("✏️ Edit Produk")

    df = pd.read_csv("data/produk.csv")
    if df.empty:
        st.info("Tidak ada produk untuk diedit.")
        return

    produk_list = df["nama"].tolist()
    produk_dipilih = st.selectbox("Pilih produk yang ingin diedit:", produk_list)

    if produk_dipilih:
        produk_row = df[df["nama"] == produk_dipilih].iloc[0]

        nama_baru = st.text_input("Nama Produk", value=produk_row["nama"])
        harga_str_baru = st.text_input("Harga (misal: 5.000)", value=f"{int(produk_row['harga']):,}".replace(",", "."))
        stok_baru = st.number_input("Stok", min_value=0, value=int(produk_row["stok"]))

        if st.button("Simpan Perubahan"):
            try:
                harga_baru = int(harga_str_baru.replace('.', '').replace(',', ''))
            except ValueError:
                st.error("Harga tidak valid. Harap isi angka seperti: 5.000")
                return

            # Update data
            idx = df[df["nama"] == produk_dipilih].index[0]
            df.at[idx, "nama"] = nama_baru
            df.at[idx, "harga"] = harga_baru
            df.at[idx, "stok"] = stok_baru
            df.to_csv("data/produk.csv", index=False)

            st.success(f"Produk '{produk_dipilih}' berhasil diperbarui!")

# ---------- Fungsi Laporan ----------
def halaman_laporan():
    st.subheader("📊 Laporan Produk")
    df = pd.read_csv("data/produk.csv")
    st.dataframe(df)

    st.subheader("🧾 Riwayat Transaksi")

    riwayat_path = "data/riwayat.csv"
    if not os.path.exists(riwayat_path):
        st.info("Belum ada riwayat transaksi.")
        return

    riwayat_df = pd.read_csv(riwayat_path)
    if riwayat_df.empty:
        st.info("Riwayat transaksi kosong.")
        return



    # Konversi kolom waktu ke datetime
    riwayat_df["waktu"] = pd.to_datetime(riwayat_df["waktu"])

    # Pilihan filter
    filter_jenis = st.radio("Filter berdasarkan:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

    now = pd.Timestamp.now()
    if filter_jenis == "Harian":
        tanggal = st.date_input("Pilih Tanggal", now.date())
        filtered = riwayat_df[riwayat_df["waktu"].dt.date == tanggal]

    elif filter_jenis == "Mingguan":
        minggu_ini = now.isocalendar().week
        tahun_ini = now.year
        filtered = riwayat_df[
            (riwayat_df["waktu"].dt.isocalendar().week == minggu_ini) &
            (riwayat_df["waktu"].dt.year == tahun_ini)
        ]

    elif filter_jenis == "Bulanan":
        bulan = st.selectbox("Pilih Bulan", list(range(1, 13)), index=now.month - 1)
        tahun = st.number_input("Tahun", value=now.year, step=1)
        filtered = riwayat_df[
            (riwayat_df["waktu"].dt.month == bulan) &
            (riwayat_df["waktu"].dt.year == tahun)
        ]

    if filtered.empty:
        st.warning("Tidak ada transaksi untuk periode yang dipilih.")
    else:
        st.dataframe(filtered)

        total_transaksi = (filtered["harga"] * filtered["qty"]).sum()
        jumlah_item = filtered["qty"].sum()
        jumlah_nota = filtered["nota"].nunique()

        st.markdown(f"""
        #### Ringkasan:
        - Total Penjualan: **Rp{int(total_transaksi):,}**
        - Total Item Terjual: **{int(jumlah_item)}**
        - Jumlah Transaksi (Nota): **{jumlah_nota}**
        """.replace(",", "."))

        # Unduh sebagai CSV
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Unduh Laporan CSV", csv, "laporan_transaksi.csv", "text/csv")



# ---------- Fungsi Logout ----------
def logout():
    if st.sidebar.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page = "login"
        st.rerun()

# ---------- MAIN ----------

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.logged_in:
        st.sidebar.image("images/logo.png", width=100)
        st.sidebar.markdown(f"### Halo, {st.session_state.username}")

        menu_options = {
            "Kasir": "🛒 Kasir",
            "Tambah Produk": "➕ Tambah Produk",
            "Edit Produk": "✏️ Edit Produk",
            "Hapus Produk": "🗑️ Hapus Produk",
            "Laporan": "📊 Laporan"
        }

        if 'menu' not in st.session_state:
            st.session_state.menu = "Kasir"

        for key, label in menu_options.items():
            if st.sidebar.button(label):
                st.session_state.menu = key
        logout()
        reset_data()

        if st.session_state.menu == "Kasir":
            halaman_kasir()
        if st.session_state.menu == "Tambah Produk":
            halaman_tambah_produk()
        elif st.session_state.menu == "Edit Produk":
            edit_produk()
        elif st.session_state.menu == "Hapus Produk":
             hapus_produk()
        elif st.session_state.menu == "Laporan":
             halaman_laporan()
    else:
        if st.session_state.page == "login":
            login()
        elif st.session_state.page == "register":
            register()

if __name__ == "__main__":
    main()
