# Simple Banking File Transfer API

> **Simplified Banking File Transfer System**  
> Eliminates manual file transfers between banking systems with intelligent, contract-driven API processing

## 🎯 **Overview**

This API replaces traditional file-based data transfers between banking systems with automated, secure, and auditable API operations. Instead of manual file copying, teams use predefined contracts to automatically discover, process, and transfer files between systems.

### **Key Benefits**
- ⚡ **Speed**: 3+ hours → 2 seconds (99.9% faster) 
(Assuming two teams have to coordinate and share files)
- 🔒 **Security**: Automatic data masking and validation
- 📋 **Compliance**: Complete audit trails and processing logs
- 🎯 **Accuracy**: Eliminates manual errors and validation issues
- 💰 **Cost**: reduction in infrastructure costs

---

## 🏗️ **Architecture**

```
System A (Source) → API Processing → System B (Target)
     ↓                    ↓              ↓
  Raw input files    Business logic   Processed files
  Date-based naming   Security rules   Audit trails
```

### **Components**
- **System A**: Source banking system (simulated as `./system_a/`)
- **System B**: Target banking system (simulated as `./system_b/`)
- **API Processing**: Flask application with business rules
- **Contracts**: Predefined file patterns and processing rules

---

## 🚀 **Quick Start**

### **1. Installation**
```bash
# Clone and setup
git clone <repository>
cd simplified-banking-api

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### **2. Create Demo Files**
```bash
curl -X POST http://localhost:5000/api/v1/demo/setup
```

### **3. Test File Processing**
```bash
# Process debit card transactions
curl -X POST http://localhost:5000/api/v1/upload/debitcardtxn

# Download processed data
curl http://localhost:5000/api/v1/download/debitcardtxn

# Download raw file
curl http://localhost:5000/api/v1/download/debitcardtxn/raw/file
```

---

## 📋 **API Contracts**

The system uses predefined contracts that define how files are discovered, processed, and stored.

### **Available Endpoints**
| Endpoint | File Pattern | Description | Format |
|----------|--------------|-------------|---------|
| `debitcardtxn` | `debitcard_input_{date}.csv` | Debit card transaction processing | CSV |
| `ebbsreport` | `ebbs_report_{date}.txt` | EBBS system report processing | TXT |
| `csvtest` | `csv_input_{date}.csv` | Generic CSV processing | CSV |
| `txttest` | `text_input_{date}.txt` | Text file processing to JSON | TXT |
| `pdftest` | `test_document_{date}.pdf` | PDF text extraction | PDF |
| `exceltest` | `excel_input_{date}.xlsx` | Excel to CSV conversion | Excel |

### **Date Pattern**
All files follow the pattern: `filename_DDMMYY.ext`  
Example: `debitcard_input_080725.csv` for July 8, 2025

---

## 🛠️ **API Reference**

### **Core Operations**

#### **Health & System Status**
```bash
GET /health                    # System health check
GET /api/v1/system/status     # File system status
GET /api/v1/contracts         # View all contracts
```

#### **File Processing**
```bash
POST /api/v1/upload/{endpoint}    # Process file from System A → System B
```

**Example:**
```bash
POST /api/v1/upload/debitcardtxn
```

**Response:**
```json
{
  "status": "success",
  "endpoint": "debitcardtxn",
  "source_file": "debitcard_input_080725.csv",
  "target_file": "debitcard_processed_080725.csv",
  "records_processed": 3,
  "file_size_kb": 1.2,
  "sample_data": [
    {
      "card_number": "1234****3456",
      "amount": 150.50,
      "merchant": "Amazon",
      "processed_at": "2025-07-08T10:30:00"
    }
  ]
}
```

#### **File Downloads**

##### **Processed Files (System B - post-processing)**
```bash
GET /api/v1/download/{endpoint}       # JSON API response
GET /api/v1/download/{endpoint}/file  # Direct file download
```

##### **Raw Files (System A)**
```bash
GET /api/v1/download/{endpoint}/raw/file  # Direct raw file download
```

### **Demo & Testing**
```bash
POST /api/v1/demo/setup          # Create sample files
GET /api/v1/system/status        # Check file availability
```

---

## 🔄 **Processing Rules**

### **CSV Processing** (debitcardtxn, csvtest)
- **Card Masking**: `1234567890123456` → `1234****3456`
- **Amount Validation**: Remove invalid amounts
- **Timestamp Addition**: Add processing timestamp
- **Metadata**: Add source file and processing date

### **TXT Processing** (ebbsreport, txttest)
- **JSON Conversion**: Convert text to structured JSON
- **Line Analysis**: Parse individual lines
- **Summary Statistics**: Word count, line count, character count

### **PDF Processing** (pdftest) (Half working - WIP, text extraction from PDF is fine)
- **Text Extraction**: Extract all text from PDF
- **Page Analysis**: Count pages and content
- **Summary Creation**: Generate content statistics

### **Excel Processing** (exceltest)
- **Multi-sheet Support**: Process all sheets
- **CSV Conversion**: Convert to unified CSV format
- **Sheet Identification**: Add source sheet column

---

## 📊 **Demo Workflow**

### **Complete Banking Scenario**

#### **1. Setup Demo Environment**
```bash
POST /api/v1/demo/setup
```

#### **2. Check System Status**
```bash
GET /api/v1/system/status
```

#### **3. Download Raw Data (Before Processing)**
```bash
GET /api/v1/download/debitcardtxn/raw/file
```
*Downloads: Full card numbers, no processing timestamp*

#### **4. Process Data (System A → System B)**
```bash
POST /api/v1/upload/debitcardtxn
```
*Result: Processes raw data and stores in System B*

#### **5. Download Processed Data (After Processing)**
```bash
GET /api/v1/download/debitcardtxn/file
```
*Downloads: Masked card numbers, processing timestamp*

#### **6. Compare Results**
View the transformation:
- **Raw**: `1234567890123456,150.50,Amazon`
- **Processed**: `1234****3456,150.50,Amazon,2025-07-08T10:30:00`

---

## 🔧 **Configuration**

### **File Paths**
```python
BASE_CONFIG = {
    "system_a_path": "./system_a",  # Source system
    "system_b_path": "./system_b",  # Target system
    "date_format": "%d%m%y"         # DDMMYY format
}
```

### **Adding New Endpoints**
Add to `API_CONTRACTS` in `app.py`:
```python
"new_endpoint": {
    "file_pattern": "new_file_{date}.csv",
    "target_pattern": "new_processed_{date}.csv",
    "format": "csv",
    "description": "New file processing",
    "processing_rules": {
        "validate_data": True,
        "add_timestamp": True
    }
}
```

---

## 🏦 **Business Impact**

### **Before vs After**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Transfer Time | 3+ hours | 2 seconds | 99.9% faster |
| Manual Errors | common | negligent |Almost nil errors |
| Security Issues | Common | Eliminated | Easily configurable with latest regulations |
| Infrastructure Cost | time+infraCosts+manual efforts | one-time central setup | Standardisation all over teams and bank in the long run |

### **Use Cases**
- **Risk Management**: Real-time transaction processing
- **Compliance**: Automated regulatory reporting
- **Analytics**: Instant data access for insights
- **Operations**: Streamlined daily processes

---

## 🔒 **Security Features**

- **Data Masking**: Automatic PII (Personal Identitfiable Info) protection
- **Validation**: Business rule enforcement
- **Audit Trails**: Complete operation logging
- **Access Control**: Team-based permissions
- **Input Sanitization**: Comprehensive data validation

---

## 🚀 **Future Enhancements**

### **Phase 2: Enterprise Features**
- OAuth 2.0 authentication
- Advanced monitoring and alerting
- Performance optimization
- Multi-region deployment

### **Phase 3: Advanced Capabilities**
- Real-time streaming
- AI/ML data processing
- External partner integration
- Advanced analytics

---

## 📁 **Project Structure**

```
simplified-banking-api/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── system_a/             # Source files (System A)
│   ├── debitcard_input_*.csv
│   ├── ebbs_report_*.txt
│   └── ...
├── system_b/             # Processed files (System B)
│   ├── debitcard_processed_*.csv
│   ├── ebbs_processed_*.txt
│   └── ...
└── logs/                 # Application logs
```

---

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 💬 **Support**

For support, Reach out to **Jiju, Harikrishna** or **Rajagopalan, Srini** or create an issue in the repository.

---

## **Acknowledgments**

- Built for banking hackathon demonstration
- Inspired by modern API-first banking architecture
- Designed for enterprise-scale deployment

---

**Transform your banking file transfers today! by adopting Switching&Cards Teams Solution** PII
