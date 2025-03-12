import mysql.connector
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

def connect_to_database():
    """Membuat koneksi ke database MySQL."""
    return mysql.connector.connect(
        host="36.74.102.231",
        user="honda_mis",
        password="mcMotor",
        database="honda_mis"
    )

def debug_perhitungan_margin(tanggal_mulai: str, tanggal_akhir: str) -> None:
    """
    Debug perhitungan margin dengan mencetak semua nilai komponen untuk setiap kendaraan.
    """
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)

    # Query untuk mengambil semua variabel yang digunakan dalam perhitungan margin
    debug_query = """
    SELECT 
        bast.kode_bast, 
        bast.tgl_bast,
        spk.no_form_spk,
        mb.nama_lengkap,
        bast.no_rangka,
        spk.cara_bayar,
        spk.harga_jual,
        IFNULL(dor.harga_ppn, 0) AS harga_tebus,
        spk.diskon,
        spk.nota_kredit,
        spk.komisi_makelar,
        IFNULL(pl.dp_gross, 0) AS dp_gross,
        IFNULL(pl.subs_ahm, 0) AS subs_ahm,
        IFNULL(pl.main_dealer, 0) AS main_dealer,
        IFNULL(mb.perk_notice, 0) AS perk_notice,
        spk.um_t_leasing,
        spk.uang_muka,
        spk.komisi_makelar_leasing,
        spk.promo_pusat,
        spk.perk_adm_wil,
        spk.saving
    FROM tbl_spk AS spk 
    INNER JOIN tbl_bast AS bast 
        ON bast.kode_spk = spk.kode_spk 
    INNER JOIN vi_data_induk_barang_motor AS mb 
        ON spk.kendaraan_warna_id = mb.data_id 
    LEFT JOIN tbl_sub_barang_masuk AS sbm 
        ON bast.no_rangka = sbm.no_rangka
    LEFT JOIN tbl_barang_masuk AS bm 
        ON sbm.kode_bm = bm.kode_bm
    LEFT JOIN vi_do_lengkap AS dor 
        ON bm.no_do = dor.no_do 
        AND mb.kode_warna_lengkap = dor.kode_barang_lengkap
    LEFT JOIN tbl_penagihan_leasing pl 
        ON pl.kode_bast = bast.kode_bast
    WHERE DATE_FORMAT(bast.tgl_bast, '%Y-%m-%d') BETWEEN %s AND %s
    """
    
    try:
        cursor.execute(debug_query, (tanggal_mulai, tanggal_akhir))
        hasil = cursor.fetchall()
        
        if not hasil:
            print("Tidak ada data ditemukan untuk rentang tanggal yang ditentukan.")
            return
        
        print(f"Ditemukan {len(hasil)} kendaraan untuk di-debug.\n")
        
        for i, baris in enumerate(hasil, 1):
            # Mengambil semua nilai yang diperlukan untuk perhitungan margin
            harga_jual = float(baris['harga_jual'] or 0)
            harga_tebus = float(baris['harga_tebus'] or 0)
            diskon = float(baris['diskon'] or 0)
            nota_kredit = float(baris['nota_kredit'] or 0)
            komisi_makelar = float(baris['komisi_makelar'] or 0)
            dp_gross = float(baris['dp_gross'] or 0)
            subs_ahm = float(baris['subs_ahm'] or 0)
            main_dealer = float(baris['main_dealer'] or 0)
            perk_notice = float(baris['perk_notice'] or 0)
            um_t_leasing = float(baris['um_t_leasing'] or 0)
            uang_muka = float(baris['uang_muka'] or 0)
            komisi_makelar_leasing = float(baris['komisi_makelar_leasing'] or 0)
            promo_pusat = float(baris['promo_pusat'] or 0)
            perk_adm_wil = float(baris['perk_adm_wil'] or 0)
            saving = float(baris['saving'] or 0)
            
            # Menghitung margin dengan debugging langkah demi langkah
            faktor_leasing = (um_t_leasing - uang_muka + komisi_makelar_leasing)
            faktor_diskon = (diskon + nota_kredit + komisi_makelar)
            faktor_subsidi = (subs_ahm + main_dealer)
            
            # Mencetak informasi debugging detail untuk setiap kendaraan
            cara_bayar = baris['cara_bayar'].lower() if baris['cara_bayar'] else 'tunai'
            is_kredit = 'kredit' in cara_bayar
            
            print(f"Kendaraan {i}: {baris['no_rangka']} - {baris['nama_lengkap']}")
            print(f"  BAST: {baris['kode_bast']} - SPK: {baris['no_form_spk']}")
            print(f"  Tanggal: {baris['tgl_bast']}")
            print(f"  Cara Bayar: {cara_bayar.upper()}")
            print("\n  Komponen Margin:")
            print(f"    spk.harga_jual = {harga_jual:,.2f}")
            print(f"    dor.harga_ppn (harga_tebus) = {harga_tebus:,.2f}")
            print(f"    spk.diskon = {diskon:,.2f}")
            print(f"    spk.nota_kredit = {nota_kredit:,.2f}")
            print(f"    spk.komisi_makelar = {komisi_makelar:,.2f}")
            print(f"    pl.dp_gross = {dp_gross:,.2f}")
            print(f"    pl.subs_ahm = {subs_ahm:,.2f}")
            print(f"    pl.main_dealer = {main_dealer:,.2f}")
            print(f"    mb.perk_notice = {perk_notice:,.2f}")
            print(f"    spk.um_t_leasing = {um_t_leasing:,.2f}")
            print(f"    spk.uang_muka = {uang_muka:,.2f}")
            print(f"    spk.komisi_makelar_leasing = {komisi_makelar_leasing:,.2f}")
            print(f"    spk.promo_pusat = {promo_pusat:,.2f}")
            print(f"    spk.perk_adm_wil = {perk_adm_wil:,.2f}")
            print(f"    spk.saving = {saving:,.2f}")
            
            # Perincian perhitungan dengan nilai menengah
            print("\n  Perhitungan Langkah demi Langkah:")
            print(f"    Faktor Leasing (um_t_leasing - uang_muka + komisi_makelar_leasing) = {faktor_leasing:,.2f}")
            print(f"    Faktor Diskon (diskon + nota_kredit + komisi_makelar) = {faktor_diskon:,.2f}")
            print(f"    Faktor Subsidi (subs_ahm + main_dealer) = {faktor_subsidi:,.2f}")
            
            # Perhitungan berbeda untuk kredit dan tunai
            if is_kredit:
                perhitungan_biaya = (
                    harga_tebus + 
                    faktor_diskon +
                    dp_gross + 
                    faktor_leasing - 
                    promo_pusat
                )
                
                print(f"    Perhitungan Biaya (KREDIT) = {perhitungan_biaya:,.2f}")
                print(f"      = harga_tebus + faktor_diskon + dp_gross + faktor_leasing - promo_pusat")
                print(f"      = {harga_tebus:,.2f} + {faktor_diskon:,.2f} + {dp_gross:,.2f} + {faktor_leasing:,.2f} - {promo_pusat:,.2f}")
                
                margin = harga_jual - perhitungan_biaya - perk_notice - perk_adm_wil + faktor_subsidi
            else:
                perhitungan_biaya = (
                    harga_tebus + 
                    faktor_diskon - 
                    promo_pusat
                )
                
                print(f"    Perhitungan Biaya (TUNAI) = {perhitungan_biaya:,.2f}")
                print(f"      = harga_tebus + faktor_diskon - promo_pusat")
                print(f"      = {harga_tebus:,.2f} + {faktor_diskon:,.2f} - {promo_pusat:,.2f}")
                
                margin = harga_jual - perhitungan_biaya - perk_notice - perk_adm_wil + faktor_subsidi
            
            print(f"    Margin Akhir = harga_jual - perhitungan_biaya - perk_notice - perk_adm_wil + faktor_subsidi")
            print(f"                 = {harga_jual:,.2f} - {perhitungan_biaya:,.2f} - {perk_notice:,.2f} - {perk_adm_wil:,.2f} + {faktor_subsidi:,.2f}")
            print(f"                 = {margin:,.2f}")
            
            # Membandingkan dengan rumus asli
            if is_kredit:
                margin_asli = (
                    harga_jual - (
                        harga_tebus + 
                        diskon + 
                        nota_kredit + 
                        komisi_makelar +
                        dp_gross +
                        (um_t_leasing - uang_muka + komisi_makelar_leasing) - 
                        promo_pusat
                    ) - perk_notice - perk_adm_wil + subs_ahm + main_dealer
                )
            else:
                margin_asli = (
                    harga_jual - (
                        harga_tebus + 
                        diskon + 
                        nota_kredit + 
                        komisi_makelar - 
                        promo_pusat
                    ) - perk_notice - perk_adm_wil + subs_ahm + main_dealer
                )
            
            print(f"\n  Hasil Rumus Asli = {margin_asli:,.2f}")
            print(f"  Selisih = {margin - margin_asli:,.2f}")
            print("-" * 80)
            
    except mysql.connector.Error as err:
        print(f"Kesalahan database: {err}")
    finally:
        cursor.close()
        conn.close()

# Contoh penggunaan
if __name__ == "__main__":
    # Atur rentang tanggal Anda di sini
    debug_perhitungan_margin("2025-03-03", "2025-03-03")