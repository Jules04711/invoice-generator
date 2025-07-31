import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF
import os
import tempfile
import webbrowser
from datetime import datetime, timedelta
import urllib.request
import uuid
import base64
from io import BytesIO
import requests
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        # Add home button in upper left corner
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.markdown("""
            <div style='text-align: left; margin-bottom: 20px;'>
                <a href='https://jmartin.consulting/' target='_blank' style='text-decoration: none;'>
                    <button style='background-color: #000000; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px;'>
                        Home
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        st.title("Invoice Generator Login")
        
        # Create login form at the top
        # Create columns to control width and alignment
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Login")
            
            if submit_button:
                # Prevent double-clicking by checking if already processing
                if 'login_processing' not in st.session_state:
                    st.session_state.login_processing = True
                    
                    correct_username = os.getenv('USERNAME')
                    correct_password = os.getenv('PASSWORD')
                    if username == correct_username and password == correct_password:
                        st.session_state.authenticated = True
                        st.success("Login successful! Redirecting...")
                        # Clear processing flag and rerun
                        del st.session_state.login_processing
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please try again.")
                        # Clear processing flag
                        del st.session_state.login_processing
        
        # Add HubSpot form below the login form
        st.markdown("---")
        st.markdown("### Get Access Credentials")
        st.markdown("Enter your contact information below to receive your username and password for accessing the Invoice Generator:")
        
        # HubSpot form - using components.html for better JavaScript support
        components.html("""
        <div style="width: 80%; max-width: 360px; margin: 0; padding: 30px; border: 2px solid #ddd; border-radius: 12px; background-color: #FFFFFF;">
            <script src="https://js-na2.hsforms.net/forms/embed/242871477.js" defer></script>
            <div class="hs-form-frame" data-region="na2" data-form-id="22ac7aab-b257-4485-a306-965a060bcc27" data-portal-id="242871477"></div>
        </div>
        """, height=600)
        
        st.markdown("---")
        
        # App information section
        st.markdown("""
            ### About Invoice Generator
            **Invoice Generator** is a Streamlit web application that allows users to easily create professional PDF invoices for clients.
            
            ### Features
            - Create customized invoices with your company information
            - Add client details and multiple service items
            - Customize tax rates and discounts
            - Add custom notes to invoices
            - Upload your company logo or use the default
            - Preview and download generated invoices as PDF
            
            ### How to Use
            Once logged in, follow these steps to create an invoice:
            1. **Company Info tab**: Enter your company details and upload a logo if needed
            2. **Client Info tab**: Add client information and invoice number
            3. **Invoice Items tab**: Add service items with descriptions, hours, and rates
            4. **Notes & Options tab**: Customize invoice notes, tax rate, and discount
            5. **Generate Invoice tab**: Generate the invoice, preview it, and download as PDF
            
            ### Project Information
            - **Repository**: [GitHub - Jules04711/invoice-generator](https://github.com/Jules04711/invoice-generator)
            - **License**: MIT License - Open source and available for personal and commercial use
            - **Requirements**: Python 3.7+, Streamlit, FPDF, Pillow, Requests
            
            ---
            """)
        
        # Legal disclaimer footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; font-size: 12px; color: #666; margin-top: 20px;'>
            <p><strong>Legal Disclaimer:</strong> This application is provided for general informational purposes only. 
            All information is provided in good faith; however, we make no representation or warranty of any kind regarding 
            the accuracy, adequacy, validity, reliability, availability, or completeness of any information presented. 
            Your use of this application is solely at your own risk. 
            <a href='https://jmartin.consulting/disclaimer/' target='_blank'><br>View full legal disclaimer</a></p>
            <p style='margin-top: 10px;'>© 2025 J. Martin Consulting LLC. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.stop()
    
    return True

class InvoiceGenerator:
    def __init__(self, company_name, company_address, logo=None):
        self.company_name = company_name
        self.company_address = company_address
        self.logo_path = None
        
        # Create a temporary file for the logo
        temp_dir = tempfile.gettempdir()
        self.logo_path = os.path.join(temp_dir, f"logo_{uuid.uuid4()}.png")
        
        # If custom logo is provided, use it
        if logo is not None:
            try:
                # Convert the uploaded image to PNG format
                image = Image.open(BytesIO(logo.getvalue()))
                # Convert to RGB if needed (handling RGBA or other formats)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                # Save as PNG explicitly with proper format
                image_bytes = BytesIO()
                image.save(image_bytes, format='PNG')
                # Save the processed image to the temporary file
                with open(self.logo_path, "wb") as f:
                    f.write(image_bytes.getvalue())
            except Exception as e:
                print(f"Error processing logo: {e}")
                self.logo_path = None
        else:
            # Use default logo from the asset folder
            try:
                # Save default logo to the temporary file
                with open(self.logo_path, "wb") as f:
                    with open('asset/logo.png', 'rb') as default_logo:
                        f.write(default_logo.read())
            except Exception as e:
                # If default logo file doesn't exist, use a fallback method
                print(f"Error loading default logo: {e}")
                self.logo_path = None
    
    def generate_invoice(self, invoice_number, client_name, client_address, client_email, 
                         items, notes=None, tax_rate=6.0, discount=0.0, invoice_date=None, due_date=None,
                         services_heading="Services", column_names=None):
        """
        Generate a PDF invoice
        
        Parameters:
        - invoice_number: Invoice identifier
        - client_name: Name of the client
        - client_address: Address of the client
        - client_email: Email of the client
        - items: List of dictionaries with keys 'service_item', 'description', 'hours', 'rate'
        - notes: Additional notes to include on the invoice
        - tax_rate: Tax rate percentage
        - discount: Discount percentage
        - invoice_date: Invoice date (datetime.date object)
        - due_date: Due date (datetime.date object)
        - services_heading: Custom heading for the services section
        - column_names: Dictionary of custom column names {'service_item', 'description', 'hours', 'rate', 'amount'}
        
        Returns:
        - PDF bytes
        """
        # Create PDF object
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Set default column names if not provided
        if column_names is None:
            column_names = {
                'service_item': 'Service Item',
                'description': 'Description',
                'hours': 'Hours',
                'rate': 'Rate ($)',
                'amount': 'Amount ($)'
            }
        
        # Set font
        pdf.set_font('helvetica', '', 10)
        
        # Colors
        teal_color = (0, 156, 166)
        dark_blue = (0, 51, 102)
        light_gray = (240, 240, 240)
        
        # Add logo if available
        if self.logo_path:
            pdf.image(self.logo_path, x=10, y=10, w=30)
        
        # Company information - positioned to the right of the logo
        pdf.set_xy(45, 10)  # Set position after the logo
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(*dark_blue)
        pdf.cell(0, 10, self.company_name, ln=True)
        
        pdf.set_x(45)  # Keep the x position for address lines
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(80, 80, 80)
        for line in self.company_address.split('\n'):
            pdf.set_x(45)  # Reset x position before each line
            pdf.cell(0, 5, line, ln=True)
        
        # Invoice title and details
        pdf.ln(10)
        pdf.set_fill_color(*teal_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, 'INVOICE', ln=True, fill=True)
        
        # Invoice details
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('helvetica', 'B', 10)
        
        # Current date and due date (30 days from now)
        if invoice_date:
            current_date = invoice_date.strftime('%Y-%m-%d')
        else:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        if due_date:
            due_date_str = due_date.strftime('%Y-%m-%d')
        else:
            due_date_str = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        pdf.ln(5)
        pdf.cell(30, 7, 'Invoice #:', 0)
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 7, invoice_number, ln=True)
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(30, 7, 'Date:', 0)
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 7, current_date, ln=True)
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(30, 7, 'Due Date:', 0)
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 7, due_date_str, ln=True)
        
        # Client information
        pdf.ln(10)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 7, 'Bill To:', ln=True)
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 7, client_name, ln=True)
        
        pdf.set_font('helvetica', '', 10)
        for line in client_address.split('\n'):
            pdf.cell(0, 5, line, ln=True)
        
        pdf.cell(0, 5, client_email, ln=True)
        
        # Services table
        pdf.ln(10)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 7, services_heading, ln=True)
        
        # Table header
        pdf.set_fill_color(*light_gray)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(25, 7, column_names['service_item'], 1, 0, 'L', True)
        pdf.cell(65, 7, column_names['description'], 1, 0, 'L', True)
        pdf.cell(30, 7, column_names['hours'], 1, 0, 'R', True)
        pdf.cell(30, 7, column_names['rate'], 1, 0, 'R', True)
        pdf.cell(40, 7, column_names['amount'], 1, 1, 'R', True)
        
        # Table content
        pdf.set_font('helvetica', '', 10)
        subtotal = 0.0
        
        for item in items:
            service_item = item.get('service_item', '')
            description = item['description']
            
            # Check if it's a fixed amount item or hours/rate calculation
            if item.get('amount') is not None:
                amount = float(item['amount'])
                hours_display = 'N/A'
                rate_display = 'N/A'
            else:
                hours = float(item['hours'])
                rate = float(item['rate'])
                amount = hours * rate
                hours_display = f"{hours:.2f}"
                rate_display = f"{rate:.2f}"
                
            subtotal += amount
            
            pdf.cell(25, 7, service_item, 1)
            pdf.cell(65, 7, description, 1)
            pdf.cell(30, 7, hours_display, 1, 0, 'R')
            pdf.cell(30, 7, rate_display, 1, 0, 'R')
            pdf.cell(40, 7, f"{amount:,.2f}", 1, 1, 'R')
        
        # Calculate tax and total
        tax_rate = float(tax_rate)
        discount_rate = float(discount)
        discount_amount = subtotal * (discount_rate / 100)
        discounted_subtotal = subtotal - discount_amount
        tax = discounted_subtotal * (tax_rate / 100)
        total = discounted_subtotal + tax
        
        # Totals
        pdf.ln(5)
        pdf.set_x(120)  # Position closer to the right margin
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(30, 7, 'Subtotal:', 0, 0, 'R')
        pdf.set_font('helvetica', '', 10)
        pdf.cell(40, 7, f"${subtotal:,.2f}", 0, 1, 'R')
        
        if discount_rate > 0:
            pdf.set_x(120)  # Position closer to the right margin
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(30, 7, f'Discount ({discount_rate}%):', 0, 0, 'R')
            pdf.set_font('helvetica', '', 10)
            pdf.cell(40, 7, f"-${discount_amount:,.2f}", 0, 1, 'R')
            
            pdf.set_x(120)  # Position closer to the right margin
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(30, 7, 'Subtotal after discount:', 0, 0, 'R')
            pdf.set_font('helvetica', '', 10)
            pdf.cell(40, 7, f"${discounted_subtotal:,.2f}", 0, 1, 'R')
        
        pdf.set_x(120)  # Position closer to the right margin
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(30, 7, f'Tax ({tax_rate}%):', 0, 0, 'R')
        pdf.set_font('helvetica', '', 10)
        pdf.cell(40, 7, f"${tax:,.2f}", 0, 1, 'R')
        
        pdf.set_draw_color(200, 200, 200)
        pdf.line(120, pdf.get_y(), 190, pdf.get_y())
        
        pdf.set_x(120)  # Position closer to the right margin
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(30, 10, 'Total:', 0, 0, 'R')
        pdf.cell(40, 10, f"${total:,.2f}", 0, 1, 'R')
        
        # Notes
        if notes:
            pdf.ln(10)
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(0, 7, 'Notes:', ln=True)
            pdf.set_font('helvetica', '', 10)
            pdf.multi_cell(0, 5, notes)
        
        # Footer
        pdf.ln(15)
        pdf.set_font('helvetica', 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, 'Thank you for your business!', 0, 1, 'C')
        pdf.cell(0, 5, self.company_name, 0, 1, 'C')
        
        # Get the PDF as bytes
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        
        # Clean up the logo file
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                os.remove(self.logo_path)
            except:
                pass
        
        return pdf_bytes

def create_download_link(pdf_bytes, filename="invoice.pdf"):
    """Generate a link to download the PDF file"""
    b64 = base64.b64encode(pdf_bytes).decode("latin1")
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download Invoice PDF</a>'
    return href

# Set page config with mobile-friendly settings
st.set_page_config(
    page_title="Invoice Generator", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add mobile-friendly CSS
st.markdown("""
<style>
    /* Mobile-friendly button styling */
    .stButton > button {
        min-height: 44px; /* iOS minimum touch target */
        padding: 12px 24px;
        font-size: 16px;
        border-radius: 8px;
        border: 2px solid #4CAF50;
        background-color: #4CAF50;
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
        -webkit-tap-highlight-color: transparent;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Mobile-friendly form inputs */
    .stTextInput > div > div > input {
        min-height: 44px;
        font-size: 16px;
        padding: 12px;
    }
    
    .stNumberInput > div > div > input {
        min-height: 44px;
        font-size: 16px;
        padding: 12px;
    }
    
    /* Mobile-friendly file uploader */
    .stFileUploader > div {
        min-height: 44px;
    }
    
    /* Prevent double-tap zoom on mobile */
    * {
        touch-action: manipulation;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication first
check_authentication()

# Create a header with title and logout button
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.title("Invoice Generator")
with col3:
    st.write("")  # Add some spacing
    if st.button("Logout", key="logout_button"):
        # Prevent double-clicking by checking if already processing
        if 'logout_processing' not in st.session_state:
            st.session_state.logout_processing = True
            st.session_state.authenticated = False
            st.success("Logged out successfully!")
            # Clear processing flag and rerun
            del st.session_state.logout_processing
            st.rerun()

st.write("Create an Invoice for your Clients:")

# Initialize session state for all parameters
if 'company_name' not in st.session_state:
    st.session_state.company_name = "ABC123 INC"
if 'company_address' not in st.session_state:
    st.session_state.company_address = "123 Broadway\nNew York, NY 10004 \ninvoice@abc123inc.com\n(555) 555-5555"
if 'uploaded_logo' not in st.session_state:
    st.session_state.uploaded_logo = None
if 'invoice_number' not in st.session_state:
    st.session_state.invoice_number = "INV-001"
if 'client_name' not in st.session_state:
    st.session_state.client_name = "Acme Corporation"
if 'client_address' not in st.session_state:
    st.session_state.client_address = "123 Business Ave\nEnterprise City, CA 90210"
if 'client_email' not in st.session_state:
    st.session_state.client_email = "billing@acmecorp.com"
if 'items' not in st.session_state:
    st.session_state['items'] = [
        {"service_item": "AI-001", "description": "AI Workflow Development", "hours": 12, "rate": 150, "amount": None},
        {"service_item": "LLM-001", "description": "LLM Systems Integration", "hours": 8, "rate": 175, "amount": None},
        {"service_item": "CONS-001", "description": "Implementation Consulting", "hours": 8, "rate": 175, "amount": None}
    ]
if 'notes' not in st.session_state:
    st.session_state.notes = "Payment is due within 30 days. Please make checks payable to ABC123 INC."
if 'tax_rate' not in st.session_state:
    st.session_state.tax_rate = 6.0
if 'discount' not in st.session_state:
    st.session_state.discount = 0.0
if 'service_item_col' not in st.session_state:
    st.session_state.service_item_col = "Service Item"
if 'description_col' not in st.session_state:
    st.session_state.description_col = "Description"
if 'hours_col' not in st.session_state:
    st.session_state.hours_col = "Hours"
if 'rate_col' not in st.session_state:
    st.session_state.rate_col = "Rate ($)"
if 'amount_col' not in st.session_state:
    st.session_state.amount_col = "Amount ($)"
if 'services_heading' not in st.session_state:
    st.session_state.services_heading = "Services"

# Function to update column name in session state
def update_service_heading():
    st.session_state.services_heading = st.session_state.services_heading_input

def update_service_item_col():
    st.session_state.service_item_col = st.session_state.service_item_col_input

def update_description_col():
    st.session_state.description_col = st.session_state.description_col_input
    
def update_hours_col():
    st.session_state.hours_col = st.session_state.hours_col_input
    
def update_rate_col():
    st.session_state.rate_col = st.session_state.rate_col_input
    
def update_amount_col():
    st.session_state.amount_col = st.session_state.amount_col_input

# Create tabs for company info, client info, items, and preview
tabs = st.tabs(["Company Info", "Client Info", "Options and Notes", "Invoice Items", "Generate Invoice"])

# Company Info Tab
with tabs[0]:
    st.header("Company Information")
    
    company_name = st.text_input("Company Name", value=st.session_state.company_name)
    company_address = st.text_area("Company Address", value=st.session_state.company_address, height=100)
    
    # Display the default logo image
    st.write("Default Logo:")
    try:
        st.image('asset/logo.png', width=150)
    except Exception as e:
        st.write(f"Default logo image not found. Error: {e}")
    
    company_logo = st.file_uploader("Upload Custom Logo (optional)", type=["png", "jpg", "jpeg"], key="company_logo_uploader")
    if company_logo:
        st.image(company_logo, width=150, caption="Custom Logo Preview")
        # Store the uploaded file in session state for persistence across tabs
        st.session_state['uploaded_logo'] = company_logo
    elif st.session_state.get('uploaded_logo') is not None:
        # Show previously uploaded logo if current uploader is empty
        st.image(st.session_state['uploaded_logo'], width=150, caption="Previously Uploaded Logo")
    
    # Save to session state
    if st.button("Save Company Info", key="save_company_info"):
        # Prevent double-clicking by checking if already processing
        if 'save_company_processing' not in st.session_state:
            st.session_state.save_company_processing = True
            
            st.session_state.company_name = company_name
            st.session_state.company_address = company_address
            
            # Update notes with the new company name
            current_notes = st.session_state.notes
            # Replace the old company name with the new one in the notes
            if "Please make checks payable to" in current_notes:
                # Extract the part before "Please make checks payable to"
                before_part = current_notes.split("Please make checks payable to")[0]
                # Create new notes with updated company name
                st.session_state.notes = f"{before_part}Please make checks payable to {company_name}."
            
            st.success("Company information saved!")
            # Clear processing flag
            del st.session_state.save_company_processing

# Client Info Tab
with tabs[1]:
    st.header("Client Information")
    
    invoice_number = st.text_input("Invoice Number", value=st.session_state.invoice_number)
    client_name = st.text_input("Client Name", value=st.session_state.client_name)
    client_address = st.text_area("Client Address", value=st.session_state.client_address, height=100)
    client_email = st.text_input("Client Email", value=st.session_state.client_email)
    
    # Save to session state
    if st.button("Save Client Info", key="save_client_info"):
        # Prevent double-clicking by checking if already processing
        if 'save_client_processing' not in st.session_state:
            st.session_state.save_client_processing = True
            
            st.session_state.invoice_number = invoice_number
            st.session_state.client_name = client_name
            st.session_state.client_address = client_address
            st.session_state.client_email = client_email
            st.success("Client information saved!")
            # Clear processing flag
            del st.session_state.save_client_processing

# Invoice Items Tab
with tabs[3]:
    st.header("Invoice Items")
    
    # Reset items if it's not a list
    if not isinstance(st.session_state.get('items'), list):
        st.session_state['items'] = [
            {"service_item": "AI-001", "description": "AI Workflow Development", "hours": 12, "rate": 150, "amount": None},
            {"service_item": "LLM-001", "description": "LLM Systems Integration", "hours": 8, "rate": 175, "amount": None},
            {"service_item": "CONS-001", "description": "Implementation Consulting", "hours": 8, "rate": 175, "amount": None}
        ]
    
    # Get items from session state
    items = st.session_state['items']
    
    # Get custom column names from session state
    service_item_label = st.session_state.get('service_item_col', 'Service Item')
    description_label = st.session_state.get('description_col', 'Description')
    hours_label = st.session_state.get('hours_col', 'Hours')
    rate_label = st.session_state.get('rate_col', 'Rate ($)')
    amount_label = st.session_state.get('amount_col', 'Amount ($)')
    
    # Display existing items
    for i, item in enumerate(items):
        st.write(f"**Item #{i+1}**")
        
        # Add a select box to choose between hours/rate or fixed amount - moved above fields
        calc_method = "hours_rate"
        if item.get("amount") is not None and (item.get("hours") is None or item.get("rate") is None):
            calc_method = "fixed_amount"
        
        calc_method = st.radio(f"Calculation method for item #{i+1}", 
                               ["Hours & Rate", "Fixed Amount"], 
                               index=0 if calc_method == "hours_rate" else 1,
                               horizontal=True, key=f"calc_method_{i}")
        
        cols = st.columns([1, 3, 1, 1, 1])
        with cols[0]:
            st.text_input(f"{service_item_label} #{i+1}", value=item.get("service_item", ""), key=f"service_{i}")
        with cols[1]:
            st.text_input(f"{description_label} #{i+1}", value=item["description"], key=f"desc_{i}")
        
        # Display fields based on calculation method
        if calc_method == "Hours & Rate":
            with cols[2]:
                st.number_input(f"{hours_label} #{i+1}", value=float(item.get("hours", 0)), step=0.5, format="%.2f", key=f"hours_{i}")
            with cols[3]:
                st.number_input(f"{rate_label} #{i+1}", value=float(item.get("rate", 0)), step=10.0, format="%.2f", key=f"rate_{i}")
            with cols[4]:
                # Display calculated amount (read-only)
                hours = float(st.session_state.get(f"hours_{i}", 0))
                rate = float(st.session_state.get(f"rate_{i}", 0))
                calculated_amount = hours * rate
                st.text_input(f"{amount_label} #{i+1}", value=f"${calculated_amount:,.2f}", disabled=True, key=f"calc_amount_{i}")
        else:
            # For fixed amount, disable hours and rate, but show amount field
            with cols[2]:
                st.text_input(f"{hours_label} #{i+1}", value="N/A", disabled=True, key=f"disabled_hours_{i}")
            with cols[3]:
                st.text_input(f"{rate_label} #{i+1}", value="N/A", disabled=True, key=f"disabled_rate_{i}")
            with cols[4]:
                # Fix the error by ensuring we have a valid default value
                amount_value = 0.0
                if item.get("amount") is not None:
                    amount_value = float(item.get("amount"))
                st.number_input(f"{amount_label} #{i+1}", value=amount_value, step=10.0, format="%.2f", key=f"amount_{i}")
        
        # Remove button with some spacing
        if st.button("Remove Item", key=f"remove_{i}"):
            # Prevent double-clicking by checking if already processing
            if f'remove_processing_{i}' not in st.session_state:
                st.session_state[f'remove_processing_{i}'] = True
                
                items_copy = list(items)  # Create a copy
                items_copy.pop(i)
                st.session_state['items'] = items_copy
                
                # Clear processing flag and rerun
                del st.session_state[f'remove_processing_{i}']
                st.rerun()
        st.markdown("---")  # Add a separator between items
    
    # Add new item button
    if st.button("Add New Item", key="add_new_item"):
        # Prevent double-clicking by checking if already processing
        if 'add_item_processing' not in st.session_state:
            st.session_state.add_item_processing = True
            
            items_copy = list(items)  # Create a copy
            items_copy.append({"service_item": "", "description": "", "hours": 1, "rate": 100, "amount": None})
            st.session_state['items'] = items_copy
            
            # Clear processing flag and rerun
            del st.session_state.add_item_processing
            st.rerun()
    
    # Save items
    if st.button("Save Items", key="save_items_button"):
        # Prevent double-clicking by checking if already processing
        if 'save_items_processing' not in st.session_state:
            st.session_state.save_items_processing = True
            
            updated_items = []
            for i in range(len(items)):
                calc_method = st.session_state.get(f"calc_method_{i}")
                if calc_method == "Hours & Rate":
                    updated_items.append({
                        "service_item": st.session_state[f"service_{i}"],
                        "description": st.session_state[f"desc_{i}"],
                        "hours": float(st.session_state[f"hours_{i}"]),
                        "rate": float(st.session_state[f"rate_{i}"]),
                        "amount": None
                    })
                else:
                    updated_items.append({
                        "service_item": st.session_state[f"service_{i}"],
                        "description": st.session_state[f"desc_{i}"],
                        "hours": None,
                        "rate": None,
                        "amount": float(st.session_state[f"amount_{i}"])
                    })
            st.session_state['items'] = updated_items
            st.success("Invoice items saved!")
            # Clear processing flag
            del st.session_state.save_items_processing

# Options & Notes Tab
with tabs[2]:
    st.header("Options and Notes")
    
    # Add column for custom headings and column names
    st.subheader("Custom Invoice Table Labels")
    
    # Use a smaller column width for the section heading
    col1, _ = st.columns([2, 6])  # Use 2/8 = 25% of the width
    with col1:
        services_heading = st.text_input("Section Heading", 
                                       value=st.session_state.services_heading, 
                                       key="services_heading_input",
                                       on_change=update_service_heading)
    
    st.markdown("**Custom Column Names:**")
    cols = st.columns(5)  # Create 5 equal columns for each input field
    
    with cols[0]:
        service_item_col = st.text_input("Service Item", 
                                       value=st.session_state.service_item_col,
                                       key="service_item_col_input",
                                       on_change=update_service_item_col)
    with cols[1]:
        description_col = st.text_input("Description", 
                                      value=st.session_state.description_col,
                                      key="description_col_input",
                                      on_change=update_description_col)
    with cols[2]:
        hours_col = st.text_input("Hours", 
                                value=st.session_state.hours_col,
                                key="hours_col_input",
                                on_change=update_hours_col)
    with cols[3]:
        rate_col = st.text_input("Rate", 
                               value=st.session_state.rate_col,
                               key="rate_col_input",
                               on_change=update_rate_col)
    with cols[4]:
        amount_col = st.text_input("Amount", 
                                 value=st.session_state.amount_col,
                                 key="amount_col_input",
                                 on_change=update_amount_col)
    
    st.markdown("---")
    st.subheader("Invoice Notes and Settings")
    
    # Create dynamic default text with company name
    company_name_for_notes = st.session_state.get('company_name', 'Your Company')
    dynamic_default = f"Payment is due within 30 days. Please make checks payable to {company_name_for_notes}."
    
    # Use the dynamic default if notes are empty or contain the old placeholder
    current_notes = st.session_state.notes
    
    # If the current notes contain the old placeholder, update to the new dynamic version
    if '[Company Name]' in current_notes:
        current_notes = current_notes.replace('[Company Name]', company_name_for_notes)
        st.session_state.notes = current_notes
    
    notes = st.text_area("Notes", value=current_notes, height=100, 
                        placeholder=dynamic_default,
                        help=f"Default note includes your company name: {company_name_for_notes}")
    tax_rate = st.number_input("Tax Rate (%)", value=st.session_state.tax_rate, min_value=0.0, step=0.1)
    discount = st.number_input("Discount (%)", value=st.session_state.discount, min_value=0.0, max_value=100.0, step=0.1)
    
    # Add date fields
    if 'invoice_date' not in st.session_state:
        st.session_state.invoice_date = datetime.now().date()
    if 'due_date' not in st.session_state:
        st.session_state.due_date = (datetime.now() + timedelta(days=30)).date()
        
    invoice_date = st.date_input("Invoice Date", value=st.session_state.invoice_date)
    due_date = st.date_input("Due Date", value=st.session_state.due_date)
    
    # Save to session state
    if st.button("Save Options & Notes", key="save_options_notes"):
        # Prevent double-clicking by checking if already processing
        if 'save_options_processing' not in st.session_state:
            st.session_state.save_options_processing = True
            
            st.session_state.notes = notes
            st.session_state.tax_rate = tax_rate
            st.session_state.discount = discount
            st.session_state.invoice_date = invoice_date
            st.session_state.due_date = due_date
            # Save custom headings and column names
            st.session_state.services_heading = services_heading
            st.session_state.service_item_col = service_item_col
            st.session_state.description_col = description_col
            st.session_state.hours_col = hours_col
            st.session_state.rate_col = rate_col
            st.session_state.amount_col = amount_col
            st.success("Options and notes saved!")
            # Clear processing flag
            del st.session_state.save_options_processing

# Preview Tab
with tabs[4]:
    st.header("Invoice Generation")
    
    if st.button("Generate and Download Invoice", key="generate_invoice_button"):
        # Prevent double-clicking by checking if already processing
        if 'generate_invoice_processing' not in st.session_state:
            st.session_state.generate_invoice_processing = True
            
            try:
                # Update items with the latest values
                updated_items = []
                items = st.session_state['items']
                for i in range(len(items)):
                    calc_method = st.session_state.get(f"calc_method_{i}")
                    if calc_method == "Hours & Rate":
                        updated_items.append({
                            "service_item": st.session_state[f"service_{i}"],
                            "description": st.session_state[f"desc_{i}"],
                            "hours": float(st.session_state[f"hours_{i}"]),
                            "rate": float(st.session_state[f"rate_{i}"]),
                            "amount": None
                        })
                    else:
                        updated_items.append({
                            "service_item": st.session_state[f"service_{i}"],
                            "description": st.session_state[f"desc_{i}"],
                            "hours": None,
                            "rate": None,
                            "amount": float(st.session_state[f"amount_{i}"])
                        })
                
                # Create custom column names dictionary
                column_names = {
                    'service_item': st.session_state.get('service_item_col', 'Service Item'),
                    'description': st.session_state.get('description_col', 'Description'),
                    'hours': st.session_state.get('hours_col', 'Hours'),
                    'rate': st.session_state.get('rate_col', 'Rate ($)'),
                    'amount': st.session_state.get('amount_col', 'Amount ($)')
                }
                
                # Get the uploaded logo from session state
                uploaded_logo = st.session_state.get('uploaded_logo', None)
                
                generator = InvoiceGenerator(
                    st.session_state.company_name,
                    st.session_state.company_address,
                    uploaded_logo
                )
                
                pdf_bytes = generator.generate_invoice(
                    invoice_number=st.session_state.invoice_number,
                    client_name=st.session_state.client_name,
                    client_address=st.session_state.client_address,
                    client_email=st.session_state.client_email,
                    items=updated_items,  # Pass the updated items explicitly
                    notes=st.session_state.notes,
                    tax_rate=float(st.session_state.tax_rate),
                    discount=float(st.session_state.discount),
                    invoice_date=st.session_state.invoice_date,
                    due_date=st.session_state.due_date,
                    services_heading=st.session_state.get('services_heading', 'Services'),
                    column_names=column_names
                )
                
                # Create download link
                download_link = create_download_link(pdf_bytes, filename=f"Invoice_{st.session_state.invoice_number}.pdf")
                st.markdown(download_link, unsafe_allow_html=True)
                
                # Display the PDF using a download button
                st.download_button(
                    label="Download Invoice PDF",
                    data=pdf_bytes,
                    file_name=f"Invoice_{st.session_state.invoice_number}.pdf",
                    mime="application/pdf"
                )
                    
                # Display PDF inline
                try:
                    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not display preview: {e}")
                
            except Exception as e:
                st.error(f"Error generating invoice: {str(e)}")
            
            # Clear processing flag
            del st.session_state.generate_invoice_processing 
