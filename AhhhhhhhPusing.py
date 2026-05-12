from textual.app import App, ComposeResult
from textual.widgets import Input, Label, Button, Header, Footer, Static, DataTable
from textual.containers import Vertical, Horizontal
import datetime
import uuid

class ParkiranGabut(App):
    # ============================================================
    # KONFIGURASI TAMPILAN (CSS)
    # ============================================================
    CSS = """
    #main-container { height: 100%; }
    #left-panel { width: 60%; padding: 1; }
    #right-panel { width: 40%; border-left: solid $primary; padding: 1; }
    .box { border: solid green; padding: 1; margin: 1 0; height: auto; }
    .hidden { display: none; }
    #struk-area { 
        border: double white; 
        background: $boost; 
        margin-top: 1; 
        padding: 1; 
        height: 8; 
    }
    DataTable { height: 100%; border: tall $primary; }
    """

    # Database sementara di dalam memori
    data_parkir = {}
    kategori_pilihan = ""

    def compose(self) -> ComposeResult:
        """Menyusun struktur UI aplikasi"""
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):

            # PANEL KIRI: Tempat interaksi User
            with Vertical(id="left-panel"):
                yield Label("[b]MENU UTAMA[/]")
                with Horizontal():
                    yield Button("Masuk", variant="primary", id="menu-masuk")
                    yield Button("Keluar", variant="error", id="menu-keluar")

                # FORM MASUK: Muncul saat tombol 'Masuk' ditekan
                with Vertical(id="area-masuk", classes="hidden box"):
                    yield Label("Pilih Tipe Kendaraan:")
                    with Horizontal():
                        yield Button("Mobil", id="pilih-mobil")
                        yield Button("Motor", id="pilih-motor")
                    yield Label("", id="label-kategori")
                    yield Input(placeholder="Masukkan Plat Nomor...", id="input-plat", classes="hidden")

                # FORM KELUAR: Muncul saat tombol 'Keluar' ditekan
                with Vertical(id="area-keluar", classes="hidden box"):
                    yield Label("[b red]PROSES KELUAR[/]")
                    yield Label("Masukkan ID dari tabel kanan:")
                    yield Input(placeholder="Contoh: A1B2C", id="input-id-keluar")

                # AREA OUTPUT: Tempat menampilkan pesan status dan struk bayar
                yield Label("\n[b]INFO / STRUK PEMBAYARAN:[/]")
                yield Static("Silahkan pilih menu di atas.", id="struk-area")

            # PANEL KANAN: Monitoring Live
            with Vertical(id="right-panel"):
                yield Label("[b]DAFTAR KENDARAAN (LIVE)[/]")
                yield DataTable(id="tabel-parkir")
        
        yield Footer()

    def on_mount(self) -> None:
        """Inisialisasi tabel saat aplikasi pertama kali jalan"""
        table = self.query_one(DataTable)
        table.add_columns("ID", "Plat", "Tipe", "Jam Masuk")
        table.cursor_type = "row"

    def update_table(self) -> None:
        """LOGIKA UPDATE TABEL: Refresh data di layar kanan agar sinkron dengan database"""
        table = self.query_one(DataTable)
        table.clear() # Hapus semua baris lama
        for id_pk, info in self.data_parkir.items():

            # Tambahkan ulang data dari dictionary ke tabel UI
            table.add_row(
                id_pk, 
                info["plat"], 
                info["kategori"], 
                info["waktu_masuk"].strftime("%H:%M:%S")
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """LOGIKA TOMBOL: Menangani perpindahan menu dan pemilihan kategori"""
        struk = self.query_one("#struk-area", Static)
        
        # Switch menu ke 'Masuk'
        if event.button.id == "menu-masuk":
            self.query_one("#area-masuk").remove_class("hidden")
            self.query_one("#area-keluar").add_class("hidden")
            struk.update("Pilih kategori kendaraan...")

        # Switch menu ke 'Keluar'
        elif event.button.id == "menu-keluar":
            self.query_one("#area-keluar").remove_class("hidden")
            self.query_one("#area-masuk").add_class("hidden")
            struk.update("Masukkan ID Parkir untuk checkout.")

        # Pilih kategori (Mobil/Motor)
        elif event.button.id in ["pilih-mobil", "pilih-motor"]:
            self.kategori_pilihan = "Mobil" if event.button.id == "pilih-mobil" else "Motor"
            self.query_one("#label-kategori").update(f"Terpilih: [b]{self.kategori_pilihan}[/]")
            self.query_one("#input-plat").remove_class("hidden") # Munculkan input plat
            self.query_one("#input-plat").focus() # Langsung arahkan kursor ke input

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """LOGIKA UTAMA: Pemrosesan Data Masuk & Keluar saat Enter ditekan"""
        struk = self.query_one("#struk-area", Static)
        
        # --- LOGIKA KENDARAAN MASUK ---
        if event.input.id == "input-plat":
            plat = event.value.upper()
            if not plat: return
            
            # Generate ID unik 5 digit
            id_pk = str(uuid.uuid4())[:5].upper()
            
            # Simpan data ke dictionary
            self.data_parkir[id_pk] = {
                "plat": plat, 
                "kategori": self.kategori_pilihan,
                "waktu_masuk": datetime.datetime.now()
            }
            
            self.update_table() # Refresh tabel kanan
            struk.update(f"[b green]MASUK BERHASIL[/]\nID: {id_pk}\nPlat: {plat}")
            
            # Reset form ke kondisi awal
            event.input.value = ""
            self.query_one("#area-masuk").add_class("hidden")
            self.query_one("#input-plat").add_class("hidden")

        # --- LOGIKA KENDARAAN KELUAR & PERHITUNGAN ---
        elif event.input.id == "input-id-keluar":
            id_input = event.value.upper()
            
            if id_input in self.data_parkir:
                data = self.data_parkir[id_input]
                
                # 1. Hitung selisih waktu
                waktu_keluar = datetime.datetime.now()
                durasi = waktu_keluar - data["waktu_masuk"]
                
                # 2. Konversi ke menit
                menit = max(1, int(durasi.total_seconds() / 60))
                
                # 3. Logika Tarif sesuai kategori
                tarif_per_menit = 5000 if data["kategori"] == "Mobil" else 2000
                total_bayar = menit * tarif_per_menit
                
                # 4. Tampilkan struk
                struk_teks = (
                    f"[b red]STRUK KELUAR[/]\n"
                    f"Plat: {data['plat']} ({data['kategori']})\n"
                    f"Durasi: {menit} Menit\n"
                    f"Tarif: Rp {total_bayar:,}"
                )
                struk.update(struk_teks)
                
                # 5. Hapus data dari database & refresh tabel
                del self.data_parkir[id_input]
                self.update_table()
            else:
                struk.update("[b red]ID TIDAK DITEMUKAN![/]")
            
            event.input.value = ""
            self.query_one("#area-keluar").add_class("hidden")

if __name__ == "__main__":
    app = ParkiranGabut()
    app.run()