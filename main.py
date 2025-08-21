from utils import (
    load_parameters,
    calculate_flows,
    calculate_financials,
    calculate_npvs_for_production_cases,
    find_price_boundaries_all_products
)
import numpy as np
import numpy_financial as npf
import pandas as pd
import json
import matplotlib.pyplot as plt

# Load all parameters from parameters.txt
params = load_parameters("config/parameters.txt")

# Unpack parameters for readability
potato_input_kg = params["potato_input_kg"]
operating_days = params["operating_days"]
fermentation_time = params["fermentation_time"]
life_span = params["life_span"]
starch_yield = params["starch_yield"]
freeze_dry_weight_loss = params["freeze_dry_weight_loss"]
oven_dry_weight_loss = params["oven_dry_weight_loss"]
freeze_drying_energy = params["freeze_drying_energy"]
oven_drying_energy = params["oven_drying_energy"]
energy_cost_per_kwh = params["energy_cost_per_kwh"]
NaOH_for_purification = params["NaOH_for_purification"]
Water_for_washing = params["Water_for_washing"]
Water_treatment = params["Water_treatment"]
bc_productivity = params["bc_productivity"]
sugar_concentration = params["sugar_concentration"]
max_bioreactor_volume = params["max_bioreactor_volume"]
waste_starch_content = params["waste_starch_content"]
waste_sugar_content = params["waste_sugar_content"]
hydrolysis_efficiency = params["hydrolysis_efficiency"]
ratios = params["ratios"]
capex_breakdown = params["capex_breakdown"]
opex_breakdown = params["opex_breakdown"]
prices = params["prices"]

total_capex = sum(capex_breakdown.values())

# Calculations
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

# Calculate overall lifespan metrics
total_profit_before_tax = sum(financial_summary[year]['profit']['annual_gross (USD)'] for year in financial_summary)
total_profit_after_tax = sum(financial_summary[year]['profit']['net_profit (USD)'] for year in financial_summary)
total_costs = sum(financial_summary[year]['annual_costs']['CAPEX+OPEX'] for year in financial_summary)

lifespan_roi_before_tax = total_profit_before_tax / total_costs
lifespan_roi_after_tax = total_profit_after_tax / total_costs

# IRR and NPV calculations
cash_flows = [financial_summary[year]['cash_flow']['free_cash_flow (USD)'] for year in financial_summary]
irr = npf.irr(cash_flows)
npv = npf.npv(0.12, cash_flows) # Discount rate of 12%

# Payback period calculation
cumulative_cash_flow = 0
payback_period = 0
for year in financial_summary:
    cumulative_cash_flow += financial_summary[year]['cash_flow']['free_cash_flow (USD)']
    if cumulative_cash_flow >= 0:
        payback_period = year
        break

# Save financial_summary to JSON
with open('financial_summary.json', 'w') as f:
    json.dump(financial_summary, f, indent=2)

# Extract metrics for table
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
table_data = {}
for category, metric in metrics:
    row_name = f"{category} - {metric}" if category != metric else metric
    table_data[row_name] = {year: financial_summary[year][category][metric] for year in financial_summary}

df_table = pd.DataFrame(table_data).T
df_table.columns = [f'Year {col}' for col in df_table.columns]
df_table.to_csv('financial_summary_table.csv')

# Comprehensive output DataFrame
def add_section_header(df, header_text):
    header_df = pd.DataFrame([{'Metric': header_text, 'Value': ''}])
    return pd.concat([df, header_df], ignore_index=True)

df = pd.DataFrame({
    'Metric': [
        'Daily Potato Input (kg)',
        'Operating Days/Year',
        'Fermentation Time (hours/batch)',
        'Life Span (years)'
    ],
    'Value': [
        potato_input_kg,
        operating_days,
        fermentation_time,
        life_span
    ]
})
df = add_section_header(df, "=== RAW MATERIALS ===")
raw_materials_df = pd.DataFrame([
    {'Metric': 'Potatoes (kg/day)', 'Value': potato_input_kg},
    {'Metric': 'HS Medium (L/day)', 'Value': opex_breakdown['HS_medium']},
    {'Metric': 'Hydrolysis Enzymes (USD/day)', 'Value': opex_breakdown['Hydrolysis_enzymes']}
])
df = pd.concat([df, raw_materials_df], ignore_index=True)
df = add_section_header(df, "=== UTILITIES ===")
utilities_df = pd.DataFrame([
    {'Metric': 'Electricity (kWh/day)', 'Value': 400},  # Example static value
    {'Metric': 'Water (m³/day)', 'Value': 10},  # Example static value
    {'Metric': 'Steam (USD/day)', 'Value': opex_breakdown['Steam']},
    {'Metric': 'Cooling (USD/day)', 'Value': opex_breakdown['Cooling']}
])
df = pd.concat([df, utilities_df], ignore_index=True)
df = add_section_header(df, "=== LABOR ===")
labor_df = pd.DataFrame([
    {'Metric': 'Labor (USD/day)', 'Value': opex_breakdown['Labor']},
    {'Metric': 'Quality Control (USD/day)', 'Value': opex_breakdown['Quality_control']}
])
df = pd.concat([df, labor_df], ignore_index=True)
df = add_section_header(df, "=== WASTE DISPOSAL ===")
waste_disposal_df = pd.DataFrame([
    {'Metric': 'Waste Disposal (USD/day)', 'Value': opex_breakdown['Waste_disposal']}
])
df = pd.concat([df, waste_disposal_df], ignore_index=True)
df = add_section_header(df, "=== OTHER COSTS ===")
other_costs_df = pd.DataFrame([
    {'Metric': 'Maintenance (USD/day)', 'Value': opex_breakdown['Maintenance']},
    {'Metric': 'Insurance (USD/day)', 'Value': opex_breakdown['Insurance']},
    {'Metric': 'Administrative (USD/day)', 'Value': opex_breakdown['Administrative']},
    {'Metric': 'Alkali Treatment (USD/day)', 'Value': opex_breakdown['Alkali_treatment_fixed']}
])
df = pd.concat([df, other_costs_df], ignore_index=True)
df = add_section_header(df, "=== FLOWS ===")
flows_df = pd.DataFrame(flows.items(), columns=['Metric', 'Value'])
df = pd.concat([df, flows_df], ignore_index=True)
df = add_section_header(df, "=== UPDATED PRICES ===")
prices_df = pd.DataFrame(updated_prices.items(), columns=['Metric', 'Value'])
prices_df['Value'] = prices_df['Value'].apply(lambda x: f"${x:.2f}/kg")
df = pd.concat([df, prices_df], ignore_index=True)
df = add_section_header(df, "=== DETAILED CAPEX BREAKDOWN ===")
capex_df = pd.DataFrame(capex_breakdown.items(), columns=['Metric', 'Value'])
capex_df['Value'] = capex_df['Value'].apply(lambda x: f"${x:,.2f}")
df = pd.concat([df, capex_df], ignore_index=True)
df = pd.concat([df, pd.DataFrame([{'Metric': 'Total CAPEX', 'Value': f"${total_capex:,.2f}"}])], ignore_index=True)
df = add_section_header(df, "=== DETAILED OPEX BREAKDOWN (YEAR 1) ===")
year_1_opex = financial_summary[1]['costs_daily']['detailed_opex (USD)']
opex_df = pd.DataFrame(year_1_opex.items(), columns=['Metric', 'Value'])
opex_df['Value'] = opex_df['Value'].apply(lambda x: f"${x:,.2f}")
df = pd.concat([df, opex_df], ignore_index=True)
df = pd.concat([df, pd.DataFrame([{'Metric': 'Total OPEX (Year 1)', 'Value': f"${financial_summary[1]['costs_daily']['opex_total (USD)']:,.2f}"}])], ignore_index=True)
df = add_section_header(df, "=== MINIMUM SELLING PRICES (MSPs) ===")
msps_df = pd.DataFrame([{'Metric': product, 'Value': f"${price_boundaries_dict[product]['msp']:.2f}/kg"} for product in ['wet_BC', 'freeze_BC', 'oven_BC']])
df = pd.concat([df, msps_df], ignore_index=True)
df = add_section_header(df, "=== LIFESPAN FINANCIAL METRICS ===")
financial_metrics_df = pd.DataFrame([
    {'Metric': 'Lifespan ROI (before tax)', 'Value': f"{lifespan_roi_before_tax:.2%}"},
    {'Metric': 'Lifespan ROI (after tax)', 'Value': f"{lifespan_roi_after_tax:.2%}"},
    {'Metric': 'IRR', 'Value': f"{irr:.2%}"},
    {'Metric': 'NPV (at 12% discount rate)', 'Value': f"${npv:,.2f}"},
    {'Metric': 'Payback Period (years)', 'Value': payback_period}
])
df = pd.concat([df, financial_metrics_df], ignore_index=True)
df.to_csv('comprehensive_output.csv', index=False)

# Plotting: ROI and FCF
years = list(financial_summary.keys())
annual_roi_before_tax = [financial_summary[year]['profit']['annual_roi(before_tax) (%)'] for year in years]
annual_roi_after_tax = [financial_summary[year]['profit']['annual_roi(after_tax) ($)'] for year in years]
fcf = [financial_summary[year]['cash_flow']['free_cash_flow (USD)'] for year in years]
cumulative_fcf = [sum(fcf[:i+1]) for i in range(len(fcf))]

fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(years, np.array(cumulative_fcf)/10**6, label='Cumulative FCF', marker='o', color='gray')
ax1.plot(years, np.array(fcf)/10**6, label='FCF', marker='x', color='gray')
ax1.set_xlabel('Year', fontsize=14)
ax1.set_ylabel('Cash Flow in USD (M)', color='gray', fontsize=14)
ax1.tick_params(axis='y', labelcolor='gray', labelsize=12)
ax1.tick_params(axis='x', labelsize=12)
ax1.set_ylim(min(cumulative_fcf)/10**6 * 1.05, max(cumulative_fcf)/10**6 * 1.05)
ax2 = ax1.twinx()
ax2.plot(years, annual_roi_before_tax, label='Annual ROI (Before Tax)', marker='s', color='black' , linestyle='--')
ax2.plot(years, annual_roi_after_tax, label='Annual ROI (After Tax)', marker='^', color='black', linestyle='--')
ax2.set_ylabel('ROI (Percentage)', color='black', fontsize=14)
ax2.tick_params(axis='y', labelcolor='black', labelsize=12)
ax2.set_ylim(5, 30)
plt.title('Financial Performance over Time', fontsize=14, y=1.12)
plt.grid(False)
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=len(labels + labels2), fontsize=14)
plt.set_cmap('gray')
plt.savefig('financial_performance.svg', format='svg', bbox_inches='tight')
plt.show()

# CAPEX Pie Chart
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
fig1, ax1 = plt.subplots(figsize=(10, 8))
ax1.pie(combined_capex_sizes, labels=combined_capex_labels, startangle=90, colors=plt.cm.viridis(np.linspace(0, 1, len(combined_capex_sizes))), textprops={'fontsize': 18})
ax1.axis('equal')
plt.title('CAPEX Breakdown', fontsize=24, fontweight='bold')
plt.show()

# OPEX Pie Chart (Year 1)
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
fig2, ax2 = plt.subplots(figsize=(10, 8))
ax2.pie(combined_opex_sizes, labels=combined_opex_labels, startangle=90, colors=plt.cm.viridis(np.linspace(0, 1, len(combined_opex_sizes))), textprops={'fontsize': 18})
ax2.axis('equal')
plt.title('OPEX Breakdown', fontsize=24, fontweight='bold')
plt.show()

print("Financial summary saved to financial_summary.json")
print("Comprehensive output saved to comprehensive_output.csv")
print("Financial performance plot saved to financial_performance.svg")
