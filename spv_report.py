import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from db_operations import get_spv_performance

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
            }}
            th {{
                background-color: #e70000;
                color: white;
                padding: 8px;
                text-align: center;
                font-size: 13px;
            }}
            td {{
                padding: 8px;
                text-align: center;
                border-bottom: 1px solid #ddd;
                font-size: 13px;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .spv-name {{
                text-align: left;
                font-weight: bold;
                color: #e70000;
            }}
            .today-change {{
                color: #34a853;
                font-weight: bold;
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
                    <th>SPV</th>
                    <th>MTD</th>
                    <th>YTD</th>
                    <th>Today</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Combine SPVs with same name and sum their DO counts
    combined_spvs = {}
    for spv in spv_data['data']:
        spv_name = spv['nama_spv']
        if spv_name in combined_spvs:
            # Sum the DO counts for SPVs with the same name
            combined_spvs[spv_name]['mtd_do'] += spv['mtd_do']
            combined_spvs[spv_name]['ytd_do'] += spv['ytd_do']
            combined_spvs[spv_name]['today_do'] += spv['today_do']
        else:
            combined_spvs[spv_name] = {
                'nama_spv': spv_name,
                'mtd_do': spv['mtd_do'],
                'ytd_do': spv['ytd_do'],
                'today_do': spv['today_do']
            }
    
    # Sort by YTD DO count (highest to lowest) for performance ranking
    sorted_spvs = sorted(combined_spvs.values(), key=lambda x: x['ytd_do'], reverse=True)
    
    for spv in sorted_spvs:
        html += f"""
            <tr>
                <td class="spv-name">{spv['nama_spv']}</td>
                <td>{spv['mtd_do']}</td>
                <td>{spv['ytd_do']}</td>
                <td>{spv['today_do']} <span class="today-change">[+{spv['today_do']}]</span></td>
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
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "marviano.austin@gmail.com"
    app_password = "ktqbdhbktmcdkvuf"

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
    if len(sys.argv) != 3:
        print("Usage: python spv_report.py <start_date> <end_date>")
        print("Example: python spv_report.py 2024-01-01 2024-03-20")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    recipients = ["alvusebastian@gmail.com", "sony_hendarto@hotmail.com"]
    
    try:
        # Get SPV performance data for both locations
        madiun_data = get_spv_performance(start_date, end_date, "honda_mis")
        magetan_data = get_spv_performance(start_date, end_date, "m2_magetan")
        
        # Combine data from both locations (no need to add city info anymore)
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