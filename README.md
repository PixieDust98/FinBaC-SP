# FinBaC-SP Financial Model & Interactive Web App

## Overview

This project provides a **flexible financial modeling toolkit** for evaluating bacterial cellulose (BC) production from potato starch waste. It includes:

- **Modular Python code** for detailed CAPEX/OPEX analysis, product pricing, ROI, IRR, NPV, and payback period calculations.
- **Parameter-driven design:** All key parameters, prices, CAPEX, and OPEX can be set in a central config file.
- **Interactive Streamlit web application** for live scenario analysis, allowing users to adjust all model inputs and visualize results instantly.

---

## Features

- **Parameter Management:** All model inputs (ratios, CAPEX, OPEX, prices, process values) are read from `config/parameters.txt`. Easily customize for your use case.
- **Comprehensive Financial Analysis:** Output includes detailed tables, summary CSVs, and plots (ROI over time, FCF, CAPEX/OPEX breakdown).
- **User Interface:** The web app lets users interactively adjust all inputs, edit tables, and view results with real-time charts.
- **Extensible:** Modular code structure in `utils.py` can be adapted to other bioprocess or manufacturing scenarios.

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/PixieDust98/FinBaC-SP.git
cd FinBaC-SP
```

### 2. Setup Environment

Create and activate the project environment:

```bash
conda env create -f environment.yml
conda activate finbac-sp-env
```

### 3. Edit Parameters

All model parameters are defined in:
```
config/parameters.txt
```
Edit this file to set default values for your scenario.

### 4. Run the Main Analysis Script

```bash
python main.py
```
This will run the financial analysis using parameters from `parameters.txt` and output tables and plots.

### 5. Launch the Interactive Web Application

```bash
streamlit run app.py
```
- The web app will open in your browser.
- Adjust any inputs, CAPEX/OPEX, prices, or ratios in the sidebar and see results update live.

---

## File Structure

```
config/parameters.txt      # All input parameters (editable)
environment.yml            # Required packages for Conda environment
main.py                    # Main financial analysis script (reads all config)
utils.py                   # Core calculation functions (imported by main/app)
app.py                     # Streamlit interactive web app
README.md                  # This file
```

---

## Requirements

- Python >= 3.8
- All dependencies are listed in `environment.yml` (including Streamlit, numpy, pandas, matplotlib, numpy-financial, icecream, pillow, etc.)

---

## Usage Notes

- **All model inputs** (including CAPEX, OPEX, prices, ratios) are read from `config/parameters.txt` and can be edited directly.
- The web application allows further interactive editing and scenario testing.
- Outputs include:
  - Detailed CSV tables (`financial_summary_table.csv`, `comprehensive_output.csv`)
  - Financial summaries (`financial_summary.json`)
  - Plots (`financial_performance.svg`, pie charts)
- You can extend `utils.py` to add more calculation methods or outputs as needed.

---

## How to Cite

If you use this toolkit in a publication or report, please cite the repository URL and authors.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Contact

For questions or suggestions, contact [PixieDust98](https://github.com/PixieDust98) via GitHub.
