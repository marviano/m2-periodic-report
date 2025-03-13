#db_operations.py

import mysql.connector
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

def connect_to_database(database_name="honda_mis"):
    """Establish connection to the MySQL database.
    
    Args:
        database_name (str): Name of the database to connect to. Default is "honda_mis".
    """
    return mysql.connector.connect(
        host="36.74.102.231",
        user="honda_mis",
        password="mcMotor",
        database=database_name
    )

def get_vehicle_data(start_date: str, end_date: str, database_name="honda_mis") -> Dict[str, Any]:
    """
    Retrieve vehicle data from database for the specified date range.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        database_name (str): Name of the database to connect to. Default is "honda_mis".
    """
    conn = connect_to_database(database_name)
    cursor = conn.cursor(dictionary=True)
    
    # Choose the appropriate query based on the database
    if database_name == "honda_mis":
        # Original query for honda_mis
        vehicle_query = """
        SELECT 
            bast.kode_bast, 
            bast.tgl_bast,
            spk.no_form_spk,
            spk.cara_bayar,
            mp.nama_pelanggan,
            spk.kode_finance,
            mf.nama_finance,
            spk.tenor,
            mb.kode_warna_lengkap,
            mb.nama_lengkap,
            bast.no_rangka,
            bast.no_mesin,
            mk_sales.nama_karyawan AS nama_sales,
            mk_spv.nama_karyawan AS nama_spv,
            spk.harga_jual,
            IFNULL(dor.harga_ppn, 0) AS harga_tebus,
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
        LEFT JOIN tbl_data_induk_finance AS mf 
            ON spk.kode_finance = mf.kode_finance 
        INNER JOIN vi_data_induk_barang_motor AS mb 
            ON spk.kendaraan_warna_id = mb.data_id 
        INNER JOIN tbl_data_induk_pelanggan AS mp 
            ON spk.kode_pelanggan_faktur = mp.pelanggan_id 
        INNER JOIN tbl_data_induk_karyawan AS mk_sales 
            ON spk.sales = mk_sales.nik 
        INNER JOIN tbl_data_induk_karyawan AS mk_spv 
            ON spk.supervisor = mk_spv.nik 
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
    else:
        # Modified query for m2_magetan and any other database without subs_ahm and main_dealer
        vehicle_query = """
        SELECT 
            bast.kode_bast, 
            bast.tgl_bast,
            spk.no_form_spk,
            spk.cara_bayar,
            mp.nama_pelanggan,
            spk.kode_finance,
            mf.nama_finance,
            spk.tenor,
            mb.kode_warna_lengkap,
            mb.nama_lengkap,
            bast.no_rangka,
            bast.no_mesin,
            mk_sales.nama_karyawan AS nama_sales,
            mk_spv.nama_karyawan AS nama_spv,
            spk.harga_jual,
            IFNULL(dor.harga_ppn, 0) AS harga_tebus,
            (
                spk.harga_jual - (
                    IFNULL(dor.harga_ppn, 0) + 
                    spk.diskon + 
                    spk.nota_kredit + 
                    spk.komisi_makelar +
                    IFNULL(pl.dp_gross, 0) - 
                    0 - /* Replace pl.subs_ahm with 0 */
                    0 - /* Replace pl.main_dealer with 0 */
                    IFNULL(mb.perk_notice, 0) +
                    (spk.um_t_leasing - spk.uang_muka + spk.komisi_makelar_leasing) - 
                    spk.promo_pusat
                ) - 0 + spk.saving /* Replace spk.perk_adm_wil with 0 */
            ) AS margin_unit
        FROM tbl_spk AS spk 
        INNER JOIN tbl_bast AS bast 
            ON bast.kode_spk = spk.kode_spk 
        LEFT JOIN tbl_data_induk_finance AS mf 
            ON spk.kode_finance = mf.kode_finance 
        INNER JOIN vi_data_induk_barang_motor AS mb 
            ON spk.kendaraan_warna_id = mb.data_id 
        INNER JOIN tbl_data_induk_pelanggan AS mp 
            ON spk.kode_pelanggan_faktur = mp.pelanggan_id 
        INNER JOIN tbl_data_induk_karyawan AS mk_sales 
            ON spk.sales = mk_sales.nik 
        INNER JOIN tbl_data_induk_karyawan AS mk_spv 
            ON spk.supervisor = mk_spv.nik 
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
        # Get vehicle data
        cursor.execute(vehicle_query, (start_date, end_date))
        results = cursor.fetchall()
        
        if not results:
            empty_summary = {
                'total_units': 0,
                'total_value': 0,
                'total_margin': 0,
                'average_margin': 0,
                'margin_percentage': 0,
                'models_count': {},
                'daily_stats': {},
                'payment_methods': {
                    'tunai': {'count': 0, 'margin': 0},
                    'kredit': {'count': 0, 'margin': 0}
                }
            }
            return {'data': [], 'summary': empty_summary}

        # Calculate summary statistics
        total_units = len(results)
        total_value = sum(float(row['harga_tebus'] or 0) for row in results)
        total_margin = sum(float(row['margin_unit'] or 0) for row in results)
        
        # Calculate payment method statistics
        payment_stats = {
            'tunai': {'count': 0, 'margin': 0},
            'kredit': {'count': 0, 'margin': 0}
        }
        
        for row in results:
            payment_type = row['cara_bayar'].lower() if row['cara_bayar'] else 'tunai'
            if payment_type in payment_stats:
                payment_stats[payment_type]['count'] += 1
                payment_stats[payment_type]['margin'] += float(row['margin_unit'] or 0)
        
        # Create summary
        summary = {
            'total_units': total_units,
            'total_value': total_value,
            'total_margin': total_margin,
            'average_margin': total_margin / total_units if total_units > 0 else 0,
            'margin_percentage': (total_margin / total_value * 100) if total_value > 0 else 0,
            'models_count': {},
            'daily_stats': {},
            'payment_methods': payment_stats
        }

        return {
            'data': results,
            'summary': summary
        }
        
    except mysql.connector.Error as err:
        print(f"Database error ({database_name}): {err}")
        return {
            'data': [],
            'summary': {
                'total_units': 0,
                'total_value': 0,
                'total_margin': 0,
                'average_margin': 0,
                'margin_percentage': 0,
                'models_count': {},
                'daily_stats': {},
                'payment_methods': {
                    'tunai': {'count': 0, 'margin': 0},
                    'kredit': {'count': 0, 'margin': 0}
                }
            }
        }
    finally:
        cursor.close()
        conn.close()