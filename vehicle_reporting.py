#vehicle_reporting.py

import os
import time
import smtplib
import argparse
import traceback
import sys
import mysql.connector
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta, date
from db_operations import get_vehicle_data, connect_to_database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def format_currency(amount):
    """Format number to Indonesian Rupiah."""
    return f"Rp {amount:,.0f}"

def format_percentage(value):
    """Format number to percentage with 2 decimal places."""
    return f"{value:+.2f}%" if value != 0 else "0.00%"

def format_date(date):
    """Format date to Indonesian format."""
    months = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    return f"{date.day} {months[date.month]} {date.year}"

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

def get_margin_summary(start_date, end_date, database_name="honda_mis"):
    """
    Get margin summary for a specific date range.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        database_name (str): Database to connect to
    
    Returns:
        dict: Summary of margin data
    """
    conn = connect_to_database(database_name)
    cursor = conn.cursor(dictionary=True)
    
    # Choose the appropriate query based on the database
    if database_name == "honda_mis":
        # Original query for honda_mis
        query = """
        SELECT 
            COUNT(*) as total_vehicles,
            SUM(spk.harga_jual) as total_harga_jual,
            SUM(IFNULL(dor.harga_ppn, 0)) as total_harga_tebus,
            SUM(
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
            ) AS total_margin,
            SUM(CASE WHEN (spk.cara_bayar IS NULL OR spk.cara_bayar != 'KREDIT') THEN 1 ELSE 0 END) as tunai_count,
            SUM(CASE WHEN spk.cara_bayar = 'KREDIT' THEN 1 ELSE 0 END) as kredit_count,
            SUM(CASE WHEN (spk.cara_bayar IS NULL OR spk.cara_bayar != 'KREDIT') THEN 
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
            ELSE 0 END) AS tunai_margin,
            SUM(CASE WHEN spk.cara_bayar = 'KREDIT' THEN 
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
            ELSE 0 END) AS kredit_margin
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
        """
    else:
        # Modified query for m2_magetan and any other database without subs_ahm, main_dealer, and perk_adm_wil
        query = """
        SELECT 
            COUNT(*) as total_vehicles,
            SUM(spk.harga_jual) as total_harga_jual,
            SUM(IFNULL(dor.harga_ppn, 0)) as total_harga_tebus,
            SUM(
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
            ) AS total_margin,
            SUM(CASE WHEN (spk.cara_bayar IS NULL OR spk.cara_bayar != 'KREDIT') THEN 1 ELSE 0 END) as tunai_count,
            SUM(CASE WHEN spk.cara_bayar = 'KREDIT' THEN 1 ELSE 0 END) as kredit_count,
            SUM(CASE WHEN (spk.cara_bayar IS NULL OR spk.cara_bayar != 'KREDIT') THEN 
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
            ELSE 0 END) AS tunai_margin,
            SUM(CASE WHEN spk.cara_bayar = 'KREDIT' THEN 
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
            ELSE 0 END) AS kredit_margin
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
        """
    
    try:
        cursor.execute(query, (start_date, end_date))
        result = cursor.fetchone()
        
        if not result or result['total_vehicles'] == 0:
            return {
                'total_vehicles': 0,
                'total_margin': 0,
                'total_harga_jual': 0,
                'total_harga_tebus': 0,
                'tunai_count': 0,
                'kredit_count': 0,
                'tunai_margin': 0,
                'kredit_margin': 0,
                'average_margin': 0
            }
        
        # Calculate average margin
        average_margin = result['total_margin'] / result['total_vehicles'] if result['total_vehicles'] > 0 else 0
        
        return {
            'total_vehicles': result['total_vehicles'],
            'total_margin': result['total_margin'] or 0,
            'total_harga_jual': result['total_harga_jual'] or 0,
            'total_harga_tebus': result['total_harga_tebus'] or 0,
            'tunai_count': result['tunai_count'] or 0,
            'kredit_count': result['kredit_count'] or 0,
            'tunai_margin': result['tunai_margin'] or 0,
            'kredit_margin': result['kredit_margin'] or 0,
            'average_margin': average_margin
        }
        
    except mysql.connector.Error as err:
        print(f"Database error in get_margin_summary: {err}")
        return {
            'total_vehicles': 0,
            'total_margin': 0,
            'total_harga_jual': 0,
            'total_harga_tebus': 0,
            'tunai_count': 0,
            'kredit_count': 0,
            'tunai_margin': 0,
            'kredit_margin': 0,
            'average_margin': 0
        }
    finally:
        cursor.close()
        conn.close()

def calculate_margin_changes(current_margin, last_period_margin):
    """Calculate margin changes between current and last period."""
    if not current_margin or not last_period_margin:
        return {
            'margin_change': 0,
            'margin_change_pct': 0,
            'vehicles_change': 0,
            'vehicles_change_pct': 0,
            'last_period_margin': 0,
            'last_period_vehicles': 0
        }
    
    current_total_margin = current_margin['total_margin']
    current_vehicles = current_margin['total_vehicles']
    last_period_total_margin = last_period_margin['total_margin']
    last_period_vehicles = last_period_margin['total_vehicles']
    
    margin_change = current_total_margin - last_period_total_margin
    margin_change_pct = ((current_total_margin / last_period_total_margin) - 1) * 100 if last_period_total_margin > 0 else 0
    
    vehicles_change = current_vehicles - last_period_vehicles
    vehicles_change_pct = ((current_vehicles / last_period_vehicles) - 1) * 100 if last_period_vehicles > 0 else 0
    
    return {
        'margin_change': margin_change,
        'margin_change_pct': margin_change_pct,
        'vehicles_change': vehicles_change,
        'vehicles_change_pct': vehicles_change_pct,
        'last_period_margin': last_period_total_margin,
        'last_period_vehicles': last_period_vehicles
    }

def calculate_yoy_changes(current_data, last_year_data):
    if not current_data or not last_year_data:
        return {
            'unit_change': 0,
            'unit_change_pct': 0,
            'value_change': 0,
            'value_change_pct': 0,
            'last_year_units': 0,
            'last_year_value': 0
        }
    
    current_units = current_data['summary']['total_units'] if current_data and current_data['summary']['total_units'] else 0
    current_value = current_data['summary']['total_value'] if current_data and current_data['summary']['total_value'] else 0
    last_year_units = last_year_data['summary']['total_units'] if last_year_data and last_year_data['summary']['total_units'] else 0
    last_year_value = last_year_data['summary']['total_value'] if last_year_data and last_year_data['summary']['total_value'] else 0
    
    unit_change = current_units - last_year_units
    unit_change_pct = ((current_units / last_year_units) - 1) * 100 if last_year_units > 0 else 0
    
    value_change = current_value - last_year_value
    value_change_pct = ((current_value / last_year_value) - 1) * 100 if last_year_value > 0 else 0
    
    return {
        'unit_change': unit_change,
        'unit_change_pct': unit_change_pct,
        'value_change': value_change,
        'value_change_pct': value_change_pct,
        'last_year_units': last_year_units,
        'last_year_value': last_year_value
    }

def calculate_mom_changes(current_data, last_month_data):
    if not current_data or not last_month_data:
        return {
            'unit_change': 0,
            'unit_change_pct': 0,
            'value_change': 0,
            'value_change_pct': 0,
            'last_month_units': 0,
            'last_month_value': 0
        }
    
    current_units = current_data['summary']['total_units'] if current_data and current_data['summary']['total_units'] else 0
    current_value = current_data['summary']['total_value'] if current_data and current_data['summary']['total_value'] else 0
    last_month_units = last_month_data['summary']['total_units'] if last_month_data and last_month_data['summary']['total_units'] else 0
    last_month_value = last_month_data['summary']['total_value'] if last_month_data and last_month_data['summary']['total_value'] else 0
    
    unit_change = current_units - last_month_units
    unit_change_pct = ((current_units / last_month_units) - 1) * 100 if last_month_units > 0 else 0
    
    value_change = current_value - last_month_value
    value_change_pct = ((current_value / last_month_value) - 1) * 100 if last_month_value > 0 else 0
    
    return {
        'unit_change': unit_change,
        'unit_change_pct': unit_change_pct,
        'value_change': value_change,
        'value_change_pct': value_change_pct,
        'last_month_units': last_month_units,
        'last_month_value': last_month_value
    }

def create_html_report(daily_data, weekly_data, monthly_data, 
                      daily_yoy, weekly_yoy, monthly_yoy, location_name, report_date=None, 
                      daily_mom=None, monthly_mom=None, daily_margin=None, monthly_margin=None,
                      daily_margin_yoy=None, daily_margin_mom=None, monthly_margin_yoy=None, monthly_margin_mom=None):
    """Create HTML formatted report showing daily and monthly data with YoY comparison and payment methods.
    
    Args:
        daily_data: Data for the specific day
        weekly_data: Data for the week (not used)
        monthly_data: Data for the month
        daily_yoy: Year-over-year comparison for the day
        weekly_yoy: Year-over-year comparison for the week (not used)
        monthly_yoy: Year-over-year comparison for the month
        location_name: Name of the location (e.g., "M2 Madiun" or "M2 Magetan")
        report_date: Specific date for the report (default: current date)
        daily_mom: Day-over-month comparison data (same date last month)
        monthly_mom: Month-over-month comparison data (YTD)
        daily_margin: Margin data for the specific day
        monthly_margin: Margin data for the month
        daily_margin_yoy: Year-over-year comparison for the day's margin
        daily_margin_mom: Day-over-month comparison for the day's margin
        monthly_margin_yoy: Year-over-year comparison for the month's margin
        monthly_margin_mom: Month-over-month comparison for the month's margin
    """
    # Use the specified report date or today's date
    today = report_date if report_date else datetime.now().date()
    month_start = today.replace(day=1)
    last_year = today.replace(year=today.year - 1)
    last_year_month_start = month_start.replace(year=month_start.year - 1)
    
    # Calculate last month's same date
    last_month = today.replace(day=1) - timedelta(days=1)
    last_month = last_month.replace(day=min(today.day, last_month.day))
    
    current_time = datetime.now().strftime("%H:%M:%S")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @media only screen and (max-width: 600px) {{
                .container {{
                    width: 100% !important;
                    padding: 8px !important;
                }}
                .card {{
                    margin: 6px 0 !important;
                }}
                .stats-row {{
                    grid-template-columns: 1fr !important;
                    gap: 8px !important;
                }}
                .comparison-row {{
                    grid-template-columns: 1fr !important;
                    gap: 6px !important;
                }}
                .payment-row {{
                    grid-template-columns: 1fr 1fr !important;
                    gap: 8px !important;
                }}
            }}
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #f5f5f5;
                color: #333;
                line-height: 1.3;
            }}
            .container {{
                max-width: 650px;
                margin: 0 auto;
                padding: 10px;
                background-color: #ffffff;
            }}
            .header {{
                text-align: center;
                padding: 15px 0;
                background: linear-gradient(135deg, #e70000, #c60000);
                color: white;
                border-radius: 10px 10px 0 0;
                box-shadow: 0 3px 6px rgba(0,0,0,0.15);
            }}
            .header h1 {{
                margin: 0;
                font-size: 22px;
                font-weight: 700;
            }}
            .date-range {{
                font-size: 14px;
                color: #ffffff;
                opacity: 0.95;
                margin-top: 5px;
            }}
            .card {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 3px 8px rgba(0,0,0,0.1);
                margin: 10px 0;
                overflow: hidden;
                border: 1px solid #ddd;
            }}
            .card-header.do-section {{
                background: linear-gradient(135deg, #1976d2, #1565c0);
                color: white;
                padding: 12px 15px;
            }}
            .card-header.margin-section {{
                background: linear-gradient(135deg, #388e3c, #2e7d32);
                color: white;
                padding: 12px 15px;
            }}
            .card-title {{
                margin: 0;
                font-size: 18px;
                font-weight: 600;
            }}
            .card-body {{
                padding: 15px;
            }}
            .stats-row {{
                display: table;
                width: 100%;
                margin-bottom: 15px;
            }}
            .stat-box {{
                display: table-cell;
                width: 50%;
                text-align: center;
                padding: 15px 10px;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 8px;
                border: 1px solid #dee2e6;
                vertical-align: top;
            }}
            .stat-box:first-child {{
                margin-right: 6px;
            }}
            .stat-box:last-child {{
                margin-left: 6px;
            }}
            .stat-value {{
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }}
            .stat-label {{
                font-size: 14px;
                color: #666;
                font-weight: 500;
            }}
            .payment-row {{
                display: table;
                width: 100%;
                margin-bottom: 15px;
            }}
            .payment-box {{
                display: table-cell;
                width: 50%;
                text-align: center;
                padding: 12px;
                background: #fff;
                border-radius: 8px;
                border: 2px solid #e9ecef;
                vertical-align: top;
            }}
            .payment-box:first-child {{
                margin-right: 6px;
            }}
            .payment-box:last-child {{
                margin-left: 6px;
            }}
            .payment-count {{
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 4px;
            }}
            .payment-value {{
                font-size: 14px;
                color: #333;
                font-weight: 500;
                margin-bottom: 4px;
            }}
            .payment-label {{
                font-size: 13px;
                color: #666;
                font-weight: 500;
            }}
            .comparison-row {{
                display: table;
                width: 100%;
                margin-top: 15px;
            }}
            .comparison-box {{
                display: table-cell;
                width: 50%;
                background: #f8f9fa;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #e9ecef;
                vertical-align: top;
                text-align: center;
            }}
            .comparison-box:first-child {{
                margin-right: 6px;
            }}
            .comparison-box:last-child {{
                margin-left: 6px;
            }}
            .comparison-title {{
                font-size: 14px;
                color: #333;
                margin-bottom: 6px;
                font-weight: 600;
            }}
            .comparison-content {{
                font-size: 12px;
                color: #666;
                margin-bottom: 4px;
            }}
            .comparison-change {{
                font-size: 13px;
                color: #28a745;
                font-weight: 600;
            }}
            .comparison-change.negative {{
                color: #dc3545;
            }}
            .footer {{
                text-align: center;
                padding: 12px;
                color: #666;
                font-size: 12px;
                border-top: 1px solid #ddd;
                background: #f8f9fa;
                border-radius: 0 0 10px 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{location_name}</h1>
                <div class="date-range">{format_date(today)}</div>
            </div>
            
            <div class="card">
                <div class="card-header do-section">
                    <h2 class="card-title">📊 Penjualan Hari Ini</h2>
                </div>
                <div class="card-body">
                    <div class="stats-row">
                        <div class="stat-box">
                            <div class="stat-value">{daily_data['summary']['total_units']}</div>
                            <div class="stat-label">Unit Terjual</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{format_currency(daily_data['summary']['total_value'])}</div>
                            <div class="stat-label">Total Harga Beli</div>
                        </div>
                    </div>
                    
                    <div class="payment-row">
                        <div class="payment-box">
                            <div class="payment-count">{daily_data['summary']['payment_methods']['tunai']['count']} Unit</div>
                            <div class="payment-value">Margin: {format_currency(daily_data['summary']['payment_methods']['tunai']['margin'])}</div>
                            <div class="payment-label">💰 Tunai</div>
                        </div>
                        <div class="payment-box">
                            <div class="payment-count">{daily_data['summary']['payment_methods']['kredit']['count']} Unit</div>
                            <div class="payment-value">Margin: {format_currency(daily_data['summary']['payment_methods']['kredit']['margin'])}</div>
                            <div class="payment-label">💳 Kredit</div>
                        </div>
                    </div>
                    
                    <div class="comparison-row">
                        <div class="comparison-box">
                            <div class="comparison-title">📈 vs Tahun Lalu</div>
                            <div class="comparison-content">
                                {daily_yoy['last_year_units']} Unit (Harga Beli: {format_currency(daily_yoy['last_year_value'])})
                            </div>
                            <div class="comparison-change {'' if daily_yoy['unit_change'] >= 0 else 'negative'}">
                                {daily_yoy['unit_change']:+d} Unit ({format_percentage(daily_yoy['unit_change_pct'])})
                            </div>
                        </div>
                        <div class="comparison-box">
                            <div class="comparison-title">📅 vs Bulan Lalu</div>
                            <div class="comparison-content">
                                {daily_mom['last_month_units']} Unit (Harga Beli: {format_currency(daily_mom['last_month_value'])})
                            </div>
                            <div class="comparison-change {'' if daily_mom['unit_change'] >= 0 else 'negative'}">
                                {daily_mom['unit_change']:+d} Unit ({format_percentage(daily_mom['unit_change_pct'])})
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header do-section">
                    <h2 class="card-title">📊 Penjualan Bulan Ini</h2>
                </div>
                <div class="card-body">
                    <div class="stats-row">
                        <div class="stat-box">
                            <div class="stat-value">{monthly_data['summary']['total_units']}</div>
                            <div class="stat-label">Unit Terjual</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{format_currency(monthly_data['summary']['total_value'])}</div>
                            <div class="stat-label">Total Harga Beli</div>
                        </div>
                    </div>
                    
                    <div class="payment-row">
                        <div class="payment-box">
                            <div class="payment-count">{monthly_data['summary']['payment_methods']['tunai']['count']} Unit</div>
                            <div class="payment-value">Margin: {format_currency(monthly_data['summary']['payment_methods']['tunai']['margin'])}</div>
                            <div class="payment-label">💰 Tunai</div>
                        </div>
                        <div class="payment-box">
                            <div class="payment-count">{monthly_data['summary']['payment_methods']['kredit']['count']} Unit</div>
                            <div class="payment-value">Margin: {format_currency(monthly_data['summary']['payment_methods']['kredit']['margin'])}</div>
                            <div class="payment-label">💳 Kredit</div>
                        </div>
                    </div>
                    
                    <div class="comparison-row">
                        <div class="comparison-box">
                            <div class="comparison-title">📈 vs Tahun Lalu</div>
                            <div class="comparison-content">
                                {monthly_yoy['last_year_units']} Unit (Harga Beli: {format_currency(monthly_yoy['last_year_value'])})
                            </div>
                            <div class="comparison-change {'' if monthly_yoy['unit_change'] >= 0 else 'negative'}">
                                {monthly_yoy['unit_change']:+d} Unit ({format_percentage(monthly_yoy['unit_change_pct'])})
                            </div>
                        </div>
                        <div class="comparison-box">
                            <div class="comparison-title">📅 vs Bulan Lalu</div>
                            <div class="comparison-content">
                                {monthly_mom['last_month_units']} Unit (Harga Beli: {format_currency(monthly_mom['last_month_value'])})
                            </div>
                            <div class="comparison-change {'' if monthly_mom['unit_change'] >= 0 else 'negative'}">
                                {monthly_mom['unit_change']:+d} Unit ({format_percentage(monthly_mom['unit_change_pct'])})
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {f'''
            <div class="card">
                <div class="card-header margin-section">
                    <h2 class="card-title">💰 Keuntungan Hari Ini</h2>
                </div>
                <div class="card-body">
                    <div class="stats-row">
                        <div class="stat-box">
                            <div class="stat-value">{daily_margin['total_vehicles']}</div>
                            <div class="stat-label">Unit Terjual</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{format_currency(daily_margin['total_margin'])}</div>
                            <div class="stat-label">Total Keuntungan</div>
                        </div>
                    </div>
                    
                    <div class="payment-row">
                        <div class="payment-box">
                            <div class="payment-count">{daily_margin['tunai_count']} Unit</div>
                            <div class="payment-value">{format_currency(daily_margin['tunai_margin'])}</div>
                            <div class="payment-label">💰 Keuntungan Tunai</div>
                        </div>
                        <div class="payment-box">
                            <div class="payment-count">{daily_margin['kredit_count']} Unit</div>
                            <div class="payment-value">{format_currency(daily_margin['kredit_margin'])}</div>
                            <div class="payment-label">💳 Keuntungan Kredit</div>
                        </div>
                    </div>
                    
                    <div class="comparison-row">
                        <div class="comparison-box">
                            <div class="comparison-title">📈 vs Tahun Lalu</div>
                            <div class="comparison-content">
                                {daily_margin_yoy['last_period_vehicles']} Unit (Keuntungan: {format_currency(daily_margin_yoy['last_period_margin'])})
                            </div>
                            <div class="comparison-change {'' if daily_margin_yoy['margin_change'] >= 0 else 'negative'}">
                                {format_currency(daily_margin_yoy['margin_change'])} ({format_percentage(daily_margin_yoy['margin_change_pct'])})
                            </div>
                        </div>
                        <div class="comparison-box">
                            <div class="comparison-title">📅 vs Bulan Lalu</div>
                            <div class="comparison-content">
                                {daily_margin_mom['last_period_vehicles']} Unit (Keuntungan: {format_currency(daily_margin_mom['last_period_margin'])})
                            </div>
                            <div class="comparison-change {'' if daily_margin_mom['margin_change'] >= 0 else 'negative'}">
                                {format_currency(daily_margin_mom['margin_change'])} ({format_percentage(daily_margin_mom['margin_change_pct'])})
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header margin-section">
                    <h2 class="card-title">💰 Keuntungan Bulan Ini</h2>
                </div>
                <div class="card-body">
                    <div class="stats-row">
                        <div class="stat-box">
                            <div class="stat-value">{monthly_margin['total_vehicles']}</div>
                            <div class="stat-label">Unit Terjual</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{format_currency(monthly_margin['total_margin'])}</div>
                            <div class="stat-label">Total Keuntungan</div>
                        </div>
                    </div>
                    
                    <div class="payment-row">
                        <div class="payment-box">
                            <div class="payment-count">{monthly_margin['tunai_count']} Unit</div>
                            <div class="payment-value">{format_currency(monthly_margin['tunai_margin'])}</div>
                            <div class="payment-label">💰 Keuntungan Tunai</div>
                        </div>
                        <div class="payment-box">
                            <div class="payment-count">{monthly_margin['kredit_count']} Unit</div>
                            <div class="payment-value">{format_currency(monthly_margin['kredit_margin'])}</div>
                            <div class="payment-label">💳 Keuntungan Kredit</div>
                        </div>
                    </div>
                    
                    <div class="comparison-row">
                        <div class="comparison-box">
                            <div class="comparison-title">📈 vs Tahun Lalu</div>
                            <div class="comparison-content">
                                {monthly_margin_yoy['last_period_vehicles']} Unit (Keuntungan: {format_currency(monthly_margin_yoy['last_period_margin'])})
                            </div>
                            <div class="comparison-change {'' if monthly_margin_yoy['margin_change'] >= 0 else 'negative'}">
                                {format_currency(monthly_margin_yoy['margin_change'])} ({format_percentage(monthly_margin_yoy['margin_change_pct'])})
                            </div>
                        </div>
                        <div class="comparison-box">
                            <div class="comparison-title">📅 vs Bulan Lalu</div>
                            <div class="comparison-content">
                                {monthly_margin_mom['last_period_vehicles']} Unit (Keuntungan: {format_currency(monthly_margin_mom['last_period_margin'])})
                            </div>
                            <div class="comparison-change {'' if monthly_margin_mom['margin_change'] >= 0 else 'negative'}">
                                {format_currency(monthly_margin_mom['margin_change'])} ({format_percentage(monthly_margin_mom['margin_change_pct'])})
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ''' if daily_margin and monthly_margin else ''}
            
            <div class="footer">
                <p>Laporan dibuat otomatis pada {current_time}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(subject, body, recipients):
    """Send email to specified recipients."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("SENDER_PASSWORD")

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["Subject"] = subject
    message["To"] = ", ".join(recipients)
    
    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(message)
        print(f"Email berhasil dikirim ke {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"Error mengirim email: {e}")
        return False

def process_location_data(db_name, location_name, specific_date=None):
    """
    Process data for a specific location (database) and generate a report.
    
    Args:
        db_name (str): Database name to use
        location_name (str): Name of the location for the report title
        specific_date (date, optional): Specific date for the report. Defaults to None (current date).
    """
    # Get recipients from environment variables
    recipients_str = os.getenv("EMAIL_RECIPIENTS", "")
    recipients = [email.strip() for email in recipients_str.split(",") if email.strip()]
    
    try:
        # Use the provided date or today's date
        today = specific_date if specific_date else datetime.now().date()
        print(f"Mengambil data untuk {location_name} tanggal {format_date(today)}")
        
        # Get today's data and last year comparison
        daily_data = get_vehicle_data(
            start_date=today.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}

        last_year = today.replace(year=today.year - 1)
        daily_last_year = get_vehicle_data(
            start_date=last_year.strftime('%Y-%m-%d'),
            end_date=last_year.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        print(f"Data harian {location_name} berhasil diambil")
        
        # Get last month's same date data
        last_month = today.replace(day=1) - timedelta(days=1)
        last_month = last_month.replace(day=min(today.day, last_month.day))
        daily_last_month = get_vehicle_data(
            start_date=last_month.strftime('%Y-%m-%d'),
            end_date=last_month.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        
        # Get this month's data and last month YTD comparison
        month_start = today.replace(day=1)
        monthly_data = get_vehicle_data(
            start_date=month_start.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        
        # Get last month's YTD data
        last_month_start = last_month.replace(day=1)
        last_month_end = last_month
        monthly_last_month = get_vehicle_data(
            start_date=last_month_start.strftime('%Y-%m-%d'),
            end_date=last_month_end.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        
        # Get last year's monthly data
        last_year_month_start = month_start.replace(year=month_start.year - 1)
        monthly_last_year = get_vehicle_data(
            start_date=last_year_month_start.strftime('%Y-%m-%d'),
            end_date=last_year.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        
        # Get margin data for today
        daily_margin = get_margin_summary(
            today.strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d'),
            db_name
        )
        
        # Get margin data for last year same date
        daily_margin_last_year = get_margin_summary(
            last_year.strftime('%Y-%m-%d'),
            last_year.strftime('%Y-%m-%d'),
            db_name
        )
        
        # Get margin data for last month same date
        daily_margin_last_month = get_margin_summary(
            last_month.strftime('%Y-%m-%d'),
            last_month.strftime('%Y-%m-%d'),
            db_name
        )
        
        # Get margin data for this month
        monthly_margin = get_margin_summary(
            month_start.strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d'),
            db_name
        )
        
        # Get margin data for last month YTD
        monthly_margin_last_month = get_margin_summary(
            last_month_start.strftime('%Y-%m-%d'),
            last_month_end.strftime('%Y-%m-%d'),
            db_name
        )
        
        # Get margin data for last year monthly
        monthly_margin_last_year = get_margin_summary(
            last_year_month_start.strftime('%Y-%m-%d'),
            last_year.strftime('%Y-%m-%d'),
            db_name
        )
        
        print(f"Data margin {location_name} berhasil diambil")
        
        if all([daily_data, daily_last_year, daily_last_month, monthly_data, monthly_last_month, monthly_last_year]):
            
            # Calculate all comparisons
            daily_yoy = calculate_yoy_changes(daily_data, daily_last_year)
            daily_mom = calculate_mom_changes(daily_data, daily_last_month)
            monthly_yoy = calculate_yoy_changes(monthly_data, monthly_last_year)
            monthly_mom = calculate_mom_changes(monthly_data, monthly_last_month)
            
            # Calculate margin comparisons
            daily_margin_yoy = calculate_margin_changes(daily_margin, daily_margin_last_year)
            daily_margin_mom = calculate_margin_changes(daily_margin, daily_margin_last_month)
            monthly_margin_yoy = calculate_margin_changes(monthly_margin, monthly_margin_last_year)
            monthly_margin_mom = calculate_margin_changes(monthly_margin, monthly_margin_last_month)
            
            html_report = create_html_report(
                daily_data, 
                None,  # weekly data not used
                monthly_data,
                daily_yoy,
                None,  # weekly yoy not used
                monthly_yoy,
                location_name,
                report_date=today,
                daily_mom=daily_mom,
                monthly_mom=monthly_mom,
                daily_margin=daily_margin,
                monthly_margin=monthly_margin,
                daily_margin_yoy=daily_margin_yoy,
                daily_margin_mom=daily_margin_mom,
                monthly_margin_yoy=monthly_margin_yoy,
                monthly_margin_mom=monthly_margin_mom
            )
            send_email(
                f"M2 | {location_name} today, DO: {daily_data['summary']['total_units']}, Margin: {format_currency(daily_margin['total_margin'])}",
                html_report,
                recipients
            )
            print(f"Laporan {location_name} untuk tanggal {format_date(today)} berhasil dikirim")
            return True
        else:
            print(f"Tidak ada data untuk {location_name} untuk ditampilkan")
            return False
    
    except Exception as e:
        print(f"Terjadi kesalahan pada {location_name}: {e}")
        print(traceback.format_exc())
        return False

def main(specific_date=None):
    """
    Generate and send sales reports for both databases for a specific date or today if no date is provided.
    
    Args:
        specific_date (date, optional): Specific date for the report. Defaults to None (current date).
    """
    # Process data for M2 Madiun
    process_location_data("honda_mis", "M2 Madiun", specific_date)
    
    # Process data for M2 Magetan
    process_location_data("m2_magetan", "M2 Magetan", specific_date)

if __name__ == "__main__":
    # Use argparse for command line arguments
    parser = argparse.ArgumentParser(description='Generate and send vehicle sales report')
    parser.add_argument('date', nargs='?', help='Report date in DDMMYYYY format (e.g., 24022025)')
    args = parser.parse_args()
    
    try:
        if args.date:
            # Parse command line date argument
            day = int(args.date[0:2])
            month = int(args.date[2:4])
            year = int(args.date[4:8])
            target_date = date(year, month, day)
            print(f"Mengirim laporan untuk tanggal {day} {['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'][month-1]} {year}...")
            main(specific_date=target_date)
        else:
            # Use current date if no date provided
            print("Mengirim laporan untuk hari ini...")
            main()
        print("Selesai!")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Contoh penggunaan: python {os.path.basename(sys.argv[0])} 24022025")
        sys.exit(1)