from datetime import datetime, date
import mysql.connector
import sys

# Helper functions for formatting
def format_currency(amount):
    """Format number to Indonesian Rupiah."""
    return f"Rp {amount:,.0f}"

def format_percentage(value):
    """Format number to percentage with 2 decimal places."""
    return f"{value:+.2f}%" if value != 0 else "0.00%"

def format_date(date_obj):
    """Format date to Indonesian format."""
    months = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    return f"{date_obj.day} {months[date_obj.month]} {date_obj.year}"

def connect_to_database():
    """Establish connection to the MySQL database."""
    try:
        return mysql.connector.connect(
            host="36.74.102.231",
            user="honda_mis",
            password="mcMotor",
            database="honda_mis"
        )
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        sys.exit(1)

def get_test_data(test_date):
    """Get real data for testing margin calculations."""
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        bast.kode_bast, 
        bast.tgl_bast,
        spk.no_form_spk,
        spk.cara_bayar,
        mp.nama_pelanggan,
        spk.kode_finance,
        mf.nama_finance,
        mb.kode_warna_lengkap,
        mb.nama_lengkap,
        mb.perk_notice,
        mk_sales.nama_karyawan AS nama_sales,
        spk.harga_jual,
        IFNULL(dor.harga_ppn, 0) AS harga_tebus,
        spk.diskon,
        spk.nota_kredit, 
        spk.komisi_makelar,
        IF(spk.status_otr = 0, spk.cad_bbn, 0) AS cadangan_bbn,
        spk.perk_adm_wil,
        spk.um_t_leasing,
        spk.uang_muka,
        spk.komisi_makelar_leasing,
        spk.promo_pusat,
        spk.ins_owner,
        spk.oi_bbn,
        spk.scp,
        spk.saving,
        spk.admin_bbn,
        
        -- Your current margin calculation
        (spk.harga_jual - (IFNULL(dor.harga_ppn, 0) 
            + spk.diskon 
            + spk.nota_kredit 
            + spk.komisi_makelar 
            + IF(spk.status_otr = 0, spk.cad_bbn, 0) 
            + (spk.um_t_leasing - spk.uang_muka + spk.komisi_makelar_leasing) 
            + spk.promo_pusat) 
            + spk.ins_owner 
            + spk.oi_bbn 
            + spk.scp 
            + spk.saving 
            + spk.admin_bbn) AS current_margin,
            
        -- Try to get leasing data if available
        IFNULL(pl.dp_gross, 0) AS dp_gross,
        IFNULL(pl.subs_ahm, 0) AS subs_ahm,
        IFNULL(pl.main_dealer, 0) AS main_dealer
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
    WHERE DATE_FORMAT(bast.tgl_bast, '%Y-%m-%d') = %s
    """
    
    try:
        cursor.execute(query, (test_date.strftime('%Y-%m-%d'),))
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error executing query: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def calculate_margin_percentage(margin, selling_price):
    """Calculate margin as a percentage of selling price."""
    if selling_price == 0:
        return 0
    return (margin / selling_price) * 100

def calculate_proposed_margin(row):
    """Calculate margin using the formula from the new query."""
    try:
        # Check if we have the necessary fields to calculate
        if 'harga_jual' not in row or 'harga_tebus' not in row:
            return None
        
        # Calculate subs_dealer as in the query
        subs_dealer = row.get('um_t_leasing', 0) - row.get('uang_muka', 0) + row.get('komisi_makelar_leasing', 0)
        
        # Use the new margin calculation matching the query
        proposed_margin = (
            row['harga_jual'] - (
                row['harga_tebus'] + 
                row.get('diskon', 0) + 
                row.get('nota_kredit', 0) + 
                row.get('komisi_makelar', 0) +
                row.get('dp_gross', 0) - 
                row.get('subs_ahm', 0) - 
                row.get('main_dealer', 0) - 
                row.get('perk_notice', 0) +
                subs_dealer - 
                row.get('promo_pusat', 0)
            ) - row.get('perk_adm_wil', 0) + row.get('saving', 0)
        )
        
        return proposed_margin
    except Exception as e:
        print(f"Error calculating proposed margin: {e}")
        return None

def test_margin_calculations():
    """Test both margin calculations and compare the results."""
    # Set test date to February 23, 2025
    test_date = date(2025, 2, 23)
    print(f"Testing margin calculations for date: {format_date(test_date)}")
    
    # Get test data
    test_data = get_test_data(test_date)
    
    if not test_data:
        print(f"No data found for {format_date(test_date)}")
        return
    
    print(f"Found {len(test_data)} records for testing")
    print("-" * 80)
    
    # Calculate total margin for all units
    total_units = len(test_data)
    total_selling_price = 0
    total_proposed_margin = 0
    
    # Test each record
    for idx, row in enumerate(test_data, 1):
        print(f"\nVehicle {idx}: {row['nama_lengkap']} ({row['kode_bast']})")
        
        # Calculate proposed margin
        proposed_margin = calculate_proposed_margin(row)
        current_margin = row['current_margin']
        
        # Keep running total for overall margin calculation
        total_selling_price += row['harga_jual']
        if proposed_margin is not None:
            total_proposed_margin += proposed_margin
        
        # Calculate margin percentage
        margin_percentage = calculate_margin_percentage(proposed_margin, row['harga_jual'])
        
        # Display components
        print(f"Selling Price: {format_currency(row['harga_jual'])}")
        print(f"Purchase Price: {format_currency(row['harga_tebus'])}")
        print(f"Discount: {format_currency(row.get('diskon', 0))}")
        
        # Compare margins
        print(f"\nCurrent Margin:  {format_currency(current_margin)}")
        print(f"New Calculated Margin: {format_currency(proposed_margin)}")
        print(f"Margin Percentage: {format_percentage(margin_percentage)}")
        
        # Check for discrepancies
        if proposed_margin is not None and abs(proposed_margin - current_margin) > 10:  # Allow for small rounding differences
            print(f"WARNING: Margin calculation discrepancy of {format_currency(proposed_margin - current_margin)}")
            print("Detailed component breakdown:")
            print(f"  - Selling Price: {format_currency(row['harga_jual'])}")
            print(f"  - Purchase Price: {format_currency(row['harga_tebus'])}")
            print(f"  - Discount: {format_currency(row.get('diskon', 0))}")
            print(f"  - Credit Note: {format_currency(row.get('nota_kredit', 0))}")
            print(f"  - Broker Commission: {format_currency(row.get('komisi_makelar', 0))}")
            print(f"  - DP Gross: {format_currency(row.get('dp_gross', 0))}")
            print(f"  - Subsidy AHM: {format_currency(row.get('subs_ahm', 0))}")
            print(f"  - Main Dealer: {format_currency(row.get('main_dealer', 0))}")
            print(f"  - Perk Notice: {format_currency(row.get('perk_notice', 0))}")
            print(f"  - Leasing Adjustment: {format_currency(row.get('um_t_leasing', 0) - row.get('uang_muka', 0) + row.get('komisi_makelar_leasing', 0))}")
            print(f"  - Promo Pusat: {format_currency(row.get('promo_pusat', 0))}")
            print(f"  - Perk Adm Wil: {format_currency(row.get('perk_adm_wil', 0))}")
            print(f"  - Saving: {format_currency(row.get('saving', 0))}")
            
        print("-" * 50)
    
    # Calculate and display overall margin
    overall_margin_percentage = calculate_margin_percentage(total_proposed_margin, total_selling_price)
    print("\n" + "=" * 80)
    print(f"SUMMARY: Total Units: {total_units}")
    print(f"Total Selling Price: {format_currency(total_selling_price)}")
    print(f"Total Margin: {format_currency(total_proposed_margin)} ({format_percentage(overall_margin_percentage)})")
    print("=" * 80)
    
    # Generate SMS-style message
    print(f"\nSMS Format: Mrgn:{format_currency(total_proposed_margin).replace('Rp ', '')}({format_percentage(overall_margin_percentage)})")

if __name__ == "__main__":
    test_margin_calculations()