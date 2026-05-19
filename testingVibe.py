import datetime
import uuid

data_parkir = {}

def kendaraan_masuk():
    # placeholder
    print("\n--- KENDARAAN MASUK ---")
    # 1. Generate ID Unik
    id_parkir = str(uuid.uuid4())[:5].upper()
    
    # 2. Input Kategori dan Plat Nomor
    plat_nomor = input("Masukkan Plat Nomor: ")
    print("Kategori: 1. Mobil | 2. Motor")
    pilihan = input("Pilih kategori (1/2): ")
    
    kategori = "mobil" if pilihan == "1" else "motor"
    waktu_masuk = datetime.datetime.now()
    
    data_parkir[id_parkir] = {
        "plat": plat_nomor,
        "kategori": kategori,
        "waktu_masuk": waktu_masuk
    }
    
    # placeholder
    print(f"\nBerhasil!")
    print(f"ID Parkir    : {id_parkir}")
    print(f"Waktu Masuk  : {waktu_masuk.strftime('%H:%M:%S')}")
    return id_parkir

def kendaraan_keluar():
    # placeholder
    print("\n--- KENDARAAN KELUAR ---")
    id_input = input("Masukkan ID Parkir: ")
    
    if id_input in data_parkir:
        kendaraan = data_parkir[id_input]
        waktu_keluar = datetime.datetime.now()
        waktu_masuk = kendaraan["waktu_masuk"]
        
        # 3. Hitung Durasi dan Tarif
        durasi = waktu_keluar - waktu_masuk
        menit_parkir = max(1, int(durasi.total_seconds() / 60))
        
        tarif_per_menit = 5000 if kendaraan["kategori"] == "mobil" else 2000
        total_bayar = menit_parkir * tarif_per_menit
        
        #placeholder
        print(f"\n--- STRUK PEMBAYARAN ---")
        print(f"ID           : {id_input}")
        print(f"Plat Nomor   : {kendaraan['plat']}")
        print(f"Kategori     : {kendaraan['kategori'].capitalize()}")
        print(f"Durasi       : {menit_parkir} Menit")
        print(f"Total Tarif  : Rp {total_bayar:,}")
        
        del data_parkir[id_input]
    else:
        print("ID tidak ditemukan! Silakan cek kembali.")


# placeholder
def main():
    while True:
        print("\n=== SISTEM PARKIR DIGITAL ===")
        print("1. Kendaraan Masuk")
        print("2. Kendaraan Keluar")
        print("3. Keluar Aplikasi")
        opsi = input("Pilih menu (1/2/3): ")
        
        if opsi == "1":
            kendaraan_masuk()
        elif opsi == "2":
            kendaraan_keluar()
        elif opsi == "3":
            print("Terima kasih!")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()