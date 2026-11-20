import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk 
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ResimToPdfApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Resim → PDF Dönüştürücü Pro")
        self.geometry("600x480")
        self.resizable(False, False)
        self.dosya_yollari = []
        self.arayuz_olustur()

        # İkon dosyası yoksa veya Windows değilse program çökmesin
        try:
            ikon_yolu = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfconvert.ico")
            self.iconbitmap(ikon_yolu)
        except Exception:
            pass

    def arayuz_olustur(self):
        self.baslik = ctk.CTkLabel(self, text="JPG / PNG → PDF", font=("Arial", 24, "bold"))
        self.baslik.pack(pady=(20, 10))

        # Liste Alanı
        self.liste_frame = ctk.CTkFrame(self)
        self.liste_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.liste = tk.Listbox(
            self.liste_frame, bg="#2b2b2b", fg="white", selectbackground="#1f538d",
            font=("Arial", 11), bd=0, highlightthickness=0
        )
        self.liste.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.scrollbar = ctk.CTkScrollbar(self.liste_frame, command=self.liste.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.liste.config(yscrollcommand=self.scrollbar.set)

        # Butonlar ve Seçenekler Alanı
        self.buton_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buton_frame.pack(pady=5)

        self.btn_ekle = ctk.CTkButton(self.buton_frame, text="Resim Ekle", command=self.resim_ekle, width=100)
        self.btn_ekle.grid(row=0, column=0, padx=5)

        self.btn_sil = ctk.CTkButton(self.buton_frame, text="Seçileni Sil", command=self.secileni_sil, width=100, fg_color="#8B0000", hover_color="#600000")
        self.btn_sil.grid(row=0, column=1, padx=5)

        self.btn_temizle = ctk.CTkButton(self.buton_frame, text="Temizle", command=self.listeyi_temizle, width=100, fg_color="#555555", hover_color="#333333")
        self.btn_temizle.grid(row=0, column=2, padx=5)

        # --- YENİ: Yön Seçimi Combobox'ı ---
        self.yon_secim = ctk.CTkComboBox(self.buton_frame, values=["Otomatik Yön", "Hepsi Dikey", "Hepsi Yatay"], width=130)
        self.yon_secim.set("Otomatik Yön")
        self.yon_secim.grid(row=0, column=3, padx=5)

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.pack(pady=15)
        self.progress.set(0)

        self.btn_donustur = ctk.CTkButton(self, text="PDF Olarak Kaydet", command=self.donusturme_baslat, font=("Arial", 16, "bold"), height=40)
        self.btn_donustur.pack(pady=(0, 20))

    def resim_ekle(self):
        dosyalar = filedialog.askopenfilenames(
            title="Resimleri Seç",
            filetypes=[("Resim Dosyaları", "*.jpg *.jpeg *.png")]
        )
        for dosya in dosyalar:
            if dosya not in self.dosya_yollari:
                self.dosya_yollari.append(dosya)
                self.liste.insert(tk.END, os.path.basename(dosya))

    def secileni_sil(self):
        secili_index = self.liste.curselection()
        if secili_index:
            index = secili_index[0]
            self.liste.delete(index)
            self.dosya_yollari.pop(index)

    def listeyi_temizle(self):
        self.liste.delete(0, tk.END)
        self.dosya_yollari.clear()
        self.progress.set(0)

    def donusturme_baslat(self):
        if not self.dosya_yollari:
            messagebox.showwarning("Uyarı", "Lütfen önce dönüştürülecek resimleri ekleyin.")
            return

        kayit_yolu = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Dosyası", "*.pdf")],
            title="PDF olarak kaydet"
        )

        if kayit_yolu:
            self.btn_donustur.configure(state="disabled", text="Dönüştürülüyor...")
            self.progress.set(0)
            threading.Thread(target=self.pdf_olustur_thread, args=(kayit_yolu,), daemon=True).start()

    def pdf_olustur_thread(self, kayit_yolu):
        try:
            resimler = []
            toplam_dosya = len(self.dosya_yollari)
            secilen_yon = self.yon_secim.get()

            for i, dosya in enumerate(self.dosya_yollari):
                img = Image.open(dosya)

                if img.mode != "RGB":
                    img = img.convert("RGB")

                # --- YENİ: Yön (Oryantasyon) Ayarlama ---
                width, height = img.size
                if secilen_yon == "Hepsi Dikey" and width > height:
                    # Resim yatay ama kullanıcı dikey istiyor, 90 derece döndür
                    img = img.transpose(Image.Transpose.ROTATE_270)
                elif secilen_yon == "Hepsi Yatay" and height > width:
                    # Resim dikey ama kullanıcı yatay istiyor, 90 derece döndür
                    img = img.transpose(Image.Transpose.ROTATE_270)

                # --- YENİ: Hızlı Yüklenme İçin Optimizasyon ---
                # Çözünürlüğü ekran boyutlarına uygun hale getirerek dosya boyutunu küçültüyoruz
                img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                
                resimler.append(img)
                self.progress.set((i + 1) / toplam_dosya)

            resimler[0].save(
                kayit_yolu,
                save_all=True,
                append_images=resimler[1:],
                resolution=100.0 # Çözünürlük bilgisi ekliyoruz
            )

            self.after(0, self.islem_basarili)

        except Exception as e:
            self.after(0, lambda: self.islem_hatali(str(e)))

    def islem_basarili(self):
        self.btn_donustur.configure(state="normal", text="PDF Olarak Kaydet")
        messagebox.showinfo("Başarılı", "PDF başarıyla oluşturuldu ve optimize edildi!")
        self.progress.set(1)

    def islem_hatali(self, hata_mesaji):
        self.btn_donustur.configure(state="normal", text="PDF Olarak Kaydet")
        self.progress.set(0)
        messagebox.showerror("Hata", f"Dönüştürme sırasında bir hata oluştu:\n{hata_mesaji}")

if __name__ == "__main__":
    app = ResimToPdfApp()
    app.mainloop()