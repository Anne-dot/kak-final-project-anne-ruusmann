# Mach3 Tool Management and DXF to G-code System

This repository contains a comprehensive solution for CNC machine tool management and automated DXF to G-code generation using Mach3 CNC software.

## 📋 Project Overview

This project integrates two main components:
1. **Tool Management System** - Manages CNC tool data across Mach3 and external systems
2. **DXF to G-code Generation** - Automatically converts DXF drawings to machine-executable G-code

## 🔗 Documentation

For complete documentation, please visit our [Confluence Wiki](https://ruusmann.atlassian.net/wiki/spaces/MFPD/) (private access).

## 🏗️ Repository Structure

```
Mach3/
├── ToolManagement/            # Core tool management components
│   ├── Backups/               # Tool data backup system
│   ├── Scripts/               # Python processing scripts
│   │   ├── DXF/               # DXF parsing and extraction
│   │   ├── GCode/             # G-code handling
│   │   ├── GCodeGenerator/    # G-code generation
│   │   ├── ProcessingEngine/  # Core processing logic
│   │   ├── Utils/             # Shared utilities
│   │   └── Tests/             # Unit and manual tests
│   └── data/                  # Tool data storage
│
├── macros/                    # Mach3 VBScript macros
│   └── Mach3Development/      # Custom macros and scripts
│       ├── 01_CustomMacros/   # Production-ready macros
│       ├── 02_HelperMacros/   # Support macros and utilities
│       └── 99_MacroFunctionalityTesting/ # Test macros
└── CLAUDE.md                  # Development standards and guidelines
```

## 🚀 Key Features

### Tool Management
- CSV-based tool data storage with backup capabilities
- Automatic synchronization with Mach3 native tool table
- Bi-directional data exchange between Python and VBScript
- Tool parameter validation and error handling

### DXF Processing
- Parsing and extraction of DXF entities
- Workpiece boundary detection
- Drill point extraction and parameter recognition
- Coordinate transformation for machine operations

### G-code Generation
- Drill operation G-code generation
- Horizontal drilling support
- Tool selection and compatibility matching
- Safety checks and validation

## 🧰 Technologies

- **Python 3.13+**: Core processing engine
- **Mach3 VBScript**: Machine interface and control
- **CSV**: Data storage and exchange format

## 📦 Prerequisites

- **Mach3 CNC Software** (Demo version or licensed)
  - Download from [Mach3 official website](https://www.machsupport.com/software/mach3/)
  - Windows operating system required for Mach3
- **Python 3.13+** installed on your system
- Basic understanding of CNC operations and G-code

## 🔧 Installation

> **Note:** This system requires integration with an existing Mach3 installation and cannot be run standalone.

1. **Install Mach3**
   - Download and install Mach3 (demo version works for testing)
   - Default installation path: `C:\Mach3\`

2. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd Mach3
   ```

3. **Copy files to Mach3 directory**
   - Copy the entire `ToolManagement` folder to your Mach3 installation directory
   - Copy contents of `macros` folder to `C:\Mach3\macros\<YourProfile>\`
   - Typical structure after copying:
     ```
     C:\Mach3\
     ├── ToolManagement\
     │   ├── Scripts\
     │   ├── Data\
     │   └── Backups\
     └── macros\
         └── <YourProfile>\
             └── Mach3Development\
     ```

4. **Install Python dependencies**
   ```bash
   pip install -r ToolManagement/Scripts/requirements.txt
   ```

5. **Configure Mach3**
   - Open Mach3 and load your machine profile
   - Ensure macro path points to your profile's macro directory
   - Test by running macro M1000 from MDI (should display system info)

## 💻 Usage

### Running Python Scripts
```bash
# Navigate to Scripts directory
cd C:\Mach3\ToolManagement\Scripts

# Run DXF to G-code generator
python GCodeGenerator/gcode_program_generator.py

# Run tests
python Tests/run_tests.py
```

### Using Mach3 Macros
- **M1000**: Display system information
- **M1001**: Load tool data from CSV
- **M1002**: Backup tool data
- **M1003**: Sync tools to Mach3 native table

## 🔄 Development Workflow

This repository follows the development workflow and coding standards documented in `CLAUDE.md`.

## 👋 About Me & This Project

This is my final project for the Junior Software Developer program at Kuressaare Ametikool (Kuressaare Vocational School).

I'm a curious person who loves to solve problems, automate and optimize boring repetitive tasks. My journey into programming actually began while working as a CNC operator - I wanted to make my own work easier and found that coding was a challenge I genuinely enjoyed.

This project allows me to combine my hands-on CNC experience with my passion for programming. It represents the intersection of my practical knowledge and the skills I've developed through my studies.

I'm also passionate about sustainability - I believe that good design, maintainability, and optimization contribute to reducing waste and resource usage. This project is my small contribution to making industrial processes more efficient, one machine at a time.

If this sparks your interest or you'd like to collaborate, please reach out! I'm always eager to connect with people who share these interests, as I've found that there are few people around me who get as excited about CNC automation and programming as I do.

## ⚠️ Known Limitations

### File Lock Detection
The current file lock detection system (`file_lock_utils.py`) has limitations:
- Cannot reliably detect when files are open in Notepad or other text editors
- Lock detection behavior varies between Windows and Linux platforms
- Currently only manages `.lock` files, not actual file access conflicts

**Note:** Since the browser-based UI is under development, users currently edit files directly in Notepad. This module requires rework for production use.

## 🛠️ Contributing

Please read `CLAUDE.md` for details on our code of conduct and the process for submitting pull requests.