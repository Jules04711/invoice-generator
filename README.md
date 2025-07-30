# Invoice Generator

A Streamlit web application that allows users to easily create professional PDF invoices for clients.

## Demo

https://github.com/user-attachments/assets/f8170bf9-a154-42fc-8aff-c8b44ea1cc11

## Features

- Create customized invoices with your company information
- Add client details and multiple service items
- Customize tax rates and discounts
- Add custom notes to invoices
- Upload your company logo or use the default
- Preview and download generated invoices as PDF

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd invoice-generator
```

2. Create and activate a virtual environment (recommended):
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Make sure you have an `asset` folder with a `logo.png` file for the default logo, or you can upload your own logo when using the app.

## Usage

Run the Streamlit app:

```bash
streamlit run invoice.py
```

The application will open in your default web browser. Follow these steps to create an invoice:

1. **Company Info tab**: Enter your company details and upload a logo if needed
2. **Client Info tab**: Add client information and invoice number
3. **Invoice Items tab**: Add service items with descriptions, hours, and rates
4. **Notes & Options tab**: Customize invoice notes, tax rate, and discount
5. **Preview tab**: Generate the invoice, preview it, and download as PDF

## Requirements

- Python 3.7+
- Streamlit
- FPDF
- Pillow
- Requests

## MIT License

This project is open source and available for personal and commercial use. 
