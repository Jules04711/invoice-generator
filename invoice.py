import streamlit as st
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
                         items, notes=None, tax_rate=6.0, discount=0.0, invoice_date=None, due_date=None):
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
        
        Returns:
        - PDF bytes
        """
        # Create PDF object
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
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
        pdf.cell(0, 7, 'Services', ln=True)
        
        # Table header
        pdf.set_fill_color(*light_gray)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(25, 7, 'Service Item', 1, 0, 'L', True)
        pdf.cell(65, 7, 'Description', 1, 0, 'L', True)
        pdf.cell(30, 7, 'Hours', 1, 0, 'R', True)
        pdf.cell(30, 7, 'Rate ($)', 1, 0, 'R', True)
        pdf.cell(40, 7, 'Amount ($)', 1, 1, 'R', True)
        
        # Table content
        pdf.set_font('helvetica', '', 10)
        subtotal = 0.0
        
        for item in items:
            service_item = item.get('service_item', '')
            description = item['description']
            hours = float(item['hours'])
            rate = float(item['rate'])
            amount = hours * rate
            subtotal += amount
            
            pdf.cell(25, 7, service_item, 1)
            pdf.cell(65, 7, description, 1)
            pdf.cell(30, 7, f"{hours:.2f}", 1, 0, 'R')
            pdf.cell(30, 7, f"{rate:.2f}", 1, 0, 'R')
            pdf.cell(40, 7, f"{amount:.2f}", 1, 1, 'R')
        
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
        pdf.cell(40, 7, f"${subtotal:.2f}", 0, 1, 'R')
        
        if discount_rate > 0:
            pdf.set_x(120)  # Position closer to the right margin
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(30, 7, f'Discount ({discount_rate}%):', 0, 0, 'R')
            pdf.set_font('helvetica', '', 10)
            pdf.cell(40, 7, f"-${discount_amount:.2f}", 0, 1, 'R')
            
            pdf.set_x(120)  # Position closer to the right margin
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(30, 7, 'Subtotal after discount:', 0, 0, 'R')
            pdf.set_font('helvetica', '', 10)
            pdf.cell(40, 7, f"${discounted_subtotal:.2f}", 0, 1, 'R')
        
        pdf.set_x(120)  # Position closer to the right margin
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(30, 7, f'Tax ({tax_rate}%):', 0, 0, 'R')
        pdf.set_font('helvetica', '', 10)
        pdf.cell(40, 7, f"${tax:.2f}", 0, 1, 'R')
        
        pdf.set_draw_color(200, 200, 200)
        pdf.line(120, pdf.get_y(), 190, pdf.get_y())
        
        pdf.set_x(120)  # Position closer to the right margin
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(30, 10, 'Total:', 0, 0, 'R')
        pdf.cell(40, 10, f"${total:.2f}", 0, 1, 'R')
        
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

# Set page config
st.set_page_config(page_title="Invoice Generator", layout="wide")

# App title and description
st.title("Invoice Generator")
st.write("Create an Invoice for your Clients:")

# Initialize session state for all parameters
if 'company_name' not in st.session_state:
    st.session_state.company_name = "ABC123 INC"
if 'company_address' not in st.session_state:
    st.session_state.company_address = "123 Broadway\nNew York, NY 10004 \ninvoice@abc123inc.com\n(555) 555-5555"
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
        {"service_item": "AI-001", "description": "AI Workflow Development", "hours": 12, "rate": 150},
        {"service_item": "LLM-001", "description": "LLM Systems Integration", "hours": 8, "rate": 175},
        {"service_item": "CONS-001", "description": "Implementation Consulting", "hours": 8, "rate": 175}
    ]
if 'notes' not in st.session_state:
    st.session_state.notes = "Payment is due within 30 days. Please make checks payable to ABC123 INC"
if 'tax_rate' not in st.session_state:
    st.session_state.tax_rate = 6.0
if 'discount' not in st.session_state:
    st.session_state.discount = 0.0

# Create tabs for company info, client info, items, and preview
tabs = st.tabs(["Company Info", "Client Info", "Invoice Items", "Notes & Options", "Preview"])

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
    
    company_logo = st.file_uploader("Upload Custom Logo (optional)", type=["png", "jpg", "jpeg"])
    if company_logo:
        st.image(company_logo, width=150, caption="Custom Logo Preview")
    
    # Save to session state
    if st.button("Save Company Info"):
        st.session_state.company_name = company_name
        st.session_state.company_address = company_address
        st.success("Company information saved!")

# Client Info Tab
with tabs[1]:
    st.header("Client Information")
    
    invoice_number = st.text_input("Invoice Number", value=st.session_state.invoice_number)
    client_name = st.text_input("Client Name", value=st.session_state.client_name)
    client_address = st.text_area("Client Address", value=st.session_state.client_address, height=100)
    client_email = st.text_input("Client Email", value=st.session_state.client_email)
    
    # Save to session state
    if st.button("Save Client Info"):
        st.session_state.invoice_number = invoice_number
        st.session_state.client_name = client_name
        st.session_state.client_address = client_address
        st.session_state.client_email = client_email
        st.success("Client information saved!")

# Invoice Items Tab
with tabs[2]:
    st.header("Invoice Items")
    
    # Reset items if it's not a list
    if not isinstance(st.session_state.get('items'), list):
        st.session_state['items'] = [
            {"service_item": "AI-001", "description": "AI Workflow Development", "hours": 12, "rate": 150},
            {"service_item": "LLM-001", "description": "LLM Systems Integration", "hours": 8, "rate": 175},
            {"service_item": "CONS-001", "description": "Implementation Consulting", "hours": 8, "rate": 175}
        ]
    
    # Get items from session state
    items = st.session_state['items']
    
    # Display existing items
    for i, item in enumerate(items):
        cols = st.columns([1, 3, 1, 1, 1])
        with cols[0]:
            st.text_input(f"Service Item #{i+1}", value=item.get("service_item", ""), key=f"service_{i}")
        with cols[1]:
            st.text_input(f"Description #{i+1}", value=item["description"], key=f"desc_{i}")
        with cols[2]:
            st.number_input(f"Hours #{i+1}", value=float(item["hours"]), step=0.5, format="%.2f", key=f"hours_{i}")
        with cols[3]:
            st.number_input(f"Rate #{i+1}", value=float(item["rate"]), step=10.0, format="%.2f", key=f"rate_{i}")
        with cols[4]:
            if st.button("Remove", key=f"remove_{i}"):
                items_copy = list(items)  # Create a copy
                items_copy.pop(i)
                st.session_state['items'] = items_copy
                st.rerun()
    
    # Add new item button
    if st.button("Add New Item"):
        items_copy = list(items)  # Create a copy
        items_copy.append({"service_item": "", "description": "", "hours": 1, "rate": 100})
        st.session_state['items'] = items_copy
        st.rerun()
    
    # Save items
    if st.button("Save Items"):
        updated_items = []
        for i in range(len(items)):
            updated_items.append({
                "service_item": st.session_state[f"service_{i}"],
                "description": st.session_state[f"desc_{i}"],
                "hours": float(st.session_state[f"hours_{i}"]),
                "rate": float(st.session_state[f"rate_{i}"]),
            })
        st.session_state['items'] = updated_items
        st.success("Invoice items saved!")

# Notes & Options Tab
with tabs[3]:
    st.header("Notes and Options")
    
    notes = st.text_area("Notes", value=st.session_state.notes, height=100)
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
    if st.button("Save Notes & Options"):
        st.session_state.notes = notes
        st.session_state.tax_rate = tax_rate
        st.session_state.discount = discount
        st.session_state.invoice_date = invoice_date
        st.session_state.due_date = due_date
        st.success("Notes and options saved!")

# Preview Tab
with tabs[4]:
    st.header("Invoice Preview & Download")
    
    if st.button("Generate Invoice"):
        try:
            # Update items with the latest values
            updated_items = []
            items = st.session_state['items']
            for i in range(len(items)):
                updated_items.append({
                    "service_item": st.session_state[f"service_{i}"],
                    "description": st.session_state[f"desc_{i}"],
                    "hours": float(st.session_state[f"hours_{i}"]),
                    "rate": float(st.session_state[f"rate_{i}"]),
                })
            
            generator = InvoiceGenerator(
                st.session_state.company_name,
                st.session_state.company_address,
                company_logo
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
                due_date=st.session_state.due_date
            )
            
            # Create download link
            download_link = create_download_link(pdf_bytes, filename=f"Invoice_{st.session_state.invoice_number}.pdf")
            st.markdown(download_link, unsafe_allow_html=True)
            
            # Display PDF preview using Streamlit's native PDF display
            st.subheader("PDF Preview")
            st.write("If the preview doesn't appear below, use the download link above to view the invoice.")
            
            # Save PDF to a temporary file for display
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_file_path = tmp_file.name
            
            # Display the PDF using Streamlit's PDF display capability
            with open(tmp_file_path, "rb") as f:
                pdf_data = f.read()
                st.download_button(
                    label="View PDF",
                    data=pdf_data,
                    file_name=f"Invoice_{st.session_state.invoice_number}.pdf",
                    mime="application/pdf"
                )
                
            # Also try to display inline if possible
            try:
                st.write("PDF Preview:")
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.write(f"Could not display preview: {e}")
                
            # Clean up the temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            
        except Exception as e:
            st.error(f"Error generating invoice: {str(e)}") 
