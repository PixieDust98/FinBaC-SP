import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

from utils import (
    load_parameters,
    calculate_flows,
    calculate_financials,
    find_price_boundaries_all_products
)

# --- Load default parameters ---
default_params = load_parameters("config/parameters.txt")

def param_input(key, default, help_text="", dtype=float):
    """Helper for consistent parameter input."""
    if dtype == int:
        return st.number_input(key, value=int(default), help=help_text)
    elif dtype == float:
        return st.number_input(key, value=float(default), format="%.4f", help=help_text)
    elif dtype == list:
        return st.text_input(key, value=str(default), help=help_text)
    else:
        return st.text_input(key, value=str(default), help=help_text)

st.set_page_config(page_title="Financial Model App", layout="wide")
st.title("Financial Model Interactive Application")

st.sidebar.header("Input Parameters")

# --- Main input widgets ---
potato_input_kg = param_input("Daily Potato Input (kg)", default_params["potato_input_kg"], dtype=float)
operating_days = param_input("Operating Days per Year", default_params["operating_days"], dtype=int)
fermentation_time = param_input("Fermentation Time (hours/batch)", default_params["fermentation_time"], dtype=float)
life_span = param_input("Life Span (years)", default_params["life_span"], dtype=int)
starch_yield = param_input("Starch Yield (fraction)", default_params["starch_yield"], dtype=float)
freeze_dry_weight_loss = param_input("Freeze Dry Weight Loss (fraction)", default_params["freeze_dry_weight_loss"], dtype=float)
oven_dry_weight_loss = param_input("Oven Dry Weight Loss (fraction)", default_params["oven_dry_weight_loss"], dtype=float)
freeze_drying_energy = param_input("Freeze Drying Energy (kWh/kg)", default_params["freeze_drying_energy"], dtype=float)
oven_drying_energy = param_input("Oven Drying Energy (kWh/kg)", default_params["oven_drying_energy"], dtype=float)
energy_cost_per_kwh = param_input("Energy Cost per kWh (USD)", default_params["energy_cost_per_kwh"], dtype=float)
NaOH_for_purification = param_input("NaOH for Purification (USD/kg)", default_params["NaOH_for_purification"], dtype=float)
Water_for_washing = param_input("Water for Washing (USD/kg)", default_params["Water_for_washing"], dtype=float)
Water_treatment = param_input("Water Treatment (USD/kg)", default_params["Water_treatment"], dtype=float)
bc_productivity = param_input("BC Productivity (g/L/h)", default_params["bc_productivity"], dtype=float)
sugar_concentration = param_input("Sugar Concentration (g/L)", default_params["sugar_concentration"], dtype=float)
max_bioreactor_volume = param_input("Max Bioreactor Volume (L)", default_params["max_bioreactor_volume"], dtype=float)
waste_starch_content = param_input("Waste Starch Content (fraction)", default_params["waste_starch_content"], dtype=float)
waste_sugar_content = param_input("Waste Sugar Content (fraction)", default_params["waste_sugar_content"], dtype=float)
hydrolysis_efficiency = param_input("Hydrolysis Efficiency (fraction)", default_params["hydrolysis_efficiency"], dtype=float)

ratios_str = st.sidebar.text_input("Ratios [wet, freeze, oven]", str(default_params["ratios"]),
                                   help="Should be Python list, e.g. [0.2, 0.6, 0.2]")
try:
    ratios = eval(ratios_str)
    if not (isinstance(ratios, list) and len(ratios) == 3):
        st.warning("Ratios must be a list of three numbers.")
        ratios = default_params["ratios"]
except Exception:
    st.warning("Ratios input error: Using defaults.")
    ratios = default_params["ratios"]

st.sidebar.subheader("CAPEX Breakdown")
capex_breakdown = default_params["capex_breakdown"]

capex_df = pd.DataFrame(list(capex_breakdown.items()), columns=["Item", "Value"])
edited_capex = st.sidebar.experimental_data_editor(capex_df, num_rows="dynamic", use_container_width=True)
capex_breakdown = dict(zip(edited_capex["Item"], edited_capex["Value"]))
total_capex = sum(capex_breakdown.values())

st.sidebar.subheader("OPEX Breakdown")
opex_breakdown = default_params["opex_breakdown"]
opex_df = pd.DataFrame(list(opex_breakdown.items()), columns=["Item", "Value"])
edited_opex = st.sidebar.experimental_data_editor(opex_df, num_rows="dynamic", use_container_width=True)
opex_breakdown = dict(zip(edited_opex["Item"], edited_opex["Value"]))

st.sidebar.subheader("Product Prices")
prices = default_params["prices"]
prices_df = pd.DataFrame(list(prices.items()), columns=["Product", "Price"])
edited_prices = st.sidebar.experimental_data_editor(prices_df, num_rows="dynamic", use_container_width=True)
prices = dict(zip(edited_prices["Product"], edited_prices["Price"]))

# --- Calculations ---
flows = calculate_flows(
    potato_input_kg,
    starch_yield,
    waste_starch_content,
    waste_sugar_content,
    hydrolysis_efficiency,
    sugar_concentration,
    fermentation_time,
    max_bioreactor_volume,
    bc_productivity
)

price_boundaries_dict = find_price_boundaries_all_products(
    product_prices=prices.copy(),
    step=0.001,
    discount_rate=0.00001,
    potato_input_kg=potato_input_kg,
    starch_yield=starch_yield,
    waste_starch_content=waste_starch_content,
    waste_sugar_content=waste_sugar_content,
    hydrolysis_efficiency=hydrolysis_efficiency,
    sugar_concentration=sugar_concentration,
    fermentation_time=fermentation_time,
    max_bioreactor_volume=max_bioreactor_volume,
    bc_productivity=bc_productivity,
    ratios=ratios,
    freeze_dry_weight_loss=freeze_dry_weight_loss,
    oven_dry_weight_loss=oven_dry_weight_loss,
    freeze_drying_energy=freeze_drying_energy,
    oven_drying_energy=oven_drying_energy,
    energy_cost_per_kwh=energy_cost_per_kwh,
    NaOH_for_purification=NaOH_for_purification,
    Water_for_washing=Water_for_washing,
    Water_treatment=Water_treatment,
    opex_breakdown=opex_breakdown,
    operating_days=operating_days,
    total_capex=total_capex,
    life_span=life_span
)
updated_prices = prices.copy()
updated_prices.update({
    product: price_boundaries_dict[product]['msp'] * 1.2
    for product in ['wet_BC', 'freeze_BC', 'oven_BC']
})

financial_summary = {}
for year in range(1, int(life_span) + 1):
    financial_summary[year] = calculate_financials(
        flows, ratios, year, updated_prices,
        freeze_dry_weight_loss, oven_dry_weight_loss,
        freeze_drying_energy, oven_drying_energy,
        energy_cost_per_kwh, NaOH_for_purification,
        Water_for_washing, Water_treatment,
        opex_breakdown, operating_days, total_capex, life_span
    )

total_profit_before_tax = sum(financial_summary[year]['profit']['annual_gross (USD)'] for year in financial_summary)
total_profit_after_tax = sum(financial_summary[year]['profit']['net_profit (USD)'] for year in financial_summary)
total_costs = sum(financial_summary[year]['annual_costs']['CAPEX+OPEX'] for year in financial_summary)
lifespan_roi_before_tax = total_profit_before_tax / total_costs
lifespan_roi_after_tax = total_profit_after_tax / total_costs

cash_flows = [financial_summary[year]['cash_flow']['free_cash_flow (USD)'] for year in financial_summary]
irr = npf.irr(cash_flows)
npv = npf.npv(0.12, cash_flows)
cumulative_cash_flow = 0
payback_period = 0
for year in financial_summary:
    cumulative_cash_flow += financial_summary[year]['cash_flow']['free_cash_flow (USD)']
    if cumulative_cash_flow >= 0:
        payback_period = year
        break

# --- Display Results ---
st.header("Result Summary")
st.markdown(f"**Lifespan ROI (before tax):** {lifespan_roi_before_tax:.2%}")
st.markdown(f"**Lifespan ROI (after tax):** {lifespan_roi_after_tax:.2%}")
st.markdown(f"**IRR:** {irr:.2%}")
st.markdown(f"**NPV (at 12% discount rate):** ${npv:,.2f}")
st.markdown(f"**Payback Period:** {payback_period} years")

st.subheader("Flows")
st.json(flows)

st.subheader("Updated Prices")
st.json(updated_prices)

st.subheader("Minimum Selling Prices (MSPs)")
for product in ['wet_BC', 'freeze_BC', 'oven_BC']:
    st.markdown(f"- **{product}:** MSP: ${price_boundaries_dict[product]['msp']:.2f}/kg")

st.subheader("CAPEX breakdown")
st.dataframe(pd.DataFrame(list(capex_breakdown.items()), columns=["Item", "Value"]))

st.subheader("OPEX breakdown")
st.dataframe(pd.DataFrame(list(opex_breakdown.items()), columns=["Item", "Value"]))

st.subheader("Financial Summary Table (Years as Columns)")
table_data = {}
metrics = [
    ('production', 'wet_bc (Kg/ day)'),
    ('production', 'freeze_bc (Kg/ day)'),
    ('production', 'oven_bc (Kg/ day)'),
    ('revenue_daily', 'revenue_starch (USD)'),
    ('revenue_daily', 'revenue_wet_BC (USD)'),
    ('revenue_daily', 'revenue_freeze_BC (USD)'),
    ('revenue_daily', 'revenue_oven_BC (USD)'),
    ('revenue_daily', 'revenue_total (USD)'),
    ('costs_daily', 'opex_total (USD)'),
    ('profit', 'gross_profit (USD)'),
    ('profit', 'annual_gross (USD)'),
    ('profit', 'taxable_income (USD)'),
    ('profit', 'net_profit (USD)'),
    ('profit', 'annual_roi(before_tax) (%)'),
    ('profit', 'annual_roi(after_tax) ($)'),
    ('cash_flow', 'operating_cash_flow (USD)'),
    ('cash_flow', 'free_cash_flow (USD)')
]
for category, metric in metrics:
    row_name = f"{category} - {metric}" if category != metric else metric
    table_data[row_name] = {year: financial_summary[year][category][metric] for year in financial_summary}
df_table = pd.DataFrame(table_data).T
df_table.columns = [f'Year {col}' for col in df_table.columns]
st.dataframe(df_table)

# --- Plots ---
st.subheader("Financial Performance Over Time")
years = list(financial_summary.keys())
annual_roi_before_tax = [financial_summary[year]['profit']['annual_roi(before_tax) (%)'] for year in years]
annual_roi_after_tax = [financial_summary[year]['profit']['annual_roi(after_tax) ($)'] for year in years]
fcf = [financial_summary[year]['cash_flow']['free_cash_flow (USD)'] for year in years]
cumulative_fcf = [sum(fcf[:i+1]) for i in range(len(fcf))]

fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(years, np.array(cumulative_fcf)/10**6, label='Cumulative FCF', marker='o', color='gray')
ax1.plot(years, np.array(fcf)/10**6, label='FCF', marker='x', color='gray')
ax1.set_xlabel('Year')
ax1.set_ylabel('Cash Flow in USD (M)', color='gray')
ax1.tick_params(axis='y', labelcolor='gray')
ax1.set_ylim(min(cumulative_fcf)/10**6 * 1.05, max(cumulative_fcf)/10**6 * 1.05)
ax2 = ax1.twinx()
ax2.plot(years, annual_roi_before_tax, label='Annual ROI (Before Tax)', marker='s', color='black' , linestyle='--')
ax2.plot(years, annual_roi_after_tax, label='Annual ROI (After Tax)', marker='^', color='black', linestyle='--')
ax2.set_ylabel('ROI (Percentage)', color='black')
ax2.tick_params(axis='y', labelcolor='black')
ax2.set_ylim(5, 30)
fig.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=3)
st.pyplot(fig)

st.subheader("CAPEX Breakdown Pie Chart")
capex_labels = list(capex_breakdown.keys())
capex_sizes = list(capex_breakdown.values())
combined_capex = {}
other_capex_size = 0
for i in range(len(capex_sizes)):
    percentage = (capex_sizes[i] / total_capex) * 100
    if percentage > 4.5:
        combined_capex[capex_labels[i]] = capex_sizes[i]
    else:
        other_capex_size += capex_sizes[i]
if other_capex_size > 0:
    combined_capex['Other'] = other_capex_size
combined_capex_labels = [f'{label.replace("_", " ")} ({size/total_capex:.1%})' for label, size in combined_capex.items()]
combined_capex_sizes = list(combined_capex.values())
fig1, ax1 = plt.subplots(figsize=(8, 6))
ax1.pie(combined_capex_sizes, labels=combined_capex_labels, startangle=90, colors=plt.cm.viridis(np.linspace(0, 1, len(combined_capex_sizes))), textprops={'fontsize': 14})
ax1.axis('equal')
plt.title('CAPEX Breakdown', fontsize=18, fontweight='bold')
st.pyplot(fig1)

st.subheader("OPEX Breakdown Pie Chart (Year 1)")
year_1_opex = financial_summary[1]['costs_daily']['detailed_opex (USD)']
opex_labels = list(year_1_opex.keys())
opex_sizes = list(year_1_opex.values())
total_opex_year1 = sum(opex_sizes)
combined_opex = {}
other_opex_size = 0
for i in range(len(opex_sizes)):
    percentage = (opex_sizes[i] / total_opex_year1) * 100
    if percentage > 4.5:
        combined_opex[opex_labels[i]] = opex_sizes[i]
    else:
        other_opex_size += opex_sizes[i]
if other_opex_size > 0:
    combined_opex['Other'] = other_opex_size
combined_opex_labels = [f'{label.replace("_", " ")} ({size/total_opex_year1:.1%})' for label, size in combined_opex.items()]
combined_opex_sizes = list(combined_opex.values())
fig2, ax2 = plt.subplots(figsize=(8, 6))
ax2.pie(combined_opex_sizes, labels=combined_opex_labels, startangle=90, colors=plt.cm.viridis(np.linspace(0, 1, len(combined_opex_sizes))), textprops={'fontsize': 14})
ax2.axis('equal')
plt.title('OPEX Breakdown', fontsize=18, fontweight='bold')
st.pyplot(fig2)

st.success("Calculation Complete! You can download the financial summary and comprehensive output CSVs from the working directory.")