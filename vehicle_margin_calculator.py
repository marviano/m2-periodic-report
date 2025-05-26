#!/usr/bin/env python3
# vehicle_margin_calculator.py
# Detailed vehicle margin calculator that displays step-by-step calculations

import os
import sys
import argparse
import locale
import mysql.connector
from datetime import datetime
from db_operations import connect_to_database

# Set locale for proper number formatting
locale.setlocale(locale.LC_ALL, '')

def format_number(value):
    """Format number with thousands separators."""
    if value is None:
        return "0.00"
    return f"{value:,.2f}"

def get_vehicle_details(search_term, search_type, database_name="honda_mis"):
    """
    Retrieve vehicle details from database.
    
    Args:
        search_term (str): Vehicle identifier to search for (frame number, SPK, etc.)
        search_type (str): Type of search ('frame', 'spk', 'bast')
        database_name (str): Database to connect to
    """
    conn = connect_to_database(database_name)
    cursor = conn.cursor(dictionary=True)
    
    # Build the WHERE clause based on search type
    if search_type == 'frame':
        where_clause = "bast.no_rangka = %s"
    elif search_type == 'spk':
        where_clause = "spk.no_form_spk = %s"
    elif search_type == 'bast':
        where_clause = "bast.kode_bast = %s"
    else:
        print(f"Error: Invalid search type '{search_type}'")
        sys.exit(1)
    
    # Query to get vehicle details with all margin components
    query = f"""
    SELECT 
        bast.kode_bast, 
        bast.tgl_bast,
        spk.no_form_spk,
        spk.cara_bayar,
        mp.nama_pelanggan,
        mb.kode_warna_lengkap,
        mb.nama_lengkap,
        bast.no_rangka,
        bast.no_mesin,
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
        spk.saving,
        (
            spk.harga_jual - (
                IFNULL(dor.harga_ppn, 0) + 
                spk.diskon + 
                spk.nota_kredit + 
                spk.komisi_makelar +
                IFNULL(pl.dp_gross, 0) - 
                IFNULL(pl.subs_ahm, 0) - 
                IFNULL(pl.main_dealer, 0) - 
                IFNULL(mb.perk_notice, 0) +
                (spk.um_t_leasing - spk.uang_muka + spk.komisi_makelar_leasing) - 
                spk.promo_pusat
            ) - spk.perk_adm_wil + spk.saving
        ) AS margin_unit
    FROM tbl_spk AS spk 
    INNER JOIN tbl_bast AS bast 
        ON bast.kode_spk = spk.kode_spk 
    INNER JOIN vi_data_induk_barang_motor AS mb 
        ON spk.kendaraan_warna_id = mb.data_id 
    INNER JOIN tbl_data_induk_pelanggan AS mp 
        ON spk.kode_pelanggan_faktur = mp.pelanggan_id 
    LEFT JOIN tbl_sub_barang_masuk AS sbm 
        ON bast.no_rangka = sbm.no_rangka
    LEFT JOIN tbl_barang_masuk AS bm 
        ON sbm.kode_bm = bm.kode_bm
    LEFT JOIN vi_do_lengkap AS dor 
        ON bm.no_do = dor.no_do 
        AND mb.kode_warna_lengkap = dor.kode_barang_lengkap
    LEFT JOIN tbl_penagihan_leasing pl 
        ON pl.kode_bast = bast.kode_bast
    WHERE {where_clause}
    """
    
    try:
        cursor.execute(query, (search_term,))
        result = cursor.fetchone()
        
        if not result:
            print(f"No vehicle found with {search_type} '{search_term}'")
            sys.exit(1)
            
        return result
    
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def display_margin_calculation(vehicle):
    """Display detailed margin calculation for a vehicle."""
    # Extract all needed values
    v_number = vehicle.get('_index', 1)  # Vehicle counter for display, default to 1
    
    # Calculate factors used in margin calculation
    faktor_leasing = vehicle['um_t_leasing'] - vehicle['uang_muka'] + vehicle['komisi_makelar_leasing']
    faktor_diskon = vehicle['diskon'] + vehicle['nota_kredit'] + vehicle['komisi_makelar']
    faktor_subsidi = vehicle['subs_ahm'] + vehicle['main_dealer']
    
    # Calculate biaya based on payment method
    if vehicle['cara_bayar'] and vehicle['cara_bayar'].upper() == 'KREDIT':
        perhitungan_biaya = vehicle['harga_tebus'] + faktor_diskon + vehicle['dp_gross'] + faktor_leasing - vehicle['promo_pusat']
        payment_method = "KREDIT"
    else:
        perhitungan_biaya = vehicle['harga_tebus'] + faktor_diskon - vehicle['promo_pusat']
        payment_method = "TUNAI"
    
    # Calculate final margin
    margin_akhir = vehicle['harga_jual'] - perhitungan_biaya - vehicle['perk_notice'] - vehicle['perk_adm_wil'] + faktor_subsidi
    
    # Compare with database calculated margin
    selisih = margin_akhir - vehicle['margin_unit']
    
    # Format the date
    try:
        tanggal = vehicle['tgl_bast'].strftime('%Y-%m-%d')
    except:
        tanggal = str(vehicle['tgl_bast'])
    
    # Print the detailed margin calculation
    print(f"\nKendaraan {v_number}: {vehicle['no_rangka']} - {vehicle['nama_lengkap']}")
    print(f"  BAST: {vehicle['kode_bast']} - SPK: {vehicle['no_form_spk']}")
    print(f"  Tanggal: {tanggal}")
    print(f"  Cara Bayar: {payment_method}")
    print()
    print("  Komponen Margin:")
    print(f"    spk.harga_jual = {format_number(vehicle['harga_jual'])}")
    print(f"    dor.harga_ppn (harga_tebus) = {format_number(vehicle['harga_tebus'])}")
    print(f"    spk.diskon = {format_number(vehicle['diskon'])}")
    print(f"    spk.nota_kredit = {format_number(vehicle['nota_kredit'])}")
    print(f"    spk.komisi_makelar = {format_number(vehicle['komisi_makelar'])}")
    print(f"    pl.dp_gross = {format_number(vehicle['dp_gross'])}")
    print(f"    pl.subs_ahm = {format_number(vehicle['subs_ahm'])}")
    print(f"    pl.main_dealer = {format_number(vehicle['main_dealer'])}")
    print(f"    mb.perk_notice = {format_number(vehicle['perk_notice'])}")
    print(f"    spk.um_t_leasing = {format_number(vehicle['um_t_leasing'])}")
    print(f"    spk.uang_muka = {format_number(vehicle['uang_muka'])}")
    print(f"    spk.komisi_makelar_leasing = {format_number(vehicle['komisi_makelar_leasing'])}")
    print(f"    spk.promo_pusat = {format_number(vehicle['promo_pusat'])}")
    print(f"    spk.perk_adm_wil = {format_number(vehicle['perk_adm_wil'])}")
    print(f"    spk.saving = {format_number(vehicle['saving'])}")
    print()
    print("  Perhitungan Langkah demi Langkah:")
    print(f"    Faktor Leasing (um_t_leasing - uang_muka + komisi_makelar_leasing) = {format_number(faktor_leasing)}")
    print(f"    Faktor Diskon (diskon + nota_kredit + komisi_makelar) = {format_number(faktor_diskon)}")
    print(f"    Faktor Subsidi (subs_ahm + main_dealer) = {format_number(faktor_subsidi)}")
    print(f"    Perhitungan Biaya ({payment_method}) = {format_number(perhitungan_biaya)}")
    
    if payment_method == "KREDIT":
        print(f"      = harga_tebus + faktor_diskon + dp_gross + faktor_leasing - promo_pusat")
        print(f"      = {format_number(vehicle['harga_tebus'])} + {format_number(faktor_diskon)} + {format_number(vehicle['dp_gross'])} + {format_number(faktor_leasing)} - {format_number(vehicle['promo_pusat'])}")
    else:
        print(f"      = harga_tebus + faktor_diskon - promo_pusat")
        print(f"      = {format_number(vehicle['harga_tebus'])} + {format_number(faktor_diskon)} - {format_number(vehicle['promo_pusat'])}")
    
    print(f"    Margin Akhir = harga_jual - perhitungan_biaya - perk_notice - perk_adm_wil + faktor_subsidi")
    print(f"                 = {format_number(vehicle['harga_jual'])} - {format_number(perhitungan_biaya)} - {format_number(vehicle['perk_notice'])} - {format_number(vehicle['perk_adm_wil'])} + {format_number(faktor_subsidi)}")
    print(f"                 = {format_number(margin_akhir)}")
    print()
    print(f"  Hasil Rumus Asli = {format_number(vehicle['margin_unit'])}")
    print(f"  Selisih = {format_number(selisih)}")
    print()

def main():
    """Main function to parse arguments and run the margin calculator."""
    parser = argparse.ArgumentParser(description='Calculate and display detailed vehicle margin.')
    parser.add_argument('search_term', help='Vehicle identifier (frame number, SPK, or BAST)')
    parser.add_argument('--type', choices=['frame', 'spk', 'bast'], default='frame', 
                        help='Type of search term (default: frame)')
    parser.add_argument('--db', choices=['honda_mis', 'm2_magetan'], default='honda_mis',
                        help='Database to use (default: honda_mis)')
    args = parser.parse_args()
    
    try:
        vehicle = get_vehicle_details(args.search_term, args.type, args.db)
        display_margin_calculation(vehicle)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 