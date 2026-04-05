import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# Define the target directory inside the workspace
OUT_DIR = r"c:\Users\ansy2\OneDrive\Desktop\Outskill Gen-AI Engg\Projects\Hackathon\finance tech\Financial Doctor\sample_data"
os.makedirs(OUT_DIR, exist_ok=True)

print("Writing files to:", OUT_DIR)

# -------------------------------------------------------------
# 1. Generate bank_statement_march_2026.csv
# -------------------------------------------------------------
csv_data = [
    ["28-02-2026", "OPENING BALANCE", "", "", "45800.00"],
    ["01-03-2026", "INB/SALARY CREDITED - NEFT ACME CORP", "", "155000.00", "200800.00"],
    ["03-03-2026", "UPI/Zomato/Food", "850.00", "", "199950.00"],
    ["05-03-2026", "UPI/Amazon/Shopping", "4500.00", "", "195450.00"],
    ["07-03-2026", "EMI/SBI HOME LOAN", "35000.00", "", "160450.00"],
    ["10-03-2026", "UPI/Dmart/Groceries", "6500.00", "", "153950.00"],
    ["12-03-2026", "SIP/ZERODHA MF NIFTY50", "15000.00", "", "138950.00"],
    ["14-03-2026", "UPI/Uber/Travel", "450.00", "", "138500.00"],
    ["15-03-2026", "CREDIT CARD BILL/HDFC", "12500.00", "", "126000.00"],
    ["20-03-2026", "LIC PREMIUM", "5000.00", "", "121000.00"],
    ["25-03-2026", "CASH WITHDRAWAL/ATM", "5000.00", "", "116000.00"],
    ["28-03-2026", "UPI/Swiggy/Food", "950.00", "", "115050.00"]
]
df_csv = pd.DataFrame(csv_data, columns=["Txn Date", "Description", "Debit", "Credit", "Balance"])
csv_path = os.path.join(OUT_DIR, "bank_statement_march_2026.csv")
df_csv.to_csv(csv_path, index=False)
print(f"Generated: {csv_path}")


# -------------------------------------------------------------
# 2. Generate debt_summary_march_2026.xlsx
# -------------------------------------------------------------
excel_data = [
    ["SBI Home Loan", 4500000.00, "8.5%", 35000.00, "07-04-2026"],
    ["HDFC Car Loan", 650000.00, "9.2%", 14500.00, "15-04-2026"],
    ["HDFC Credit Card", 45000.00, "36.0%", 2250.00, "05-04-2026"], 
    ["Personal Loan (Bajaj)", 150000.00, "14.5%", 6500.00, "12-04-2026"]
]
df_excel = pd.DataFrame(excel_data, columns=["Loan/Credit Account", "Principal Outstanding", "Interest Rate (APR)", "Monthly EMI", "Next Due Date"])
excel_path = os.path.join(OUT_DIR, "debt_summary_march_2026.xlsx")
df_excel.to_excel(excel_path, index=False)
print(f"Generated: {excel_path}")


# -------------------------------------------------------------
# 3. Generate salary_slip_march_2026.pdf
# -------------------------------------------------------------
pdf = FPDF()
pdf.add_page()

# Header
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt="ACME TECHNOLOGIES INDIA PVT LTD", ln=True, align='C')
pdf.set_font("Arial", '', 12)
pdf.cell(200, 10, txt="Salary Slip for the month of March 2026", ln=True, align='C')
pdf.line(10, 30, 200, 30)

# Employee Details
pdf.ln(10)
pdf.set_font("Arial", 'B', 10)
pdf.cell(50, 8, "Employee Name:", border=0)
pdf.set_font("Arial", '', 10)
pdf.cell(50, 8, "Rahul Sharma", border=0)
pdf.set_font("Arial", 'B', 10)
pdf.cell(50, 8, "Designation:", border=0)
pdf.set_font("Arial", '', 10)
pdf.cell(50, 8, "Senior Software Engineer", ln=True)

pdf.set_font("Arial", 'B', 10)
pdf.cell(50, 8, "Employee ID:", border=0)
pdf.set_font("Arial", '', 10)
pdf.cell(50, 8, "EMP-2048", border=0)
pdf.set_font("Arial", 'B', 10)
pdf.cell(50, 8, "Department:", border=0)
pdf.set_font("Arial", '', 10)
pdf.cell(50, 8, "Engineering", ln=True)

pdf.set_font("Arial", 'B', 10)
pdf.cell(50, 8, "Bank A/c No:", border=0)
pdf.set_font("Arial", '', 10)
pdf.cell(50, 8, "XXXXXXXX4093", border=0)
pdf.set_font("Arial", 'B', 10)
pdf.cell(50, 8, "PAN:", border=0)
pdf.set_font("Arial", '', 10)
pdf.cell(50, 8, "ABCDE1234F", ln=True)

# Earnings and Deductions Table
pdf.ln(10)
pdf.set_font("Arial", 'B', 10)
pdf.cell(90, 8, "Earnings", border=1, align='C')
pdf.cell(10, 8, "", border=0) # spacer
pdf.cell(90, 8, "Deductions", border=1, align='C', ln=True)

pdf.set_font("Arial", '', 10)

# Row 1
pdf.cell(60, 8, "Basic Salary", border='L')
pdf.cell(30, 8, "95,000.00", border='R', align='R')
pdf.cell(10, 8, "", border=0)
pdf.cell(60, 8, "Provident Fund (PF)", border='L')
pdf.cell(30, 8, "11,400.00", border='R', align='R', ln=True)

# Row 2
pdf.cell(60, 8, "House Rent Allowance (HRA)", border='L')
pdf.cell(30, 8, "47,500.00", border='R', align='R')
pdf.cell(10, 8, "", border=0)
pdf.cell(60, 8, "Tax Deducted at Source (TDS)", border='L')
pdf.cell(30, 8, "25,000.00", border='R', align='R', ln=True)

# Row 3
pdf.cell(60, 8, "Special Allowance", border='L,B')
pdf.cell(30, 8, "48,900.00", border='R,B', align='R')
pdf.cell(10, 8, "", border=0)
pdf.cell(60, 8, "Professional Tax", border='L,B')
pdf.cell(30, 8, "200.00", border='R,B', align='R', ln=True)

# Totals
pdf.set_font("Arial", 'B', 10)
pdf.cell(60, 8, "Gross Earnings", border=1)
pdf.cell(30, 8, "191,400.00", border=1, align='R')
pdf.cell(10, 8, "", border=0)
pdf.cell(60, 8, "Total Deductions", border=1)
pdf.cell(30, 8, "36,600.00", border=1, align='R', ln=True)

# Net Salary
pdf.ln(10)
pdf.set_font("Arial", 'B', 12)
pdf.cell(100, 10, "NET SALARY PAYABLE: Rs. 154,800.00", border=0, ln=True)

# Note
pdf.set_font("Arial", 'I', 8)
pdf.cell(200, 8, "This is a computer generated document and does not require a signature.", border=0, align='C')

pdf_path = os.path.join(OUT_DIR, "salary_slip_march_2026.pdf")
pdf.output(pdf_path)
print(f"Generated: {pdf_path}")
print("Test files generated successfully!")
