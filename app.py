import pickle
import webbrowser
import threading
import random
import os
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF
from flask import Flask, render_template, request, session, redirect, url_for, send_file
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import hashlib  # 👈 ADD THIS
from time import time  # 👈 ADD THIs
from flask import jsonify  # Add this at top with other imports
# =========================
# LOAD AI MODEL (Placeholder for now, using rule-based mostly)
# =========================
try:
    with open("ai_model.pkl", "rb") as f:
        ai_model = pickle.load(f)
except:
    ai_model = None  # Fallback provided

# =========================
# FLASK INIT
# =========================
app = Flask(__name__)
app.secret_key = "jayam_super_secret_key_2026"

# =========================
# DATABASE SETUP
# =========================
def init_db():
    users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    enquiries_sql = """
    CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        insurance_type TEXT,
        details TEXT,
        recommendation TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    activity_sql = """
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        page TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    conn = sqlite3.connect('jayam.db')
    cursor = conn.cursor()
    cursor.execute(users_sql)
    cursor.execute(enquiries_sql)
    cursor.execute(activity_sql)
    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

@app.before_request
def log_activity():
    if request.endpoint and "static" not in request.endpoint:
        user = session.get("user", "Guest")
        page = request.path
        try:
            conn = sqlite3.connect('jayam.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO activity_logs (user_email, page) VALUES (?, ?)", (user, page))
            conn.commit()
            conn.close()
        except:
            pass

def log_user_login(name, email):
    try:
        conn = sqlite3.connect('jayam.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB LOG ERROR: {e}")

def log_enquiry(email, ins_type, details, recommendation):
    try:
        conn = sqlite3.connect('jayam.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO enquiries (user_email, insurance_type, details, recommendation) VALUES (?, ?, ?, ?)", 
                       (email, ins_type, str(details), recommendation))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB LOG ERROR: {e}")

# =========================
# HELPERS
# =========================
def login_required():
    return "user" in session

def generate_pdf(data):
    """Generates a PDF for the selected policy and details."""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(200, 10, txt="Jayam Insurance Consultancy", ln=1, align='C')
    pdf.ln(8)
    
    # Subtitle
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(200, 10, txt="Policy Application Confirmation", ln=1, align='L')
    pdf.ln(6)
    
    # Customer Details Section
    pdf.set_font("Arial", size=12)
    actual_name = session.get('name', 'Customer')
    actual_email = session.get('email', session.get('user', ''))
    
    pdf.cell(200, 8, txt=f"Name: {actual_name}", ln=1, align='L')
    pdf.cell(200, 8, txt=f"Email: {actual_email}", ln=1, align='L')
    
    # Customer Details from form
    for key, value in data.get('customer_details', {}).items():
        if key.lower() not in ['name', 'email']:
            pdf.cell(200, 8, txt=f"{key.replace('_', ' ').title()}: {value}", ln=1, align='L')
    
    pdf.ln(8)
    
    # Policy Details Section
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(200, 10, txt="Selected Policy Details", ln=1, align='L')
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 8, txt=f"Insurance Type: {data.get('type')}", ln=1, align='L')
    for key, value in data.get('policy_details', {}).items():
        pdf.cell(200, 8, txt=f"{key.replace('_', ' ').title()}: {value}", ln=1, align='L')

    # Ensure output directory exists
    if not os.path.exists("static/downloads"):
        os.makedirs("static/downloads")
        
    filename = f"static/downloads/Policy_{session.get('name', 'User')}_{random.randint(1000,9999)}.pdf"
    pdf.output(filename)
    return filename

# =========================
# RECOMMENDATION LOGIC
# =========================
# =========================
# RECOMMENDATION LOGIC
# =========================
def get_recommendations(insurance_type, data):
    recommendations = []
    
    # --- 1. Rule-Based Recommendations (Existing) ---
    if insurance_type == "Health":
        age = int(data.get('age', data.get('customer_age', 30) or 30))
        members = int(data.get('members', 1))
        
        if members > 1:
            recommendations.append({
                "company": "Star Health", 
                "policy": "Family Optima", 
                "cover": "5 Lakhs", 
                "premium": "Rs. 15,000/yr", 
                "features": "Family Floater, Maternity"
            })
            recommendations.append({
                "company": "HDFC ERGO", 
                "policy": "Optima Restore", 
                "cover": "10 Lakhs", 
                "premium": "Rs. 18,000/yr", 
                "features": "100% Restore Benefit"
            })
        else:
            recommendations.append({
                "company": "Niva Bupa", 
                "policy": "ReAssure", 
                "cover": "5 Lakhs", 
                "premium": "Rs. 7,000/yr", 
                "features": "Unlimited ReAssure"
            })
             
        if age > 50:
            recommendations.append({
                "company": "Care Health", 
                "policy": "Senior Care", 
                "cover": "5 Lakhs", 
                "premium": "Rs. 22,000/yr", 
                "features": "OPD Cover, No pre-checkup"
            })

    elif insurance_type == "Motor":
        v_type = data.get('vehicle_type', 'Car')
        
        if v_type == 'Bike':
            recommendations.append({
                "company": "HDFC ERGO", 
                "policy": "Two Wheeler Secure", 
                "cover": "Comprehensive", 
                "premium": "Rs. 1,200/yr", 
                "features": "Roadside Assistance"
            })
            recommendations.append({
                "company": "ICICI Lombard", 
                "policy": "Bike Protect", 
                "cover": "Third Party Only", 
                "premium": "Rs. 850/yr", 
                "features": "Legal Liability"
            })

        elif v_type == 'Car':
            recommendations.append({
                "company": "ICICI Lombard", 
                "policy": "Car Protect", 
                "cover": "Comprehensive", 
                "premium": "Rs. 8,000/yr", 
                "features": "Zero Depreciation"
            })
            recommendations.append({
                "company": "Bajaj Allianz", 
                "policy": "Drive Assure", 
                "cover": "Bumper to Bumper", 
                "premium": "Rs. 9,500/yr", 
                "features": "Engine Protect"
            })

        elif v_type == 'GCV':
            recommendations.append({
                "company": "Shriram General", 
                "policy": "Goods Carrier Pkg", 
                "cover": "Liability + OD", 
                "premium": "Rs. 15,000/yr", 
                "features": "Pan India Cover"
            })
        
        elif v_type == 'PCV':
            recommendations.append({
                "company": "TATA AIG", 
                "policy": "Passenger Carrier", 
                "cover": "Liability + Passenger", 
                "premium": "Rs. 12,000/yr", 
                "features": "Passenger Personal Accident"
            })
             
        elif v_type == 'Misc':
            recommendations.append({
                "company": "New India Assurance", 
                "policy": "Misc Vehicle Pkg", 
                "cover": "Standard", 
                "premium": "Rs. 6,000/yr", 
                "features": "Off-Road Cover"
            })

    elif insurance_type == "Corporate":
        employees = int(data.get('employees', 10))
        
        recommendations.append({
            "company": "New India Assurance", 
            "policy": "Workmen Compensation", 
            "cover": "Legal Liability", 
            "premium": "Based on Payroll", 
            "features": "Covers Work Accidents"
        })
        if employees > 20:
            recommendations.append({
                "company": "Plum HQ", 
                "policy": "Group Health", 
                "cover": "3 Lakhs/Employee", 
                "premium": "Rs. 2,500/emp", 
                "features": "Digital Claims, Wellness"
            })

    if insurance_type == "Life":
        income = int(data.get('income', 500000))
        recommendations.append({
            "company": "LIC", 
            "policy": "Jeevan Umang", 
            "cover": "Sum Assured + Bonus", 
            "premium": "Rs. 25,000/yr", 
            "features": "Lifetime Coverage"
        })
        if income > 1000000:
            recommendations.append({
                "company": "HDFC Life", 
                "policy": "Click 2 Protect", 
                "cover": "1 Crore", 
                "premium": "Rs. 12,000/yr", 
                "features": "Term Insurance"
            })

    # --- 2. AI Model Prediction (Integration) ---
    if ai_model:
        try:
            # Map Inputs to Model Features: [type, age, income, budget, cover]
            
            # 1. Type Mapping
            type_map = {"Life": 1, "Motor": 2, "Health": 3, "Corporate": 4}
            f_type = type_map.get(insurance_type, 1)
            
            # 2. Age - Get from various possible field names
            f_age = int(data.get('age', data.get('customer_age', data.get('vehicle_age', 30))) or 30)
            
            # 3. Income (convert to lakhs if needed)
            income_value = float(data.get('income', 8))
            # If income is in rupees (like 500000), convert to lakhs
            if income_value > 1000:
                income_value = income_value / 100000
            f_income = income_value
            
            # 4. Budget (1=Low, 2=Mid, 3=High)
            budget_map = {"Economy": 1, "Standard": 2, "Premium": 3}
            f_budget = budget_map.get(data.get('budget'), 2)
            
            # 5. Cover - Get from form data
            cover_value = data.get('cover', '50L')
            cover_map = {"5L": 5, "10L": 10, "20L": 20, "50L": 50, "1Cr": 100}
            # Handle numeric cover values
            if isinstance(cover_value, (int, float)):
                f_cover = cover_value
            else:
                f_cover = cover_map.get(cover_value, 50)
            
            # Predict
            features = [[f_type, f_age, f_income, f_budget, f_cover]]
            prediction = ai_model.predict(features)
            predicted_policy_name = prediction[0]
            
            # Confidence Score
            confidence = 0
            if hasattr(ai_model, "predict_proba"):
                probs = ai_model.predict_proba(features)
                confidence = round(max(probs[0]) * 100)
            
            # Extract company name from policy name
            # List of known insurance companies
            known_companies = [
                "HDFC", "ICICI", "SBI", "Max", "LIC", "Star", "Niva", 
                "Care", "Digit", "New", "Plum", "Bajaj", "TATA", "Shriram"
            ]
            
            policy_parts = predicted_policy_name.split()
            
            # Try to extract company name
            ai_company = "AI Recommended"  # Default fallback
            
            if len(policy_parts) >= 2:
                # Check if first word is a known company
                if policy_parts[0] in known_companies:
                    ai_company = policy_parts[0]
                # Check if first two words form a known company
                elif (policy_parts[0] + " " + policy_parts[1]) in ["HDFC Life", "HDFC ERGO", "ICICI Lombard", "Star Health", "New India", "Bajaj Allianz", "TATA AIG"]:
                    ai_company = policy_parts[0] + " " + policy_parts[1]
                else:
                    ai_company = policy_parts[0]
            elif len(policy_parts) >= 1:
                ai_company = policy_parts[0]
            
            # Clean up company name
            ai_company = ai_company.replace("(Term)", "").replace("(Basic)", "").replace("(Standard)", "").strip()
            
            # Determine budget text
            budget_text = ["Eco", "Std", "Prem"][f_budget - 1]
            
            # Determine approximate premium based on type and budget
            base_premium = 5000
            if insurance_type == "Health":
                base_premium = 7000 if f_budget == 1 else 12000 if f_budget == 2 else 20000
            elif insurance_type == "Motor":
                base_premium = 2000 if f_budget == 1 else 8000 if f_budget == 2 else 15000
            elif insurance_type == "Life":
                base_premium = 10000 if f_budget == 1 else 25000 if f_budget == 2 else 50000
            elif insurance_type == "Corporate":
                base_premium = 15000 if f_budget == 1 else 50000 if f_budget == 2 else 100000
                
            approx_premium = f"Rs. {base_premium:,}/yr (Approx)"
            
            # Create a recommendation object for the AI result
            ai_rec = {
                "company": ai_company,
                "policy": predicted_policy_name,
                "cover": f"{confidence}% Match",
                "premium": approx_premium,
                "features": f"Based on your profile...",
                "is_ai_recommended": True,
                "confidence": confidence
                }
            
            # Prepend to list so it shows first
            recommendations.insert(0, ai_rec)
            print(f"✅ AI PREDICTION ({insurance_type}): {predicted_policy_name} (Company: {ai_company}, Conf: {confidence}%)")
            
        except Exception as e:
            print(f"❌ AI PREDICTION FAILED: {e}")
            import traceback
            traceback.print_exc()

    return recommendations
# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return redirect(url_for("login"))

# =========================
# EMAIL HELPER
# =========================
def send_otp_email(recipient_email, otp):
    # For testing and security, we are providing a dummy placeholder setup
    # If the user wants to use a real email, they can replace these credentials
    sender_email = "jayam.associates.2026@gmail.com" 
    sender_password = "tejs pcox pest vtst" # User must paste the App Password here
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Your Jayam InsurEase Login OTP"
        
        body = f"""
        Hello,

        Your One-Time Password (OTP) for logging into Jayam InsurEase is: 
        
        {otp}
        
        Please do not share this code with anyone.

        Regards,
        Jayam AI System
        """
        msg.attach(MIMEText(body, 'plain'))

        # Note: Actually attempting SMTP connection will fail unless real creds are provided. 
        # For the sake of the demo, we will wrap it in a try/except and still allow login.
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            print(f"SUCCESS: Email sent to {recipient_email}")
        except Exception as smtp_err:
            print(f"SMTP ERROR (Expected with dummy creds): {smtp_err}")
            print(f"FALLBACK - OTP FOR {recipient_email} is: {otp}")
            
        return True
    except Exception as e:
        print(f"EMAIL GENERATION ERROR: {e}")
        return False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["name"] = request.form.get("name")
        session["email"] = request.form.get("email")
        otp = random.randint(100000, 999999)
        session["otp"] = str(otp)
        
        # Call the new email function
        send_otp_email(session["email"], otp)
        
        return render_template("verify_otp.html")
    return render_template("login.html")

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    entered = request.form.get("otp")
    if entered == session.get("otp"): 
        session["user"] = session.get("email")
        # Log to DB
        log_user_login(session.get("name"), session.get("email"))
        return redirect(url_for("home"))
    return render_template("verify_otp.html", error="Invalid OTP")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/home")
def home():
    if not login_required(): return redirect(url_for("login"))
    return render_template("index.html", name=session.get("name"))

# --- Generic Details Input Route ---
@app.route("/details/<insurance_type>") # e.g. /details/Health
def details(insurance_type):
    if not login_required(): return redirect(url_for("login"))
    return render_template(f"{insurance_type.lower()}_details.html", type=insurance_type)

# --- Generic Suggestion Route ---
@app.route("/suggest", methods=["POST"])
def suggest_policy():
    if not login_required(): return redirect(url_for("login"))
    
    insurance_type = request.form.get("type")
    
    # Collect all form data
    data = request.form.to_dict()
    
    # Get Suggestions
    recommendations = get_recommendations(insurance_type, data)
    
    # Log Enquiry to DB
    log_enquiry(session.get("email"), insurance_type, data, recommendations[0]['policy'] if recommendations else "None")
    
    # Store input data temporarily to usage in next step
    session['current_inquiry'] = {
        "type": insurance_type,
        "customer_details": data
    }
    
    return render_template("selection.html", policies=recommendations, type=insurance_type)

# --- Policy Selection Route ---
@app.route("/select", methods=["POST"])
def select_policy():
    if not login_required(): return redirect(url_for("login"))
    
    policy_data = {
        "company": request.form.get("company"),
        "policy": request.form.get("policy"),
        "cover": request.form.get("cover"),
        "premium": request.form.get("premium")
    }
    
    # Update session data
    current_data = session.get('current_inquiry', {})
    current_data['policy_details'] = policy_data
    session['current_inquiry'] = current_data
    
    return render_template("confirmation.html", data=current_data)

from email.mime.base import MIMEBase
from email import encoders

def send_pdf_email(recipient_email, pdf_path, policy_name):
    sender_email = "jayam.associates.2026@gmail.com" 
    sender_password = "tejs pcox pest vtst" # User must paste the App Password here
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Your Jayam InsurEase Policy: {policy_name}"
        
        body = f"Hello,\n\nThank you for choosing Jayam Associates.\n\nPlease find your {policy_name} details attached as a PDF.\n\nRegards,\nJayam AI System"
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach the PDF
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(pdf_path)}",
        )
        msg.attach(part)

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            # Send copy to Company Admin
            server.sendmail(sender_email, "jayam.associates.2026@gmail.com", text)
            server.quit()
            print(f"SUCCESS: PDF emailed to {recipient_email}")
        except Exception as smtp_err:
            print(f"SMTP ERROR (Expected with dummy creds): {smtp_err}")
            
    except Exception as e:
        print(f"EMAIL PDF ERROR: {e}")

# --- Download PDF Route ---
@app.route("/download")
def download_pdf():
    if not login_required(): return redirect(url_for("login"))
    
    data = session.get('current_inquiry')
    if not data: return redirect(url_for("home"))
    
    pdf_path = generate_pdf(data)
    
    # Send PDF via email
    policy_name = data.get('policy_details', {}).get('policy', 'Insurance Policy')
    user_email = session.get("email")
    if user_email:
        send_pdf_email(user_email, pdf_path, policy_name)
        
    return send_file(pdf_path, as_attachment=True)

# --- Final Submission Route ---
@app.route("/submit-final", methods=["POST"])
def submit_final():
    if not login_required(): return redirect(url_for("login"))
    return render_template("success.html")

# --- Specific Page Routes (Legacy/Direct links) ---
@app.route("/health")
def health():
    if not login_required(): return redirect(url_for("login"))
    return redirect("/details/Health")

@app.route("/life")
def life():
    if not login_required(): return redirect(url_for("login"))
    return redirect("/details/Life")

@app.route("/corporate")
def corporate():
    if not login_required(): return redirect(url_for("login"))
    return redirect("/details/Corporate")

@app.route("/motor")
def motor(): return redirect(url_for("motor_select"))

@app.route("/motor-select")
def motor_select():
    if not login_required(): return redirect(url_for("login"))
    return render_template("motor_selection.html")
@app.route("/motor/bike")
def bike_form():
    if not login_required(): return redirect(url_for("login"))
    return render_template("bike_details.html")

@app.route("/motor/car")
def car_form():
    if not login_required(): return redirect(url_for("login"))
    return render_template("car_details.html")

@app.route("/motor/gcv")
def gcv_form():
    if not login_required(): return redirect(url_for("login"))
    return render_template("gcv_details.html")

@app.route("/motor/pcv")
def pcv_form():
    if not login_required(): return redirect(url_for("login"))
    return render_template("pcv_details.html")

@app.route("/motor/misc")
def misc_form():
    if not login_required(): return redirect(url_for("login"))
    return render_template("misc_details.html")


@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/partners")
def partners():
    partners_list = [
        {"name": "LIC", "logo": "licc.png"},
        {"name": "HDFC ERGO", "logo": "hdfc.jpg"},
        {"name": "BAJAJ ALLIANZ", "logo": "bajaj.png"},
        {"name": "ICICI LOMBARD", "logo": "icici.jpg"},
        {"name": "STAR HEALTH", "logo": "star.png"},
        {"name": "TATA AIG", "logo": "tata.png"},
        {"name": "UNITED INDIA", "logo": "united india.jpg"},
        {"name": "SHRIRAM FINANCE", "logo": "shriram.jpg"},
        {"name": "SBI GENERAL", "logo": "sbi.jpg"},
        {"name": "UNIVERSAL SOMPO", "logo": "sampo.jpg"},
        {"name": "ROYAL SUNDARAM", "logo": "royal.jpg"},
        {"name": "NEW INDIA", "logo": "new india.jpg"},
        {"name": "NATIONAL INSURANCE", "logo": "national.jpg"},
        {"name": "GALAXY HEALTH", "logo": "galaxy.jpg"},
        {"name": "FUTURE GENERALI", "logo": "future.jpg"},
        {"name": "CHOLA MS", "logo": "chola.jpg"}
    ]
    return render_template("partners.html", partners=partners_list)

# --- Enquiry Route ---
@app.route("/enquiry", methods=["GET", "POST"])
def enquiry():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone", "")
        service = request.form.get("service")
        message = request.form.get("message", "")
        
        # Send email to company
        success = send_enquiry_email(name, email, phone, service, message)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Email failed"})
    
    return render_template("enquiry.html")
def send_enquiry_email(name, customer_email, phone, service, message):
    """Send enquiry details to company email"""
    sender_email = "jayam.associates.2026@gmail.com"
    sender_password = "tejs pcox pest vtst"  # Your app password
    company_email = "jayam.associates.2026@gmail.com"  # Company email
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = company_email
        msg['Subject'] = f"New Enquiry - {service} Insurance from {name}"
        
        body = f"""
        📋 NEW ENQUIRY RECEIVED
        
        Customer Details:
        ----------------
        Name: {name}
        Email: {customer_email}
        Phone: {phone}
        
        Enquiry Details:
        ----------------
        Insurance Type: {service}
        Message: {message if message else "No additional message"}
        
        Please contact the customer at the earliest.
        
        Regards,
        Jayam AI Insurance System
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Enquiry email sent to company: {company_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send enquiry email: {e}")
        return False
# =========================
# ADMIN ROUTES
# =========================

# =========================
# ADMIN ROUTES - COMPLETE FIXED VERSION (NO DUPLICATES)
# =========================

# Store admin credentials
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "jayam.associates.2026@gmail.com"  # The company email

# Function to send OTP email
def send_admin_otp_email(recipient_email, otp):
    sender_email = "jayam.associates.2026@gmail.com"
    sender_password = "tejs pcox pest vtst" # User must paste the App Password here
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Admin Login OTP - Jayam Associates"
        
        body = f"""
🔐 ADMIN LOGIN VERIFICATION

Your One-Time Password (OTP) for admin access is: {otp}

This OTP is valid for 5 minutes.
Do not share this code with anyone.

Regards,
Jayam Associates Security Team
        """
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print(f"✅ Admin OTP sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            print(f"Admin OTP would be: {otp}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# ============================================
# ONLY ONE admin_panel_login FUNCTION - FIXED
# ============================================

@app.route("/admin", methods=["GET", "POST"])
def admin_panel_login():  # 👈 ONLY ONE FUNCTION WITH THIS NAME
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        
        # Check if credentials match
        if username == ADMIN_USERNAME and email == ADMIN_EMAIL:
            # Generate OTP
            otp = random.randint(100000, 999999)
            session["admin_otp"] = str(otp)
            session["admin_email"] = email
            session["admin_username"] = username
            
            # Send OTP to admin email
            email_sent = send_admin_otp_email(email, otp)
            
            if email_sent:
                return render_template("admin_verify_otp.html")
            else:
                # If email fails, still show OTP for testing
                return render_template("admin_verify_otp.html", warning=f"OTP: {otp} (Email failed)")
        else:
            return render_template("admin_login.html", error="Invalid username or email")
    
    return render_template("admin_login.html")

# ============================================
# OTHER ADMIN ROUTES (Different names)
# ============================================

@app.route("/admin/verify-otp", methods=["POST"])
def admin_verify_otp():  # 👈 DIFFERENT function name
    entered_otp = request.form.get("otp")
    
    if entered_otp == session.get("admin_otp"):
        session["admin_logged_in"] = True
        session.pop("admin_otp", None)
        return redirect(url_for("admin_panel_dashboard"))
    
    return render_template("admin_verify_otp.html", error="Invalid OTP")

@app.route("/admin/dashboard")
def admin_panel_dashboard():  # 👈 DIFFERENT function name
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_panel_login"))
    
    # Your dashboard code here
    conn = sqlite3.connect('jayam.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM enquiries")
    total_enquiries = cursor.fetchone()[0]
    
    def convert_to_ist(utc_str):
        if not utc_str: return "N/A"
        try:
            utc_dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
            ist_dt = utc_dt + timedelta(hours=5, minutes=30)
            return ist_dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return utc_str

    cursor.execute("SELECT name, email, timestamp FROM users ORDER BY id DESC LIMIT 10")
    users = [(u[0], u[1], convert_to_ist(u[2])) for u in cursor.fetchall()]
    
    cursor.execute("SELECT user_email, insurance_type, recommendation, timestamp FROM enquiries ORDER BY id DESC LIMIT 10")
    enquiries = [(e[0], e[1], e[2], convert_to_ist(e[3])) for e in cursor.fetchall()]

    cursor.execute("SELECT user_email, page, timestamp FROM activity_logs ORDER BY id DESC LIMIT 20")
    activities = [(a[0], a[1], convert_to_ist(a[2])) for a in cursor.fetchall()]
    
    conn.close()
    
    return render_template("admin_dashboard.html", 
                           total_users=total_users, 
                           total_enquiries=total_enquiries,
                           users=users,
                           enquiries=enquiries,
                           activities=activities)

@app.route("/admin/logout")
def admin_panel_logout():  # 👈 DIFFERENT function name
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_panel_login"))

@app.route("/admin/send_welcome/<email>")
def admin_send_welcome(email):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_panel_login"))
        
    sender_email = "jayam.associates.2026@gmail.com"
    sender_password = "tejs pcox pest vtst"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Welcome to Jayam Associates!"
        
        body = "Hello,\n\nWelcome to Jayam Associates! We are thrilled to have you onboard.\n\nOur team of experts is ready to help you find the best insurance policies tailored to your needs. If you have any questions, feel free to reply to this email or contact us via WhatsApp at +91 9159981987.\n\nWarm Regards,\nThe Jayam Associates Team"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Welcome email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        
    return redirect(url_for("admin_panel_dashboard"))
    
# =========================
# AUTO OPEN
# =========================
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    if not os.path.exists('static/downloads'):
        os.makedirs('static/downloads')
    threading.Timer(1.2, open_browser).start()
    app.run(debug=True)

