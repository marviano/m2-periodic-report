import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from db_operations import get_spv_performance
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def format_date_id(date_str):
    """Format date string to Indonesian format (e.g., '01 Januari 2025')."""
    months = {
        '01': 'Januari', '02': 'Februari', '03': 'Maret', '04': 'April',
        '05': 'Mei', '06': 'Juni', '07': 'Juli', '08': 'Agustus',
        '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Desember'
    }
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day = str(date_obj.day)
        month = months[date_obj.strftime('%m')]
        year = str(date_obj.year)
        return f"{day} {month} {year}"
    except:
        return date_str

def format_spv_report(spv_data, start_date, end_date):
    """Format SPV performance data into HTML report."""
    # Format dates to Indonesian format
    start_date_id = format_date_id(start_date)
    end_date_id = format_date_id(end_date)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 10px;
                background-color: #f8f9fa;
            }}
            .header {{
                text-align: center;
                color: #e70000;
                margin-bottom: 15px;
            }}
            .header h1 {{
                font-size: 18px;
                margin: 0;
                padding: 0;
            }}
            .header .date-range {{
                font-size: 14px;
                color: #666;
                margin-top: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 0 auto;
                background-color: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }}
            th {{
                background-color: #e70000;
                color: white;
                padding: 10px 8px;
                text-align: center;
                font-size: 12px;
                font-weight: bold;
                border-right: 1px solid #c60000;
            }}
            td {{
                padding: 8px 6px;
                text-align: center;
                border-bottom: 1px solid #e9ecef;
                border-right: 1px solid #e9ecef;
                font-size: 12px;
            }}
            /* Alternating row colors */
            tbody tr:nth-child(odd) {{
                background-color: #ffffff;
            }}
            tbody tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            tbody tr:hover {{
                background-color: #e3f2fd !important;
                transition: background-color 0.3s ease;
            }}
            .spv-name {{
                text-align: left;
                font-weight: bold;
                color: #e70000;
                min-width: 150px;
                border-right: 3px solid #e70000 !important;
                background-color: #fff5f5 !important;
            }}
            /* Column group background colors - ODD ROWS (Light colors) */
            tbody tr:nth-child(odd) .mtd-group {{
                background-color: #e8f5e8 !important; /* Light green */
            }}
            tbody tr:nth-child(odd) .ytd-group {{
                background-color: #e3f2fd !important; /* Light blue */
            }}
            tbody tr:nth-child(odd) .today-group {{
                background-color: #fff8e1 !important; /* Light yellow */
            }}
            tbody tr:nth-child(odd) .spv-name {{
                background-color: #ffebee !important; /* Light red */
            }}
            
            /* Column group background colors - EVEN ROWS (Darker colors) */
            tbody tr:nth-child(even) .mtd-group {{
                background-color: #c8e6c9 !important; /* Darker green */
            }}
            tbody tr:nth-child(even) .ytd-group {{
                background-color: #bbdefb !important; /* Darker blue */
            }}
            tbody tr:nth-child(even) .today-group {{
                background-color: #fff3c4 !important; /* Darker yellow */
            }}
            tbody tr:nth-child(even) .spv-name {{
                background-color: #ffcdd2 !important; /* Darker red */
            }}
            .today-change {{
                color: #2e7d32;
                font-weight: bold;
            }}
            /* Dividers between column groups */
            .today-divider {{
                border-right: 3px solid #333 !important;
            }}
            .mtd-divider {{
                border-right: 3px solid #333 !important;
            }}
            .ytd-divider {{
                border-right: 3px solid #333 !important;
            }}
            .header-today {{
                border-right: 3px solid #c60000 !important;
                background-color: #c60000 !important;
            }}
            .header-mtd {{
                border-right: 3px solid #c60000 !important;
                background-color: #c60000 !important;
            }}
            .header-ytd {{
                border-right: 3px solid #c60000 !important;
                background-color: #c60000 !important;
            }}
            /* Header group colors */
            .header-mtd-sub {{
                background-color: #2e7d32 !important;
            }}
            .header-ytd-sub {{
                background-color: #1565c0 !important;
            }}
            .header-today-sub {{
                background-color: #f57c00 !important;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SPV DO Report</h1>
            <div class="date-range">{start_date_id} ~ {end_date_id}</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th rowspan="2" class="spv-name">SPV</th>
                    <th colspan="3" class="header-today">Today</th>
                    <th colspan="3" class="header-mtd">MTD</th>
                    <th colspan="3" class="header-ytd">YTD</th>
                </tr>
                <tr>
                    <th class="header-today-sub">Madiun</th>
                    <th class="header-today-sub">Magetan</th>
                    <th class="header-today-sub today-divider">Total</th>
                    <th class="header-mtd-sub">Madiun</th>
                    <th class="header-mtd-sub">Magetan</th>
                    <th class="header-mtd-sub mtd-divider">Total</th>
                    <th class="header-ytd-sub">Madiun</th>
                    <th class="header-ytd-sub">Magetan</th>
                    <th class="header-ytd-sub">Total</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Combine SPVs with same name and sum their DO counts
    # Use more robust name normalization to handle variations
    combined_spvs = {}
    for spv in spv_data['data']:
        # Normalize SPV name: strip whitespace, convert to title case for consistency
        original_name = spv['nama_spv']
        normalized_name = original_name.strip().title() if original_name else "Unknown"
        
        # Hardcode fix for Tonny/Toni Saputra (same person)
        if normalized_name in ["Tonny Saputra", "Toni Saputra"]:
            normalized_name = "Tonny Saputra"
        
        # Determine which database this record came from
        database_source = spv.get('database_source', 'unknown')
        
        # Use normalized name as key but keep original for display if it's the first occurrence
        if normalized_name in combined_spvs:
            # Sum the DO counts for SPVs with the same name
            if database_source == 'honda_mis':
                combined_spvs[normalized_name]['mtd_do_madiun'] += spv['mtd_do'] or 0
                combined_spvs[normalized_name]['ytd_do_madiun'] += spv['ytd_do'] or 0
                combined_spvs[normalized_name]['today_do_madiun'] += spv['today_do'] or 0
            elif database_source == 'm2_magetan':
                combined_spvs[normalized_name]['mtd_do_magetan'] += spv['mtd_do'] or 0
                combined_spvs[normalized_name]['ytd_do_magetan'] += spv['ytd_do'] or 0
                combined_spvs[normalized_name]['today_do_magetan'] += spv['today_do'] or 0
        else:
            # Initialize with separate counters for each database
            if database_source == 'honda_mis':
                combined_spvs[normalized_name] = {
                    'nama_spv': normalized_name,
                    'mtd_do_madiun': spv['mtd_do'] or 0,
                    'mtd_do_magetan': 0,
                    'ytd_do_madiun': spv['ytd_do'] or 0,
                    'ytd_do_magetan': 0,
                    'today_do_madiun': spv['today_do'] or 0,
                    'today_do_magetan': 0
                }
            elif database_source == 'm2_magetan':
                combined_spvs[normalized_name] = {
                    'nama_spv': normalized_name,
                    'mtd_do_madiun': 0,
                    'mtd_do_magetan': spv['mtd_do'] or 0,
                    'ytd_do_madiun': 0,
                    'ytd_do_magetan': spv['ytd_do'] or 0,
                    'today_do_madiun': 0,
                    'today_do_magetan': spv['today_do'] or 0
                }
    
    # Calculate totals for each SPV
    for spv_name, spv_data in combined_spvs.items():
        spv_data['mtd_do_total'] = spv_data['mtd_do_madiun'] + spv_data['mtd_do_magetan']
        spv_data['ytd_do_total'] = spv_data['ytd_do_madiun'] + spv_data['ytd_do_magetan']
        spv_data['today_do_total'] = spv_data['today_do_madiun'] + spv_data['today_do_magetan']
    
    # Sort by YTD total DO count (highest to lowest) for performance ranking
    sorted_spvs = sorted(combined_spvs.values(), key=lambda x: x['ytd_do_total'], reverse=True)
    
    for spv in sorted_spvs:
        html += f"""
            <tr>
                <td class="spv-name">{spv['nama_spv']}</td>
                <td class="today-group">{spv['today_do_madiun']}</td>
                <td class="today-group">{spv['today_do_magetan']}</td>
                <td class="today-group today-divider">{spv['today_do_total']}</td>
                <td class="mtd-group">{spv['mtd_do_madiun']}</td>
                <td class="mtd-group">{spv['mtd_do_magetan']}</td>
                <td class="mtd-group mtd-divider">{spv['mtd_do_total']}</td>
                <td class="ytd-group">{spv['ytd_do_madiun']}</td>
                <td class="ytd-group">{spv['ytd_do_magetan']}</td>
                <td class="ytd-group">{spv['ytd_do_total']}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
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
    message["X-Priority"] = "1"  # High priority
    message["X-MSMail-Priority"] = "High"
    message["Importance"] = "High"
    
    # Create plain text version
    plain_text = f"""
SPV DO Report
{subject}

This is an automated report. Please view the HTML version for complete details.
    """
    
    # Attach both plain text and HTML versions
    message.attach(MIMEText(plain_text, "plain"))
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

def main():
    if len(sys.argv) == 2:
        # Single date argument in DDMMYYYY format (like vehicle_reporting.py)
        date_arg = sys.argv[1]
        try:
            # Parse date argument
            day = int(date_arg[0:2])
            month = int(date_arg[2:4])
            year = int(date_arg[4:8])
            target_date = datetime(year, month, day).date()
            
            # Calculate date ranges
            start_date = target_date.replace(month=1, day=1).strftime('%Y-%m-%d')  # YTD start
            end_date = target_date.strftime('%Y-%m-%d')  # Target date
            
            print(f"Generating SPV report for {day} {['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'][month-1]} {year}")
            print(f"YTD Period: {start_date} to {end_date}")
            
        except (ValueError, IndexError):
            print("Error: Invalid date format.")
            print("Usage: python spv_report.py <DDMMYYYY>")
            print("Example: python spv_report.py 05062025")
            sys.exit(1)
            
    elif len(sys.argv) == 3:
        # Original format with start_date and end_date
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        print(f"Custom date range: {start_date} to {end_date}")
        
    else:
        print("Usage:")
        print("  python spv_report.py <DDMMYYYY>")
        print("  python spv_report.py <start_date> <end_date>")
        print("")
        print("Examples:")
        print("  python spv_report.py 05062025           # YTD report for June 5, 2025")
        print("  python spv_report.py 2025-01-01 2025-06-05  # Custom date range")
        sys.exit(1)

    # Get recipients from environment variables
    recipients_str = os.getenv("EMAIL_RECIPIENTS", "")
    recipients = [email.strip() for email in recipients_str.split(",") if email.strip()]
    
    try:
        # Get SPV performance data for both locations
        madiun_data = get_spv_performance(start_date, end_date, "honda_mis")
        magetan_data = get_spv_performance(start_date, end_date, "m2_magetan")
        
        # Add database source information to each record
        for record in madiun_data['data']:
            record['database_source'] = 'honda_mis'
        
        for record in magetan_data['data']:
            record['database_source'] = 'm2_magetan'
        
        # Combine data from both locations
        combined_data = {
            'data': madiun_data['data'] + magetan_data['data']
        }
        
        # Generate and send report
        html_report = format_spv_report(combined_data, start_date, end_date)
        # Format dates for email subject
        start_date_id = format_date_id(start_date)
        end_date_id = format_date_id(end_date)
        send_email(
            f"M2 | SPV DO Report ({start_date_id} ~ {end_date_id})",
            html_report,
            recipients
        )
        print("SPV DO report sent successfully!")
        
    except Exception as e:
        print(f"Error generating SPV report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 