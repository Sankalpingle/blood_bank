import sqlite3
import os
from datetime import datetime

DB_NAME = "blood_bank.db"

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# ─────────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ─────────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────────
def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            age         INTEGER NOT NULL,
            blood_group TEXT    NOT NULL,
            contact     TEXT    NOT NULL,
            city        TEXT    NOT NULL,
            donated_on  TEXT    NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS blood_stock (
            blood_group TEXT PRIMARY KEY,
            units       INTEGER NOT NULL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS blood_requests (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT    NOT NULL,
            blood_group  TEXT    NOT NULL,
            units        INTEGER NOT NULL,
            hospital     TEXT    NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'Pending',
            requested_on TEXT    NOT NULL
        )
    """)

    # Seed blood stock for all groups if not already present
    for bg in BLOOD_GROUPS:
        c.execute("INSERT OR IGNORE INTO blood_stock (blood_group, units) VALUES (?, 0)", (bg,))

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def header(title):
    print(f"\n{RED}{BOLD}{'═'*50}{RESET}")
    print(f"{RED}{BOLD}  🩸  {title}{RESET}")
    print(f"{RED}{BOLD}{'═'*50}{RESET}\n")

def pause():
    input(f"\n{YELLOW}Press Enter to continue...{RESET}")

def pick_blood_group():
    print(f"\n{CYAN}Available Blood Groups:{RESET}")
    for i, bg in enumerate(BLOOD_GROUPS, 1):
        print(f"  {i}. {bg}")
    while True:
        choice = input("Select blood group (1-8): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 8:
            return BLOOD_GROUPS[int(choice) - 1]
        print(f"{RED}Invalid choice. Try again.{RESET}")

def validate_contact(contact):
    return contact.isdigit() and len(contact) == 10

def validate_age(age_str):
    return age_str.isdigit() and 18 <= int(age_str) <= 65

# ─────────────────────────────────────────────
#  FEATURE 1 — DONOR REGISTRATION
# ─────────────────────────────────────────────
def register_donor():
    clear()
    header("Register New Donor")

    name = input("Enter donor name        : ").strip()
    if not name:
        print(f"{RED}Name cannot be empty.{RESET}")
        pause(); return

    age_str = input("Enter age (18–65)       : ").strip()
    if not validate_age(age_str):
        print(f"{RED}Age must be between 18 and 65.{RESET}")
        pause(); return
    age = int(age_str)

    blood_group = pick_blood_group()

    contact = input("Enter contact (10 digits): ").strip()
    if not validate_contact(contact):
        print(f"{RED}Contact must be exactly 10 digits.{RESET}")
        pause(); return

    city = input("Enter city              : ").strip()
    if not city:
        print(f"{RED}City cannot be empty.{RESET}")
        pause(); return

    donated_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO donors (name, age, blood_group, contact, city, donated_on) VALUES (?,?,?,?,?,?)",
        (name, age, blood_group, contact, city, donated_on)
    )
    # Add 1 unit to stock on donation
    c.execute("UPDATE blood_stock SET units = units + 1 WHERE blood_group = ?", (blood_group,))
    conn.commit()
    conn.close()

    print(f"\n{GREEN}✅  Donor '{name}' registered successfully! 1 unit of {blood_group} added to stock.{RESET}")
    pause()

def view_all_donors():
    clear()
    header("All Registered Donors")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, age, blood_group, contact, city, donated_on FROM donors ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        print(f"{YELLOW}No donors registered yet.{RESET}")
        pause(); return

    print(f"{'ID':<5} {'Name':<20} {'Age':<5} {'Blood':<6} {'Contact':<12} {'City':<15} {'Donated On'}")
    print("─" * 80)
    for r in rows:
        print(f"{r[0]:<5} {r[1]:<20} {r[2]:<5} {r[3]:<6} {r[4]:<12} {r[5]:<15} {r[6]}")
    pause()

# ─────────────────────────────────────────────
#  FEATURE 2 — BLOOD STOCK MANAGEMENT
# ─────────────────────────────────────────────
def view_blood_stock():
    clear()
    header("Current Blood Stock")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT blood_group, units FROM blood_stock ORDER BY blood_group")
    rows = c.fetchall()
    conn.close()

    print(f"{'Blood Group':<15} {'Units Available':<18} {'Status'}")
    print("─" * 50)
    for bg, units in rows:
        if units == 0:
            status = f"{RED}Critical — Out of Stock{RESET}"
        elif units < 5:
            status = f"{YELLOW}Low Stock{RESET}"
        else:
            status = f"{GREEN}Sufficient{RESET}"
        print(f"{bg:<15} {units:<18} {status}")
    pause()

def add_stock_manually():
    """Admin can manually add units (e.g., from blood drives)."""
    clear()
    header("Add Blood Stock Manually")

    blood_group = pick_blood_group()
    units_str = input("Enter units to add: ").strip()
    if not units_str.isdigit() or int(units_str) <= 0:
        print(f"{RED}Units must be a positive number.{RESET}")
        pause(); return

    units = int(units_str)
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE blood_stock SET units = units + ? WHERE blood_group = ?", (units, blood_group))
    conn.commit()
    c.execute("SELECT units FROM blood_stock WHERE blood_group = ?", (blood_group,))
    total = c.fetchone()[0]
    conn.close()

    print(f"\n{GREEN}✅  Added {units} unit(s) of {blood_group}. Total now: {total} unit(s).{RESET}")
    pause()

# ─────────────────────────────────────────────
#  FEATURE 3 — SEARCH BY BLOOD GROUP
# ─────────────────────────────────────────────
def search_by_blood_group():
    clear()
    header("Search Donors by Blood Group")

    blood_group = pick_blood_group()

    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, age, contact, city, donated_on FROM donors WHERE blood_group = ? ORDER BY donated_on DESC",
        (blood_group,)
    )
    donors = c.fetchall()
    c.execute("SELECT units FROM blood_stock WHERE blood_group = ?", (blood_group,))
    stock = c.fetchone()
    conn.close()

    units = stock[0] if stock else 0
    print(f"\n{CYAN}Stock for {blood_group}: {units} unit(s){RESET}\n")

    if not donors:
        print(f"{YELLOW}No donors found for blood group {blood_group}.{RESET}")
        pause(); return

    print(f"{'ID':<5} {'Name':<20} {'Age':<5} {'Contact':<12} {'City':<15} {'Donated On'}")
    print("─" * 75)
    for r in donors:
        print(f"{r[0]:<5} {r[1]:<20} {r[2]:<5} {r[3]:<12} {r[4]:<15} {r[5]}")
    pause()

# ─────────────────────────────────────────────
#  FEATURE 4 — REQUEST / ISSUE BLOOD
# ─────────────────────────────────────────────
def request_blood():
    clear()
    header("Request Blood")

    patient = input("Enter patient name     : ").strip()
    if not patient:
        print(f"{RED}Patient name cannot be empty.{RESET}")
        pause(); return

    blood_group = pick_blood_group()

    units_str = input("Enter units required   : ").strip()
    if not units_str.isdigit() or int(units_str) <= 0:
        print(f"{RED}Units must be a positive number.{RESET}")
        pause(); return
    units = int(units_str)

    hospital = input("Enter hospital name    : ").strip()
    if not hospital:
        print(f"{RED}Hospital name cannot be empty.{RESET}")
        pause(); return

    # Check stock
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT units FROM blood_stock WHERE blood_group = ?", (blood_group,))
    row = c.fetchone()
    available = row[0] if row else 0

    requested_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    if available >= units:
        status = "Approved"
        c.execute("UPDATE blood_stock SET units = units - ? WHERE blood_group = ?", (units, blood_group))
        msg = f"{GREEN}✅  Request APPROVED. {units} unit(s) of {blood_group} issued to {hospital}.{RESET}"
    else:
        status = "Pending — Insufficient Stock"
        msg = (f"{YELLOW}⚠️   Only {available} unit(s) available for {blood_group}. "
               f"Request saved as Pending.{RESET}")

    c.execute(
        "INSERT INTO blood_requests (patient_name, blood_group, units, hospital, status, requested_on) VALUES (?,?,?,?,?,?)",
        (patient, blood_group, units, hospital, status, requested_on)
    )
    conn.commit()
    conn.close()

    print(f"\n{msg}")
    pause()

def view_all_requests():
    clear()
    header("All Blood Requests")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, patient_name, blood_group, units, hospital, status, requested_on FROM blood_requests ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        print(f"{YELLOW}No requests found.{RESET}")
        pause(); return

    print(f"{'ID':<5} {'Patient':<18} {'BG':<5} {'Units':<7} {'Hospital':<20} {'Status':<30} {'Date'}")
    print("─" * 100)
    for r in rows:
        status_color = GREEN if r[5] == "Approved" else YELLOW
        print(f"{r[0]:<5} {r[1]:<18} {r[2]:<5} {r[3]:<7} {r[4]:<20} {status_color}{r[5]:<30}{RESET} {r[6]}")
    pause()

# ─────────────────────────────────────────────
#  SUB-MENUS
# ─────────────────────────────────────────────
def donor_menu():
    while True:
        clear()
        header("Donor Management")
        print("  1. Register New Donor")
        print("  2. View All Donors")
        print("  0. Back to Main Menu")
        choice = input("\nEnter choice: ").strip()
        if choice == "1":   register_donor()
        elif choice == "2": view_all_donors()
        elif choice == "0": break
        else: print(f"{RED}Invalid option.{RESET}"); pause()

def stock_menu():
    while True:
        clear()
        header("Blood Stock Management")
        print("  1. View Blood Stock")
        print("  2. Add Stock Manually")
        print("  0. Back to Main Menu")
        choice = input("\nEnter choice: ").strip()
        if choice == "1":   view_blood_stock()
        elif choice == "2": add_stock_manually()
        elif choice == "0": break
        else: print(f"{RED}Invalid option.{RESET}"); pause()

def request_menu():
    while True:
        clear()
        header("Blood Requests")
        print("  1. Make a Blood Request")
        print("  2. View All Requests")
        print("  0. Back to Main Menu")
        choice = input("\nEnter choice: ").strip()
        if choice == "1":   request_blood()
        elif choice == "2": view_all_requests()
        elif choice == "0": break
        else: print(f"{RED}Invalid option.{RESET}"); pause()

# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
def main():
    init_db()
    while True:
        clear()
        print(f"{RED}{BOLD}")
        print("  ╔══════════════════════════════════════════╗")
        print("  ║     🩸  BLOOD BANK MANAGEMENT SYSTEM     ║")
        print("  ╚══════════════════════════════════════════╝")
        print(f"{RESET}")
        print(f"  {CYAN}1.{RESET} 🧑‍⚕️  Donor Management")
        print(f"  {CYAN}2.{RESET} 🏥  Blood Stock Management")
        print(f"  {CYAN}3.{RESET} 🔍  Search by Blood Group")
        print(f"  {CYAN}4.{RESET} 📋  Blood Requests")
        print(f"  {CYAN}0.{RESET} 🚪  Exit")
        print()
        choice = input("  Enter choice: ").strip()

        if choice == "1":   donor_menu()
        elif choice == "2": stock_menu()
        elif choice == "3": search_by_blood_group()
        elif choice == "4": request_menu()
        elif choice == "0":
            print(f"\n{GREEN}Thank you for using Blood Bank Management System. Goodbye!{RESET}\n")
            break
        else:
            print(f"{RED}Invalid option. Please try again.{RESET}")
            pause()

if __name__ == "__main__":
    main()
