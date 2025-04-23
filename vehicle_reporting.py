#vehicle_reporting.py

import os
import time
import smtplib
import argparse
import traceback
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta, date
from db_operations import get_vehicle_data


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

def create_html_report(daily_data, weekly_data, monthly_data, 
                      daily_yoy, weekly_yoy, monthly_yoy, location_name, report_date=None):
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
    """
    # Use the specified report date or today's date
    today = report_date if report_date else datetime.now().date()
    month_start = today.replace(day=1)
    last_year = today.replace(year=today.year - 1)
    last_year_month_start = month_start.replace(year=month_start.year - 1)
    
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
                    margin: 8px 0 !important;
                }}
                .stat-grid {{
                    grid-template-columns: 1fr !important;
                }}
            }}
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 12px;
                background-color: #ffffff;
            }}
            .header {{
                text-align: center;
                padding: 12px 0;
                background-color: #e70000;
                color: white;
                border-radius: 6px 6px 0 0;
            }}
            .header h1 {{
                margin: 0;
                font-size: 20px;
                font-weight: 600;
            }}
            .date-range {{
                font-size: 12px;
                color: #ffffff;
                opacity: 0.9;
                margin-top: 4px;
            }}
            .card {{
                background: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin: 12px 0;
                overflow: hidden;
                border: 1px solid #e70000;
            }}
            .card-header {{
                background-color: #e70000;
                padding: 8px 12px;
                border-bottom: 1px solid #e70000;
            }}
            .card-title {{
                margin: 0;
                font-size: 16px;
                color: white;
                font-weight: 600;
            }}
            .card-body {{
                padding: 12px;
            }}
            .stat-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
                margin-bottom: 12px;
            }}
            .stat-item {{
                text-align: center;
                padding: 8px;
                background: #fff;
                border-radius: 4px;
                border: 1px solid #e70000;
            }}
            .stat-value {{
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-bottom: 2px;
            }}
            .stat-label {{
                font-size: 12px;
                color: #666;
            }}
            .payment-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
                margin-bottom: 12px;
            }}
            .payment-item {{
                text-align: center;
                padding: 8px;
                background: #fff;
                border-radius: 4px;
                border: 1px solid #e70000;
            }}
            .payment-count {{
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-bottom: 2px;
            }}
            .payment-value {{
                font-size: 14px;
                color: #333;
                font-weight: 500;
                margin-bottom: 2px;
            }}
            .payment-label {{
                font-size: 12px;
                color: #666;
            }}
            .comparison {{
                background: #fff;
                padding: 8px;
                border-radius: 4px;
                margin-top: 12px;
                border: 1px solid #e70000;
            }}
            .comparison-title {{
                font-size: 14px;
                color: #333;
                margin-bottom: 6px;
                font-weight: 600;
            }}
            .comparison-value {{
                font-size: 12px;
                color: #666;
                margin-bottom: 4px;
            }}
            .comparison-change {{
                font-size: 12px;
                color: #34a853;
                font-weight: 500;
            }}
            .comparison-change.negative {{
                color: #ea4335;
            }}
            .footer {{
                text-align: center;
                padding: 12px;
                color: #666;
                font-size: 11px;
                border-top: 1px solid #e70000;
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
                <div class="card-header">
                    <h2 class="card-title">Penjualan Hari Ini</h2>
                </div>
                <div class="card-body">
                    <div class="stat-grid">
                        <div class="stat-item">
                            <div class="stat-value">{daily_data['summary']['total_units']}</div>
                            <div class="stat-label">Unit Terjual</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{format_currency(daily_data['summary']['total_value'])}</div>
                            <div class="stat-label">Total Nilai</div>
                        </div>
                    </div>
                    
                    <div class="payment-grid">
                        <div class="payment-item">
                            <div class="payment-count">{daily_data['summary']['payment_methods']['tunai']['count']}</div>
                            <div class="payment-value">{format_currency(daily_data['summary']['payment_methods']['tunai']['margin'])}</div>
                            <div class="payment-label">Tunai</div>
                        </div>
                        <div class="payment-item">
                            <div class="payment-count">{daily_data['summary']['payment_methods']['kredit']['count']}</div>
                            <div class="payment-value">{format_currency(daily_data['summary']['payment_methods']['kredit']['margin'])}</div>
                            <div class="payment-label">Kredit</div>
                        </div>
                    </div>
                    
                    <div class="comparison">
                        <div class="comparison-title">Perbandingan dengan {format_date(last_year)}</div>
                        <div class="comparison-value">
                            Tahun lalu: {daily_yoy['last_year_units']} Unit 
                            ({format_currency(daily_yoy['last_year_value'])})
                        </div>
                        <div class="comparison-change {'' if daily_yoy['unit_change'] >= 0 else 'negative'}">
                            Perubahan: {daily_yoy['unit_change']:+d} Unit 
                            ({format_percentage(daily_yoy['unit_change_pct'])})
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Penjualan Bulan Ini</h2>
                </div>
                <div class="card-body">
                    <div class="stat-grid">
                        <div class="stat-item">
                            <div class="stat-value">{monthly_data['summary']['total_units']}</div>
                            <div class="stat-label">Unit Terjual</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{format_currency(monthly_data['summary']['total_value'])}</div>
                            <div class="stat-label">Total Nilai</div>
                        </div>
                    </div>
                    
                    <div class="payment-grid">
                        <div class="payment-item">
                            <div class="payment-count">{monthly_data['summary']['payment_methods']['tunai']['count']}</div>
                            <div class="payment-value">{format_currency(monthly_data['summary']['payment_methods']['tunai']['margin'])}</div>
                            <div class="payment-label">Tunai</div>
                        </div>
                        <div class="payment-item">
                            <div class="payment-count">{monthly_data['summary']['payment_methods']['kredit']['count']}</div>
                            <div class="payment-value">{format_currency(monthly_data['summary']['payment_methods']['kredit']['margin'])}</div>
                            <div class="payment-label">Kredit</div>
                        </div>
                    </div>
                    
                    <div class="comparison">
                        <div class="comparison-title">Perbandingan dengan {format_date(last_year_month_start)} - {format_date(last_year)}</div>
                        <div class="comparison-value">
                            Tahun lalu: {monthly_yoy['last_year_units']} Unit 
                            ({format_currency(monthly_yoy['last_year_value'])})
                        </div>
                        <div class="comparison-change {'' if monthly_yoy['unit_change'] >= 0 else 'negative'}">
                            Perubahan: {monthly_yoy['unit_change']:+d} Unit 
                            ({format_percentage(monthly_yoy['unit_change_pct'])})
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>Laporan ini dibuat secara otomatis pada {current_time}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(subject, body, recipients):
    """Send email to specified recipients."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "marviano.austin@gmail.com"
    app_password = "ktqbdhbktmcdkvuf"

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
    recipients = ["alvusebastian@gmail.com"]
    # recipients = ["alvusebastian@gmail.com", "sony_hendarto@hotmail.com"]
    
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
        
        # Get this week's data and last year comparison
        week_start = today - timedelta(days=today.weekday())
        weekly_data = get_vehicle_data(
            start_date=week_start.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        last_year_week_start = week_start.replace(year=week_start.year - 1)
        weekly_last_year = get_vehicle_data(
            start_date=last_year_week_start.strftime('%Y-%m-%d'),
            end_date=last_year.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        print(f"Data mingguan {location_name} berhasil diambil")
        
        # Get this month's data and last year comparison
        month_start = today.replace(day=1)
        monthly_data = get_vehicle_data(
            start_date=month_start.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        last_year_month_start = month_start.replace(year=month_start.year - 1)
        monthly_last_year = get_vehicle_data(
            start_date=last_year_month_start.strftime('%Y-%m-%d'),
            end_date=last_year.strftime('%Y-%m-%d'),
            database_name=db_name
        ) or {'summary': {'total_units': 0, 'total_value': 0}}
        print(f"Data bulanan {location_name} berhasil diambil")
        
        if all([daily_data, daily_last_year, weekly_data, weekly_last_year, 
                monthly_data, monthly_last_year]):
            
            # Calculate all year-over-year comparisons
            daily_yoy = calculate_yoy_changes(daily_data, daily_last_year)
            weekly_yoy = calculate_yoy_changes(weekly_data, weekly_last_year)
            monthly_yoy = calculate_yoy_changes(monthly_data, monthly_last_year)
            
            html_report = create_html_report(
                daily_data, 
                weekly_data, 
                monthly_data,
                daily_yoy,
                weekly_yoy,
                monthly_yoy,
                location_name,
                report_date=today
            )
            send_email(
                f"{location_name} today, DO: {daily_data['summary']['total_units']}", 
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