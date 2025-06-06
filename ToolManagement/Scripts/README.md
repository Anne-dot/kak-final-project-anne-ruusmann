# ToolManagement Scripts - Architecture Overview

This folder contains the complete DXF to G-code generation system with safety enhancement capabilities.

## 🎯 Two Main Entry Points

### 1. **`dxf_to_gcode_main.py`** - Create New G-code from DXF
**Purpose**: Generate brand new G-code from DXF drawings
**Use when**: You have a DXF file and need safe G-code
```
DXF file → Parse → Extract → Transform → Generate → Enhance → Safe G-code (.txt)
```

### 2. **`gcode_safety_enhancer_main.py`** - Enhance Existing G-code
**Purpose**: Add safety features to existing G-code
**Use when**: You have G-code from Vectric or other CAM software
```
Existing G-code → Enhance → Safe G-code (.txt)
```

## 📦 Package Structure

Each package has ONE clear job:

```
Scripts/
├── dxf_to_gcode_main.py          # MAIN: Full DXF to G-code pipeline
├── gcode_safety_enhancer_main.py  # MAIN: Safety enhancement only
│
├── DXF/                          # Job: Parse DXF files and extract drilling info
├── ProcessingEngine/             # Job: Transform coordinates for machine
├── GCodeGenerator/               # Job: Generate G-code from processed data
└── GCodeProcessor/               # Job: Add safety features to any G-code
```

## 🔄 Data Flow

### Full Pipeline (DXF to Safe G-code):
1. **DXF Package** reads drawing → outputs drill points + workpiece
2. **ProcessingEngine** rotates/positions → outputs machine coordinates  
3. **GCodeGenerator** creates G-code → outputs raw G-code
4. **GCodeProcessor** adds safety → outputs safe G-code (.txt)

### Enhancement Only (Existing G-code):
1. **GCodeProcessor** reads G-code → outputs safe G-code (.txt)

## 💡 Why This Design?

### Modularity
- Each package does ONE thing well
- Easy to test individual parts
- Can reuse packages in different workflows

### Flexibility  
- Use full pipeline for new designs
- Use enhancer for existing G-code
- Mix and match as needed

### Clarity
- Two clear entry points
- No confusion about where to start
- Each package has clear boundaries

### Safety First
- All G-code gets safety features
- Whether generated or imported
- Consistent safety across workflows

## 🚀 Quick Start

**To generate G-code from DXF:**
```bash
python3 dxf_to_gcode_main.py input.dxf output.txt
```

**To enhance existing G-code:**
```bash
python3 gcode_safety_enhancer_main.py vectric_code.txt safe_code.txt
```

## 📝 Package Details

See individual package READMEs for detailed information:
- [DXF Package](./DXF/README.md) - DXF parsing and extraction
- [ProcessingEngine Package](./ProcessingEngine/README.md) - Coordinate transformation  
- [GCodeGenerator Package](./GCodeGenerator/README.md) - G-code generation
- [GCodeProcessor Package](./GCodeProcessor/README.md) - Safety enhancement

## 🎨 Design Principles

1. **KISS** - Keep It Simple, Stupid
2. **DRY** - Don't Repeat Yourself (reuse packages)
3. **SRP** - Single Responsibility (one job per package)
4. **ADHD-Friendly** - Clear structure, visual separation