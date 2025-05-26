#!/usr/bin/env python3
# vehicle_margin_batch.py
# Batch vehicle margin calculator that can process multiple vehicles based on date range

import os
import sys
import argparse
import locale
import mysql.connector
from datetime import datetime, timedelta
from db_operations import connect_to_database
from vehicle_margin_calculator import display_margin_calculation, format_number

# Set locale for proper number formatting
locale.setlocale(locale.LC_ALL, '')

def parse_date(date_str):
    """
    Parse date string in DD-MM-YYYY format to YYYY-MM-DD format
    Also accepts the original YYYY-MM-DD format for backward compatibility
    """
    if not date_str:
        return None
        
    # Try to detect the format
    if "-" in date_str:
        parts = date_str.split("-")
    elif "/" in date_str:
        parts = date_str.split("/")
    else:
        raise ValueError(f"Unrecognized date format: {date_str}. Use DD-MM-YYYY or DD/MM/YYYY")
    
    # If it's already YYYY-MM-DD
    if len(parts[0]) == 4:
        # Likely already YYYY-MM-DD
        return date_str
    
    # Convert from DD-MM-YYYY to YYYY-MM-DD
    if len(parts) != 3:
        raise ValueError(f"Invalid date format: {date_str}. Use DD-MM-YYYY or DD/MM/YYYY")
    
    day, month, year = parts
    return f"{year}-{month}-{day}"

def get_vehicles_by_date_range(start_date, end_date, database_name="honda_mis", limit=None):
    """
    Retrieve vehicle details from database for a specific date range.
    
    Args:
        start_date (str): Start date in DD-MM-YYYY or YYYY-MM-DD format
        end_date (str): End date in DD-MM-YYYY or YYYY-MM-DD format
        database_name (str): Database to connect to
        limit (int): Optional limit on number of records to return
    """
    # Convert dates to YYYY-MM-DD for database query
    start_date_formatted = parse_date(start_date)
    end_date_formatted = parse_date(end_date)
    
    conn = connect_to_database(database_name)
    cursor = conn.cursor(dictionary=True)
    
    # Query to get vehicle details with all margin components for a date range
    query = """
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
    WHERE DATE(bast.tgl_bast) BETWEEN %s AND %s
    ORDER BY bast.tgl_bast DESC
    """
    
    # Add limit if specified
    if limit:
        query += f" LIMIT {int(limit)}"
    
    try:
        cursor.execute(query, (start_date_formatted, end_date_formatted))
        results = cursor.fetchall()
        
        if not results:
            print(f"No vehicles found between {start_date} and {end_date}")
            sys.exit(1)
            
        return results
    
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def print_summary(vehicles):
    """Print a summary of all vehicles and their margins."""
    total_margin = sum(vehicle['margin_unit'] for vehicle in vehicles)
    total_harga_jual = sum(vehicle['harga_jual'] for vehicle in vehicles)
    total_harga_tebus = sum(vehicle['harga_tebus'] for vehicle in vehicles)
    
    # Count by payment method
    tunai_count = sum(1 for v in vehicles if not v['cara_bayar'] or v['cara_bayar'].upper() != 'KREDIT')
    kredit_count = sum(1 for v in vehicles if v['cara_bayar'] and v['cara_bayar'].upper() == 'KREDIT')
    
    # Calculate margins by payment method
    tunai_margin = sum(v['margin_unit'] for v in vehicles if not v['cara_bayar'] or v['cara_bayar'].upper() != 'KREDIT')
    kredit_margin = sum(v['margin_unit'] for v in vehicles if v['cara_bayar'] and v['cara_bayar'].upper() == 'KREDIT')
    
    print("\n=================== MARGIN SUMMARY ===================")
    print(f"Total Vehicles: {len(vehicles)}")
    print(f"  - Cash (TUNAI): {tunai_count}")
    print(f"  - Credit (KREDIT): {kredit_count}")
    print(f"Total Harga Jual: {format_number(total_harga_jual)}")
    print(f"Total Harga Tebus: {format_number(total_harga_tebus)}")
    print(f"Total Margin: {format_number(total_margin)}")
    print(f"  - Cash Margin: {format_number(tunai_margin)}")
    print(f"  - Credit Margin: {format_number(kredit_margin)}")
    print(f"Average Margin: {format_number(total_margin / len(vehicles) if vehicles else 0)}")
    print("======================================================")

def main():
    """Main function to parse arguments and run the batch margin calculator."""
    parser = argparse.ArgumentParser(description='Batch vehicle margin calculator.')
    parser.add_argument('--start-date', help='Start date (DD-MM-YYYY format, also accepts YYYY-MM-DD)', 
                       default=(datetime.now() - timedelta(days=7)).strftime('%d-%m-%Y'))
    parser.add_argument('--end-date', help='End date (DD-MM-YYYY format, also accepts YYYY-MM-DD)',
                       default=datetime.now().strftime('%d-%m-%Y'))
    parser.add_argument('--db', choices=['honda_mis', 'm2_magetan'], default='honda_mis',
                       help='Database to use (default: honda_mis)')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    parser.add_argument('--summary-only', action='store_true', 
                       help='Only show summary, not individual vehicle calculations')
    args = parser.parse_args()
    
    try:
        print(f"Fetching vehicles between {args.start_date} and {args.end_date} from {args.db} database...")
        vehicles = get_vehicles_by_date_range(args.start_date, args.end_date, args.db, args.limit)
        
        print(f"Found {len(vehicles)} vehicles in the specified date range.")
        
        if not args.summary_only:
            for i, vehicle in enumerate(vehicles):
                # Override the v_number with the actual index in the list
                vehicle['_index'] = i + 1
                display_margin_calculation(vehicle)
        
        print_summary(vehicles)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 