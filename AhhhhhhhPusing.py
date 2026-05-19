from textual.app import App, ComposeResult
from textual.widgets import Input, Label, Button, Header, Footer, Static, DataTable, Tab, Tabs
from textual.containers import Vertical, Horizontal, ScrollableContainer
import datetime
import uuid

# ─── KONFIGURASI ──────────────────────────────────────────────────────────────
KAPASITAS = {"Mobil": 5, "Motor": 5}
TARIF     = {"Mobil": 5000, "Motor": 2000}  # per menit


class ParkiranDigital(App):
    # ============================================================
    # KONFIGURASI TAMPILAN (CSS)
    # ============================================================
    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
    }

    /* ── PANEL KIRI ── */
    #left-panel {
        width: 55%;
        padding: 1 2;
    }

    #menu-bar {
        height: auto;
        margin-bottom: 1;
    }

    Button {
        margin-right: 1;
    }

    /* ── FORM BOX ── */
    .box {
        border: solid $primary;
        padding: 1;
        margin: 0 0 1 0;
        height: auto;
        min-height: 11; /* Mengunci tinggi minimum agar ruang input plat selalu aman */
    }

    .hidden {
        display: none;
    }

    /* ── STRUK ── */
    #struk-area {
        border: double $accent;
        background: $boost;
        margin-top: 1;
        padding: 1;
        height: 10;
        color: $text;
    }

    /* ── PANEL KANAN ── */
    #right-panel {
        width: 45%;
        border-left: solid $primary;
        padding: 1;
    }

    /* ── TABS ── */
    Tabs {
        height: 3;
        margin-bottom: 1;
    }

    /* ── TABEL ── */
    DataTable {
        height: 1fr;
        border: tall $primary;
    }

    /* ── SLOT BAR ── */
    #slot-info {
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
    }

    .slot-bar {
        height: auto;
        color: $text-muted;
    }

    /* ── CARI BOX ── */
    #area-cari Input {
        margin-top: 1;
    }

    /* ── LABEL ── */
    Label {
        margin-bottom: 1;
    }
    """

    # ─── HELPER ───────────────────────────────────────────────────
    def __init__(self):
        super().__init__()
        self.data_parkir     = {}   # kendaraan sedang parkir
        self.history_parkir  = []   # riwayat keluar
        self.kategori_pilihan = ""
        self.tab_aktif        = "tab-aktif"

    def hitung_slot_terpakai(self, kategori: str) -> int:
        return sum(1 for v in self.data_parkir.values() if v["kategori"] == kategori)

    def format_durasi(self, menit: int) -> str:
        jam  = menit // 60
        sisa = menit % 60
        if jam > 0:
            return f"{jam}j {sisa}m"
        return f"{sisa} menit"

    # ─── COMPOSE ──────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="main-container"):

            # ══ PANEL KIRI: Interaksi ══════════════════════════════
            with Vertical(id="left-panel"):
                yield Label("[b]MENU UTAMA[/]")

                with Horizontal(id="menu-bar"):
                    yield Button("🚗 Masuk",   variant="primary", id="menu-masuk")
                    yield Button("🚪 Keluar",  variant="error",   id="menu-keluar")
                    yield Button("🔍 Cari",    variant="warning", id="menu-cari")

                # ── FORM MASUK (Menggunakan ScrollableContainer agar anti-clip/anti-potong) ──
                with ScrollableContainer(id="area-masuk", classes="hidden box"):
                    yield Label("[b]KENDARAAN MASUK[/]")
                    yield Label("Pilih Tipe Kendaraan:")
                    with Horizontal(id="container-tipe"):
                        yield Button("🚗 Mobil", id="pilih-mobil", variant="primary")
                        yield Button("🏍 Motor", id="pilih-motor", variant="success")
                    yield Label("", id="label-kategori")
                    yield Input(
                        placeholder="Masukkan Plat Nomor lalu Enter...",
                        id="input-plat"
                    )

                # ── FORM KELUAR ──
                with Vertical(id="area-keluar", classes="hidden box"):
                    yield Label("[b red]PROSES KELUAR[/]")
                    yield Label("Masukkan ID Parkir (lihat tabel kanan):")
                    yield Input(placeholder="Contoh: A1B2C3D4", id="input-id-keluar")

                # ── FORM CARI ──
                with Vertical(id="area-cari", classes="hidden box"):
                    yield Label("[b yellow]CARI KENDARAAN[/]")
                    yield Label("Masukkan sebagian Plat Nomor lalu Enter:")
                    yield Input(placeholder="Contoh: B 1234, atau hanya '1234'", id="input-cari")

                # ── OUTPUT / STRUK ──
                yield Label("[b]INFO / STRUK PEMBAYARAN:[/]")
                yield Static("Pilih menu di atas untuk memulai.", id="struk-area")

            # ══ PANEL KANAN: Live Monitor ══════════════════════════
            with Vertical(id="right-panel"):
                yield Label("[b]MONITORING PARKIRAN[/]")

                # Slot bar
                with Vertical(id="slot-info"):
                    yield Static("", id="slot-bar")

                # Tabs: Aktif | Riwayat
                yield Tabs(
                    Tab("🟢 Parkir Aktif", id="tab-aktif"),
                    Tab("📋 Riwayat",      id="tab-history"),
                )

                yield DataTable(id="tabel-aktif")
                yield DataTable(id="tabel-history", classes="hidden")

        yield Footer()

    def on_mount(self) -> None:
        """Inisialisasi tabel"""
        t_aktif = self.query_one("#tabel-aktif", DataTable)
        t_aktif.add_columns("ID", "Plat", "Jenis", "Masuk", "Durasi")
        t_aktif.cursor_type = "row"

        t_hist = self.query_one("#tabel-history", DataTable)
        t_hist.add_columns("ID", "Plat", "Jenis", "Masuk", "Keluar", "Durasi", "Bayar")
        t_hist.cursor_type = "row"

        self.update_slot_bar()

        # Input plat disembunyikan total di awal boot secara aman
        self.query_one("#input-plat", Input).styles.display = "none"

        # Auto-refresh durasi setiap 30 detik
        self.set_interval(30, self.update_tabel_aktif)

    # ─── RENDER SLOT BAR ──────────────────────────────────────────
    def _render_slot_bar(self) -> str:
        lines = []
        for kat in ["Mobil", "Motor"]:
            terpakai = self.hitung_slot_terpakai(kat)
            sisa     = KAPASITAS[kat] - terpakai
            bar      = "█" * terpakai + "░" * sisa
            lines.append(f"[b]{kat}[/] [{bar}] {terpakai}/{KAPASITAS[kat]}")
        return "\n".join(lines)

    def update_slot_bar(self) -> None:
        self.query_one("#slot-bar", Static).update(self._render_slot_bar())

    # ─── UPDATE TABEL AKTIF ───────────────────────────────────────
    def update_tabel_aktif(self) -> None:
        t = self.query_one("#tabel-aktif", DataTable)
        t.clear()
        now = datetime.datetime.now()
        for id_pk, info in self.data_parkir.items():
            menit   = max(1, int((now - info["waktu_masuk"]).total_seconds() / 60))
            t.add_row(
                id_pk,
                info["plat"],
                info["kategori"],
                info["waktu_masuk"].strftime("%H:%M"),
                self.format_durasi(menit),
            )

    # ─── UPDATE TABEL HISTORY ─────────────────────────────────────
    def update_tabel_history(self) -> None:
        t = self.query_one("#tabel-history", DataTable)
        t.clear()
        for r in self.history_parkir:
            t.add_row(
                r["id"],
                r["plat"],
                r["kategori"],
                r["waktu_masuk"].strftime("%H:%M"),
                r["waktu_keluar"].strftime("%H:%M"),
                self.format_durasi(r["durasi_menit"]),
                f"Rp {r['total_bayar']:,}",
            )

    # ─── TAB SWITCH ───────────────────────────────────────────────
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        self.tab_aktif = event.tab.id
        if event.tab.id == "tab-aktif":
            self.query_one("#tabel-aktif").remove_class("hidden")
            self.query_one("#tabel-history").add_class("hidden")
            self.update_tabel_aktif()
        else:
            self.query_one("#tabel-history").remove_class("hidden")
            self.query_one("#tabel-aktif").add_class("hidden")
            self.update_tabel_history()

    # ─── TOMBOL ───────────────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        struk = self.query_one("#struk-area", Static)
        input_plat = self.query_one("#input-plat", Input)

        def hide_all_forms():
            self.query_one("#area-masuk").add_class("hidden")
            self.query_one("#area-keluar").add_class("hidden")
            self.query_one("#area-cari").add_class("hidden")

        if event.button.id == "menu-masuk":
            hide_all_forms()
            self.query_one("#area-masuk").remove_class("hidden")
            input_plat.styles.display = "none"
            self.query_one("#label-kategori").update("")
            self.kategori_pilihan = ""
            struk.update("Pilih tipe kendaraan lalu masukkan plat nomor.")

        elif event.button.id == "menu-keluar":
            hide_all_forms()
            self.query_one("#area-keluar").remove_class("hidden")
            self.query_one("#input-id-keluar").focus()
            struk.update("Masukkan ID Parkir untuk proses keluar & pembayaran.")

        elif event.button.id == "menu-cari":
            hide_all_forms()
            self.query_one("#area-cari").remove_class("hidden")
            self.query_one("#input-cari").focus()
            struk.update("Cari kendaraan berdasarkan plat nomor (aktif & riwayat).")

        elif event.button.id in ("pilih-mobil", "pilih-motor"):
            self.kategori_pilihan = "Mobil" if event.button.id == "pilih-mobil" else "Motor"
            terpakai  = self.hitung_slot_terpakai(self.kategori_pilihan)
            kapasitas = KAPASITAS[self.kategori_pilihan]

            if terpakai >= kapasitas:
                struk.update(
                    f"[b red]SLOT PENUH![/]\n"
                    f"Slot {self.kategori_pilihan} sudah penuh ({terpakai}/{kapasitas}).\n"
                    f"Tidak bisa menerima kendaraan baru."
                )
                self.query_one("#label-kategori").update(
                    f"[b red]Slot {self.kategori_pilihan} PENUH![/]"
                )
                input_plat.styles.display = "none"
                return

            self.query_one("#label-kategori").update(
                f"Terpilih: [b]{self.kategori_pilihan}[/]  "
                f"(Slot tersisa: {kapasitas - terpakai}/{kapasitas})"
            )
            
            # Memunculkan input plat, dipaksa render ulang di layar terminal biasa, lalu tuju fokus.
            input_plat.styles.display = "block"
            self.refresh()  
            input_plat.focus()

    # ─── INPUT SUBMITTED ──────────────────────────────────────────
    def on_input_submitted(self, event: Input.Submitted) -> None:
        struk = self.query_one("#struk-area", Static)

        # ── MASUK ────────────────────────────────────────────────
        if event.input.id == "input-plat":
            plat = event.value.strip().upper()
            if not plat:
                return

            if not self.kategori_pilihan:
                struk.update("[b red]Pilih tipe kendaraan terlebih dahulu![/]")
                return

            # Cek plat ganda
            for v in self.data_parkir.values():
                if v["plat"] == plat:
                    struk.update(
                        f"[b red]PLAT GANDA![/]\n"
                        f"Plat [b]{plat}[/] sudah tercatat sedang parkir!\n"
                        f"Selesaikan parkir yang lama terlebih dahulu."
                    )
                    event.input.value = ""
                    return

            id_pk       = uuid.uuid4().hex[:8].upper()
            waktu_masuk = datetime.datetime.now()
            terpakai    = self.hitung_slot_terpakai(self.kategori_pilihan)
            sisa        = KAPASITAS[self.kategori_pilihan] - terpakai - 1

            self.data_parkir[id_pk] = {
                "plat"       : plat,
                "kategori"   : self.kategori_pilihan,
                "waktu_masuk": waktu_masuk,
            }

            self.update_tabel_aktif()
            self.update_slot_bar()

            struk.update(
                f"[b green]✓ MASUK BERHASIL[/]\n"
                f"ID Parkir   : [b]{id_pk}[/]\n"
                f"Plat Nomor  : {plat}\n"
                f"Kategori    : {self.kategori_pilihan}\n"
                f"Jam Masuk   : {waktu_masuk.strftime('%H:%M:%S')}\n"
                f"Slot Sisa   : {sisa}/{KAPASITAS[self.kategori_pilihan]}\n"
                f"[yellow]Simpan ID parkir Anda![/]"
            )

            # Reset form & bersihkan display
            event.input.value = ""
            self.query_one("#area-masuk").add_class("hidden")
            event.input.styles.display = "none"
            self.kategori_pilihan = ""

        # ── KELUAR ───────────────────────────────────────────────
        elif event.input.id == "input-id-keluar":
            id_input = event.value.strip().upper()

            if id_input not in self.data_parkir:
                struk.update(
                    f"[b red]ID TIDAK DITEMUKAN![/]\n"
                    f"ID [b]{id_input}[/] tidak ada di database.\n"
                    f"Periksa kembali di tabel kanan."
                )
                event.input.value = ""
                return

            kendaraan    = self.data_parkir[id_input]
            waktu_keluar = datetime.datetime.now()
            durasi       = waktu_keluar - kendaraan["waktu_masuk"]
            menit        = max(1, int(durasi.total_seconds() / 60))
            total_bayar  = menit * TARIF[kendaraan["kategori"]]

            self.history_parkir.append({
                "id"          : id_input,
                "plat"        : kendaraan["plat"],
                "kategori"    : kendaraan["kategori"],
                "waktu_masuk" : kendaraan["waktu_masuk"],
                "waktu_keluar": waktu_keluar,
                "durasi_menit": menit,
                "total_bayar" : total_bayar,
            })

            del self.data_parkir[id_input]
            self.update_tabel_aktif()
            self.update_tabel_history()
            self.update_slot_bar()

            struk.update(
                f"[b red]══ STRUK PEMBAYARAN ══[/]\n"
                f"ID          : {id_input}\n"
                f"Plat        : {kendaraan['plat']}  ({kendaraan['kategori']})\n"
                f"Masuk       : {kendaraan['waktu_masuk'].strftime('%H:%M:%S')}\n"
                f"Keluar      : {waktu_keluar.strftime('%H:%M:%S')}\n"
                f"Durasi      : {self.format_durasi(menit)}\n"
                f"[b green]TOTAL BAYAR : Rp {total_bayar:,}[/]\n"
                f"Terima kasih! Selamat berkendara ^_^"
            )

            event.input.value = ""
            self.query_one("#area-keluar").add_class("hidden")

        # ── CARI ─────────────────────────────────────────────────
        elif event.input.id == "input-cari":
            keyword = event.value.strip().upper()
            if not keyword:
                return

            now = datetime.datetime.now()
            aktif = [(id_p, v) for id_p, v in self.data_parkir.items() if keyword in v["plat"]]
            hist = [r for r in self.history_parkir if keyword in r["plat"]]

            if not aktif and not hist:
                struk.update(
                    f"[b red]TIDAK DITEMUKAN[/]\n"
                    f"Plat mengandung '{keyword}' tidak ada\n"
                    f"di data aktif maupun riwayat."
                )
                event.input.value = ""
                return

            lines = [f"[b yellow]🔍 Hasil pencarian '{keyword}':[/]"]

            if aktif:
                lines.append("[b green]Sedang Parkir:[/]")
                for id_p, v in aktif:
                    menit = max(1, int((now - v["waktu_masuk"]).total_seconds() / 60))
                    lines.append(
                        f"  [{id_p}] {v['plat']} • {v['kategori']} • "
                        f"Masuk {v['waktu_masuk'].strftime('%H:%M')} • "
                        f"{self.format_durasi(menit)}"
                    )

            if hist:
                lines.append("[b cyan]Riwayat:[/]")
                for r in hist[-3:]:
                    lines.append(
                        f"  {r['plat']} • {r['kategori']} • "
                        f"{r['waktu_masuk'].strftime('%H:%M')}→"
                        f"{r['waktu_keluar'].strftime('%H:%M')} • "
                        f"Rp {r['total_bayar']:,}"
                    )

            struk.update("\n".join(lines))
            event.input.value = ""


if __name__ == "__main__":
    app = ParkiranDigital()
    app.run()