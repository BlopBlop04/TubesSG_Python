import datetime
import uuid

# ─── KONFIGURASI ──────────────────────────────────────────────────────────────
KAPASITAS = {"mobil": 5, "motor": 5}
TARIF     = {"mobil": 5000, "motor": 2000}  # per menit

# ─── DATA ─────────────────────────────────────────────────────────────────────
data_parkir  = {}   # kendaraan yang sedang parkir
history_parkir = [] # riwayat semua kendaraan yang sudah keluar

# ─── HELPER ───────────────────────────────────────────────────────────────────
def hitung_slot_terpakai(kategori):
    return sum(1 for v in data_parkir.values() if v["kategori"] == kategori)

def cek_kapasitas(kategori):
    terpakai = hitung_slot_terpakai(kategori)
    return terpakai < KAPASITAS[kategori], terpakai

def format_durasi(menit):
    jam  = menit // 60
    sisa = menit % 60
    if jam > 0:
        return f"{jam} Jam {sisa} Menit"
    return f"{sisa} Menit"

def cetak_separator(char="─", lebar=40):
    print(char * lebar)

# ─── FITUR UTAMA ──────────────────────────────────────────────────────────────
def kendaraan_masuk():
    print("\n" + "="*40)
    print("        KENDARAAN MASUK")
    cetak_separator()

    # Pilih kategori dulu sebelum input plat
    print("Kategori: 1. Mobil  |  2. Motor")
    pilihan = input("Pilih kategori (1/2): ").strip()

    if pilihan == "1":
        kategori = "mobil"
    elif pilihan == "2":
        kategori = "motor"
    else:
        print("[-] Pilihan tidak valid.")

    # Cek kapasitas
    bisa_masuk, terpakai = cek_kapasitas(kategori)
    if not bisa_masuk:
        print(f"[!] Maaf, slot {kategori} penuh! ({terpakai}/{KAPASITAS[kategori]} terisi)")
        return

    plat_nomor = input("Masukkan Plat Nomor: ").strip().upper()

    # Cek plat ganda (kendaraan sama belum keluar)
    for v in data_parkir.values():
        if v["plat"] == plat_nomor:
            print(f"\n[!!] Plat {plat_nomor} sudah tercatat sedang parkir!")
            return

    id_parkir   = str(uuid.uuid4())[:8].upper()
    waktu_masuk = datetime.datetime.now()

    data_parkir[id_parkir] = {
        "plat"       : plat_nomor,
        "kategori"   : kategori,
        "waktu_masuk": waktu_masuk
    }

    sisa_slot = KAPASITAS[kategori] - (terpakai + 1)

    cetak_separator()
    print(f"[OK] Kendaraan berhasil masuk!")
    print(f"   ID Parkir   : {id_parkir}")
    print(f"   Plat Nomor  : {plat_nomor}")
    print(f"   Kategori    : {kategori.capitalize()}")
    print(f"   Waktu Masuk : {waktu_masuk.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Slot {kategori.capitalize()} Sisa : {sisa_slot}/{KAPASITAS[kategori]}")
    cetak_separator()
    print(f"   [!] Simpan ID Parkir Anda!")

def kendaraan_keluar():
    print("\n" + "="*40)
    print("        KENDARAAN KELUAR")
    cetak_separator()

    id_input = input("Masukkan ID Parkir: ").strip().upper()

    if id_input not in data_parkir:
        print("[-] ID tidak ditemukan! Silakan cek kembali.")
        return

    kendaraan    = data_parkir[id_input]
    waktu_keluar = datetime.datetime.now()
    waktu_masuk  = kendaraan["waktu_masuk"]

    durasi        = waktu_keluar - waktu_masuk
    menit_parkir  = max(1, int(durasi.total_seconds() / 60))
    total_bayar   = menit_parkir * TARIF[kendaraan["kategori"]]

    # Simpan ke history
    record = {
        "id"          : id_input,
        "plat"        : kendaraan["plat"],
        "kategori"    : kendaraan["kategori"],
        "waktu_masuk" : waktu_masuk,
        "waktu_keluar": waktu_keluar,
        "durasi_menit": menit_parkir,
        "total_bayar" : total_bayar
    }
    history_parkir.append(record)
    del data_parkir[id_input]

    cetak_separator()
    print("          STRUK PEMBAYARAN")
    cetak_separator()
    print(f"  ID          : {id_input}")
    print(f"  Plat Nomor  : {kendaraan['plat']}")
    print(f"  Kategori    : {kendaraan['kategori'].capitalize()}")
    print(f"  Masuk       : {waktu_masuk.strftime('%H:%M:%S')}")
    print(f"  Keluar      : {waktu_keluar.strftime('%H:%M:%S')}")
    print(f"  Durasi      : {format_durasi(menit_parkir)}")
    cetak_separator()
    print(f"  TOTAL BAYAR : Rp {total_bayar:,}")
    cetak_separator()
    print("  Terima kasih, selamat berkendara! ^_^")

def lihat_status():
    print("\n" + "="*40)
    print("       STATUS PARKIRAN SAAT INI")
    cetak_separator()

    for kategori in ["mobil", "motor"]:
        terpakai = hitung_slot_terpakai(kategori)
        sisa     = KAPASITAS[kategori] - terpakai
        bar      = "[#]" * terpakai + "[_]" * sisa
        print(f"  {kategori.capitalize():5s} [{bar}] {terpakai}/{KAPASITAS[kategori]}")

    if not data_parkir:
        print("\n  (Tidak ada kendaraan parkir saat ini)")
    else:
        cetak_separator()
        print(f"  {'ID':^8} {'Plat':^10} {'Jenis':^6} {'Masuk':^10}")
        cetak_separator("-")
        for id_p, v in data_parkir.items():
            print(f"  {id_p:^8} {v['plat']:^10} {v['kategori'].capitalize():^6} "
                  f"{v['waktu_masuk'].strftime('%H:%M:%S'):^10}")
    cetak_separator()

def lihat_history():
    print("\n" + "="*40)
    print("        RIWAYAT PARKIRAN")
    cetak_separator()

    if not history_parkir:
        print("  Belum ada riwayat parkiran.")
        cetak_separator()
        return

    total_pendapatan = sum(r["total_bayar"] for r in history_parkir)

    print(f"  {'No':>3} {'ID':^8} {'Plat':^10} {'Jenis':^6} {'Durasi':^10} {'Bayar':>12}")
    cetak_separator("-")
    for i, r in enumerate(history_parkir, 1):
        print(f"  {i:>3} {r['id']:^8} {r['plat']:^10} "
              f"{r['kategori'].capitalize():^6} "
              f"{format_durasi(r['durasi_menit']):^10} "
              f"Rp {r['total_bayar']:>8,}")

    cetak_separator()
    print(f"  Total Kendaraan  : {len(history_parkir)}")
    print(f"  Total Pendapatan : Rp {total_pendapatan:,}")
    cetak_separator()

def cari_kendaraan():
    print("\n" + "="*40)
    print("        CARI KENDARAAN")
    cetak_separator()

    keyword = input("Masukkan Plat Nomor (boleh sebagian): ").strip().upper()

    # Cari di parkiran aktif
    hasil_aktif = [(id_p, v) for id_p, v in data_parkir.items() if keyword in v["plat"]]

    # Cari di history
    hasil_history = [r for r in history_parkir if keyword in r["plat"]]

    if not hasil_aktif and not hasil_history:
        print(f"\n  [-] Plat '{keyword}' tidak ditemukan.")
        cetak_separator()
        return

    # Tampilkan yang masih parkir
    if hasil_aktif:
        print(f"\n  [>>] Sedang Parkir:")
        cetak_separator("-")
        print(f"  {'ID':^8} {'Plat':^10} {'Jenis':^6} {'Masuk':^10} {'Durasi Skrg':^12}")
        cetak_separator("-")
        for id_p, v in hasil_aktif:
            sekarang = datetime.datetime.now()
            menit    = max(1, int((sekarang - v["waktu_masuk"]).total_seconds() / 60))
            print(f"  {id_p:^8} {v['plat']:^10} {v['kategori'].capitalize():^6} "
                  f"{v['waktu_masuk'].strftime('%H:%M:%S'):^10} {format_durasi(menit):^12}")

    # Tampilkan riwayat
    if hasil_history:
        print(f"\n  [>>] Riwayat:")
        cetak_separator("-")
        print(f"  {'Plat':^10} {'Jenis':^6} {'Masuk':^10} {'Keluar':^10} {'Durasi':^10} {'Bayar':>12}")
        cetak_separator("-")
        for r in hasil_history:
            print(f"  {r['plat']:^10} {r['kategori'].capitalize():^6} "
                  f"{r['waktu_masuk'].strftime('%H:%M:%S'):^10} "
                  f"{r['waktu_keluar'].strftime('%H:%M:%S'):^10} "
                  f"{format_durasi(r['durasi_menit']):^10} "
                  f"Rp {r['total_bayar']:>8,}")

    cetak_separator()

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    while True:
        print("\n" + "="*40)
        print("       SISTEM PARKIR DIGITAL")
        cetak_separator()
        print("  1. Kendaraan Masuk")
        print("  2. Kendaraan Keluar")
        print("  3. Status Parkiran")
        print("  4. Riwayat Parkiran")
        print("  5. Cari Kendaraan")
        print("  6. Keluar Aplikasi")
        cetak_separator()
        opsi = input("  Pilih menu (1-6): ").strip()

        if   opsi == "1": kendaraan_masuk()
        elif opsi == "2": kendaraan_keluar()
        elif opsi == "3": lihat_status()
        elif opsi == "4": lihat_history()
        elif opsi == "5": cari_kendaraan()
        elif opsi == "6":
            print("\n  Terima kasih! Sampai jumpa o/")
            break
        else:
            print("  [-] Pilihan tidak valid.")

if __name__ == "__main__":
    main()