#!/usr/bin/env python3
"""
Simplified Banking File Transfer API
No Kafka, No Redis, No Complex Dependencies
Direct file operations with predefined paths and contracts

Architecture:
- System A (Source): Input files with date patterns
- System B (Target): Processed/downloaded files
- API Contracts: Predefined file formats and paths
- Multi-format support: CSV, TXT, PDF, Excel
"""

from flask import Flask, jsonify, send_file, Response
from flask_cors import CORS
import os
import shutil
import pandas as pd
from datetime import datetime
import json
import io
import PyPDF2
import openpyxl
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration - File Paths and Contracts
BASE_CONFIG = {
    "system_a_path": "./system_a",  # Source system
    "system_b_path": "./system_b",  # Target system
    "supported_formats": ["csv", "txt", "pdf", "excel"],
    "date_format": "%d%m%y",  # DDMMYY format
}

# API Contracts - Define file patterns and processing rules
API_CONTRACTS = {
    "debitcardtxn": {
        "file_pattern": "debitcard_input_{date}.csv",
        "target_pattern": "debitcard_processed_{date}.csv",
        "format": "csv",
        "description": "Debit card transaction processing",
        "columns_expected": ["card_number", "amount", "merchant", "timestamp"],
        "processing_rules": {
            "validate_amount": True,
            "mask_card_number": True,
            "add_processing_timestamp": True
        }
    },
    "ebbsreport": {
        "file_pattern": "ebbs_report_{date}.txt",
        "target_pattern": "ebbs_processed_{date}.txt",
        "format": "txt",
        "description": "EBBS system report processing",
        "processing_rules": {
            "convert_to_json": True,
            "add_summary": True
        }
    },
    "pdftest": {
        "file_pattern": "test_document_{date}.pdf",
        "target_pattern": "pdf_extracted_{date}.txt",
        "format": "pdf",
        "description": "PDF text extraction and processing",
        "processing_rules": {
            "extract_text": True,
            "create_summary": True
        }
    },
    "csvtest": {
        "file_pattern": "csv_input_{date}.csv",
        "target_pattern": "csv_output_{date}.csv",
        "format": "csv",
        "description": "Generic CSV processing",
        "processing_rules": {
            "validate_headers": True,
            "add_metadata": True
        }
    },
    "exceltest": {
        "file_pattern": "excel_input_{date}.xlsx",
        "target_pattern": "excel_output_{date}.csv",
        "format": "excel",
        "description": "Excel to CSV conversion",
        "processing_rules": {
            "convert_to_csv": True,
            "preserve_formulas": False
        }
    },
    "txttest": {
        "file_pattern": "text_input_{date}.txt",
        "target_pattern": "text_processed_{date}.json",
        "format": "txt",
        "description": "Text file processing to JSON",
        "processing_rules": {
            "parse_lines": True,
            "create_structure": True
        }
    }
}

def ensure_directories():
    """Create system directories if they don't exist"""
    Path(BASE_CONFIG["system_a_path"]).mkdir(exist_ok=True)
    Path(BASE_CONFIG["system_b_path"]).mkdir(exist_ok=True)
    print(f"✅ Directories ensured: {BASE_CONFIG['system_a_path']}, {BASE_CONFIG['system_b_path']}")

def get_today_date():
    """Get today's date in DDMMYY format"""
    return datetime.now().strftime(BASE_CONFIG["date_format"])

def find_input_file(endpoint):
    """Find input file for given endpoint based on today's date"""
    if endpoint not in API_CONTRACTS:
        return None, f"Unknown endpoint: {endpoint}"
    
    contract = API_CONTRACTS[endpoint]
    today_date = get_today_date()
    file_pattern = contract["file_pattern"].format(date=today_date)
    file_path = os.path.join(BASE_CONFIG["system_a_path"], file_pattern)
    
    if os.path.exists(file_path):
        return file_path, None
    else:
        return None, f"File not found: {file_pattern} for date {today_date}"

def process_csv_file(file_path, contract):
    """Process CSV file according to contract rules"""
    try:
        df = pd.read_csv(file_path)
        
        # Apply processing rules
        rules = contract.get("processing_rules", {})
        
        if rules.get("mask_card_number") and "card_number" in df.columns:
            df["card_number"] = df["card_number"].astype(str).str.replace(r'(\d{4})\d{8}(\d{4})', r'\1****\2', regex=True)
        
        if rules.get("add_processing_timestamp"):
            df["processed_at"] = datetime.now().isoformat()
        
        if rules.get("validate_amount") and "amount" in df.columns:
            df = df[pd.to_numeric(df["amount"], errors='coerce').notna()]
        
        if rules.get("add_metadata"):
            df["file_source"] = os.path.basename(file_path)
            df["processing_date"] = get_today_date()
        
        return df, None
    except Exception as e:
        return None, f"CSV processing error: {str(e)}"

def process_txt_file(file_path, contract):
    """Process TXT file according to contract rules"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = contract.get("processing_rules", {})
        
        if rules.get("convert_to_json"):
            lines = content.strip().split('\n')
            data = {
                "total_lines": len(lines),
                "content": lines,
                "processed_at": datetime.now().isoformat(),
                "source_file": os.path.basename(file_path)
            }
            
            if rules.get("add_summary"):
                data["summary"] = {
                    "line_count": len(lines),
                    "word_count": len(content.split()),
                    "char_count": len(content)
                }
            
            return data, None
        
        elif rules.get("parse_lines"):
            lines = content.strip().split('\n')
            structured_data = []
            
            for i, line in enumerate(lines):
                structured_data.append({
                    "line_number": i + 1,
                    "content": line.strip(),
                    "length": len(line.strip())
                })
            
            return {
                "parsed_lines": structured_data,
                "metadata": {
                    "total_lines": len(lines),
                    "processed_at": datetime.now().isoformat()
                }
            }, None
        
        return {"raw_content": content, "processed_at": datetime.now().isoformat()}, None
        
    except Exception as e:
        return None, f"TXT processing error: {str(e)}"

def process_pdf_file(file_path, contract):
    """Process PDF file according to contract rules"""
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
        
        rules = contract.get("processing_rules", {})
        
        data = {
            "extracted_text": text_content,
            "page_count": len(pdf_reader.pages),
            "processed_at": datetime.now().isoformat(),
            "source_file": os.path.basename(file_path)
        }
        
        if rules.get("create_summary"):
            data["summary"] = {
                "word_count": len(text_content.split()),
                "char_count": len(text_content),
                "line_count": len(text_content.split('\n'))
            }
        
        return data, None
        
    except Exception as e:
        return None, f"PDF processing error: {str(e)}"

def process_excel_file(file_path, contract):
    """Process Excel file according to contract rules"""
    try:
        # Read all sheets
        excel_data = pd.read_excel(file_path, sheet_name=None)
        
        rules = contract.get("processing_rules", {})
        
        if rules.get("convert_to_csv"):
            # Combine all sheets into one DataFrame
            combined_df = pd.DataFrame()
            
            for sheet_name, df in excel_data.items():
                df["source_sheet"] = sheet_name
                combined_df = pd.concat([combined_df, df], ignore_index=True)
            
            combined_df["processed_at"] = datetime.now().isoformat()
            return combined_df, None
        
        # Return structured data
        processed_data = {}
        for sheet_name, df in excel_data.items():
            processed_data[sheet_name] = {
                "data": df.to_dict('records'),
                "shape": df.shape,
                "columns": list(df.columns)
            }
        
        processed_data["metadata"] = {
            "sheet_count": len(excel_data),
            "processed_at": datetime.now().isoformat(),
            "source_file": os.path.basename(file_path)
        }
        
        return processed_data, None
        
    except Exception as e:
        return None, f"Excel processing error: {str(e)}"

@app.route('/')
def index():
    """API Overview"""
    ensure_directories()
    
    return {
        "service": "Simplified Banking File Transfer API",
        "version": "2.0.0",
        "architecture": "Direct file operations (No Kafka/Redis)",
        "description": "File transfer between System A and System B with predefined contracts",
        "configuration": BASE_CONFIG,
        "available_endpoints": {
            "upload": [f"/api/v1/upload/{endpoint}" for endpoint in API_CONTRACTS.keys()],
            "download": [f"/api/v1/download/{endpoint}" for endpoint in API_CONTRACTS.keys()],
            "contracts": "/api/v1/contracts",
            "health": "/health",
            "demo": "/api/v1/demo/setup"
        },
        "supported_formats": BASE_CONFIG["supported_formats"],
        "date_pattern": "Files should follow pattern with today's date (DDMMYY)",
        "example_today": get_today_date()
    }

@app.route('/health')
def health():
    """System health check"""
    ensure_directories()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_a_accessible": os.path.exists(BASE_CONFIG["system_a_path"]),
        "system_b_accessible": os.path.exists(BASE_CONFIG["system_b_path"]),
        "today_date": get_today_date(),
        "contracts_loaded": len(API_CONTRACTS)
    }

@app.route('/api/v1/contracts')
def get_contracts():
    """Get all API contracts"""
    return {
        "contracts": API_CONTRACTS,
        "base_config": BASE_CONFIG,
        "today_date": get_today_date(),
        "usage": {
            "upload": "POST /api/v1/upload/{endpoint} - Process file from System A",
            "download": "GET /api/v1/download/{endpoint} - Download processed file to System B"
        }
    }

@app.route('/api/v1/upload/<endpoint>', methods=['POST'])
def upload_and_process(endpoint):
    """
    Upload/Process file from System A
    Finds file based on today's date and contract pattern
    """
    ensure_directories()
    
    if endpoint not in API_CONTRACTS:
        return {"error": f"Unknown endpoint: {endpoint}", "available": list(API_CONTRACTS.keys())}, 400
    
    contract = API_CONTRACTS[endpoint]
    
    # Find input file
    file_path, error = find_input_file(endpoint)
    if error:
        return {"error": error, "expected_pattern": contract["file_pattern"].format(date=get_today_date())}, 404
    
    # Process file based on format
    file_format = contract["format"]
    processed_data = None
    processing_error = None
    
    if file_format == "csv":
        processed_data, processing_error = process_csv_file(file_path, contract)
    elif file_format == "txt":
        processed_data, processing_error = process_txt_file(file_path, contract)
    elif file_format == "pdf":
        processed_data, processing_error = process_pdf_file(file_path, contract)
    elif file_format == "excel":
        processed_data, processing_error = process_excel_file(file_path, contract)
    else:
        processing_error = f"Unsupported format: {file_format}"
    
    if processing_error:
        return {"error": processing_error}, 500
    
    # Save processed file to System B
    today_date = get_today_date()
    target_filename = contract["target_pattern"].format(date=today_date)
    target_path = os.path.join(BASE_CONFIG["system_b_path"], target_filename)
    
    try:
        if isinstance(processed_data, pd.DataFrame):
            processed_data.to_csv(target_path, index=False)
            records_count = len(processed_data)
        else:
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2)
            records_count = len(processed_data) if isinstance(processed_data, (list, dict)) else 1
        
        return {
            "status": "success",
            "endpoint": endpoint,
            "description": contract["description"],
            "source_file": os.path.basename(file_path),
            "target_file": target_filename,
            "target_path": target_path,
            "records_processed": records_count,
            "format": file_format,
            "processed_at": datetime.now().isoformat(),
            "file_size_kb": round(os.path.getsize(target_path) / 1024, 2),
            "sample_data": processed_data.head(3).to_dict('records') if isinstance(processed_data, pd.DataFrame) 
                          else str(processed_data)[:200] + "..." if len(str(processed_data)) > 200 
                          else processed_data
        }
        
    except Exception as e:
        return {"error": f"Failed to save processed file: {str(e)}"}, 500

@app.route('/api/v1/download/<endpoint>')
def download_processed_file(endpoint):
    """
    Download processed file from System B
    Returns file content and also saves to System B if not exists
    """
    ensure_directories()
    
    if endpoint not in API_CONTRACTS:
        return {"error": f"Unknown endpoint: {endpoint}", "available": list(API_CONTRACTS.keys())}, 400
    
    contract = API_CONTRACTS[endpoint]
    today_date = get_today_date()
    target_filename = contract["target_pattern"].format(date=today_date)
    target_path = os.path.join(BASE_CONFIG["system_b_path"], target_filename)
    
    # Check if processed file exists, if not, process it first
    if not os.path.exists(target_path):
        # Try to process the file first
        upload_result = upload_and_process(endpoint)
        if isinstance(upload_result, tuple) and upload_result[1] != 200:  # Error occurred
            return upload_result
    
    if not os.path.exists(target_path):
        return {
            "error": f"Processed file not found: {target_filename}",
            "suggestion": f"Run POST /api/v1/upload/{endpoint} first"
        }, 404
    
    try:
        # Read and return file content
        file_size = os.path.getsize(target_path)
        
        # Determine how to read the file
        if target_filename.endswith('.csv'):
            df = pd.read_csv(target_path)
            file_content = {
                "format": "csv",
                "records": df.to_dict('records'),
                "shape": df.shape,
                "columns": list(df.columns)
            }
        elif target_filename.endswith('.json') or target_filename.endswith('.txt'):
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                file_content = {"format": "json", "data": json.loads(content)}
            except:
                file_content = {"format": "text", "content": content}
        else:
            with open(target_path, 'r', encoding='utf-8') as f:
                file_content = {"format": "text", "content": f.read()}
        
        return {
            "status": "success",
            "endpoint": endpoint,
            "description": contract["description"],
            "file_name": target_filename,
            "file_path": target_path,
            "file_size_kb": round(file_size / 1024, 2),
            "downloaded_at": datetime.now().isoformat(),
            "content": file_content,
            "download_url": f"/api/v1/download/{endpoint}/file"
        }
        
    except Exception as e:
        return {"error": f"Failed to read processed file: {str(e)}"}, 500

@app.route('/api/v1/download/<endpoint>/file')
def download_file_direct(endpoint):
    """Direct file download"""
    if endpoint not in API_CONTRACTS:
        return {"error": f"Unknown endpoint: {endpoint}"}, 400
    
    contract = API_CONTRACTS[endpoint]
    today_date = get_today_date()
    target_filename = contract["target_pattern"].format(date=today_date)
    target_path = os.path.join(BASE_CONFIG["system_b_path"], target_filename)
    
    if not os.path.exists(target_path):
        return {"error": f"File not found: {target_filename}"}, 404
    
    return send_file(target_path, as_attachment=True, download_name=target_filename)

@app.route('/api/v1/demo/setup', methods=['POST'])
def setup_demo_files():
    """Create demo files for testing"""
    ensure_directories()
    today_date = get_today_date()
    created_files = []
    
    # Create sample CSV file
    csv_data = {
        "card_number": ["1234567890123456", "2345678901234567", "3456789012345678"],
        "amount": [150.50, 250.75, 89.99],
        "merchant": ["Amazon", "Walmart", "Starbucks"],
        "timestamp": ["2025-07-08T10:30:00", "2025-07-08T11:45:00", "2025-07-08T12:15:00"]
    }
    df = pd.DataFrame(csv_data)
    csv_file = os.path.join(BASE_CONFIG["system_a_path"], f"debitcard_input_{today_date}.csv")
    df.to_csv(csv_file, index=False)
    created_files.append(f"debitcard_input_{today_date}.csv")
    
    # Create sample TXT file
    txt_content = """EBBS Report Summary
Transaction Count: 1,250
Total Amount: $125,750.50
Failed Transactions: 5
Success Rate: 99.6%
Report Generated: 2025-07-08T10:00:00"""
    
    txt_file = os.path.join(BASE_CONFIG["system_a_path"], f"ebbs_report_{today_date}.txt")
    with open(txt_file, 'w') as f:
        f.write(txt_content)
    created_files.append(f"ebbs_report_{today_date}.txt")
    
    # Create sample CSV test file
    csv_test_data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "value": [100, 200, 150, 300, 175],
        "category": ["A", "B", "A", "C", "B"]
    }
    df_test = pd.DataFrame(csv_test_data)
    csv_test_file = os.path.join(BASE_CONFIG["system_a_path"], f"csv_input_{today_date}.csv")
    df_test.to_csv(csv_test_file, index=False)
    created_files.append(f"csv_input_{today_date}.csv")
    
    # Create sample TXT test file
    txt_test_content = """Line 1: Important banking data
Line 2: Customer ID 12345
Line 3: Balance: $50,000
Line 4: Account Type: Premium
Line 5: Last Activity: 2025-07-08"""
    
    txt_test_file = os.path.join(BASE_CONFIG["system_a_path"], f"text_input_{today_date}.txt")
    with open(txt_test_file, 'w') as f:
        f.write(txt_test_content)
    created_files.append(f"text_input_{today_date}.txt")
    
    return {
        "status": "demo_files_created",
        "today_date": today_date,
        "created_files": created_files,
        "system_a_path": BASE_CONFIG["system_a_path"],
        "next_steps": [
            f"POST /api/v1/upload/debitcardtxn",
            f"POST /api/v1/upload/ebbsreport", 
            f"POST /api/v1/upload/csvtest",
            f"POST /api/v1/upload/txttest"
        ],
        "test_download": [
            f"GET /api/v1/download/debitcardtxn",
            f"GET /api/v1/download/ebbsreport"
        ]
    }

@app.route('/api/v1/system/status')
def system_status():
    """Show system file status"""
    ensure_directories()
    today_date = get_today_date()
    
    system_a_files = []
    system_b_files = []
    
    # Check System A files
    if os.path.exists(BASE_CONFIG["system_a_path"]):
        for file in os.listdir(BASE_CONFIG["system_a_path"]):
            file_path = os.path.join(BASE_CONFIG["system_a_path"], file)
            system_a_files.append({
                "filename": file,
                "size_kb": round(os.path.getsize(file_path) / 1024, 2),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    # Check System B files
    if os.path.exists(BASE_CONFIG["system_b_path"]):
        for file in os.listdir(BASE_CONFIG["system_b_path"]):
            file_path = os.path.join(BASE_CONFIG["system_b_path"], file)
            system_b_files.append({
                "filename": file,
                "size_kb": round(os.path.getsize(file_path) / 1024, 2),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    return {
        "today_date": today_date,
        "system_a": {
            "path": BASE_CONFIG["system_a_path"],
            "file_count": len(system_a_files),
            "files": system_a_files
        },
        "system_b": {
            "path": BASE_CONFIG["system_b_path"],
            "file_count": len(system_b_files),
            "files": system_b_files
        },
        "contracts_status": {
            endpoint: {
                "input_expected": contract["file_pattern"].format(date=today_date),
                "output_pattern": contract["target_pattern"].format(date=today_date),
                "input_exists": os.path.exists(os.path.join(BASE_CONFIG["system_a_path"], 
                                                           contract["file_pattern"].format(date=today_date))),
                "output_exists": os.path.exists(os.path.join(BASE_CONFIG["system_b_path"], 
                                                            contract["target_pattern"].format(date=today_date)))
            }
            for endpoint, contract in API_CONTRACTS.items()
        }
    }

if __name__ == '__main__':
    print("System A (Source):", BASE_CONFIG["system_a_path"])
    print("System B (Target):", BASE_CONFIG["system_b_path"])
    print("Today's date pattern:", get_today_date())
    print("Available endpoints:", len(API_CONTRACTS))
    
    ensure_directories()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)