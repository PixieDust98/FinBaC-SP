import numpy as np
import numpy_financial as npf
import ast

def load_parameters(filepath="config/parameters.txt"):
    params = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                value = value.strip()
                # Try to convert to float, int, dict, list, etc.
                try:
                    # Try parsing as Python literal if possible
                    params[key.strip()] = ast.literal_eval(value)
                except Exception:
                    params[key.strip()] = value
    return params

def calculate_flows(
    potato_input_kg,
    starch_yield,
    waste_starch_content,
    waste_sugar_content,
    hydrolysis_efficiency,
    sugar_concentration,
    fermentation_time,
    max_bioreactor_volume,
    bc_productivity
):
    pure_starch = potato_input_kg * starch_yield
    total_waste = potato_input_kg * (1 - starch_yield)
    solid_waste = total_waste * 0.94
    liquid_waste = total_waste * 0.06

    starch_from_solid_waste = solid_waste * waste_starch_content
    sugar_from_solid_waste = (starch_from_solid_waste * hydrolysis_efficiency) * (36/40)
    sugar_from_liquid_waste = liquid_waste * waste_sugar_content * (8/30)

    total_sugar = sugar_from_solid_waste + sugar_from_liquid_waste

    total_sugar_g = total_sugar * 1000
    required_volume_L = total_sugar_g / sugar_concentration * fermentation_time / 24
    actual_volume_L = min(required_volume_L, max_bioreactor_volume)
    daily_bc_kg = actual_volume_L * bc_productivity * fermentation_time / 1000

    pure_starch_in_BC = actual_volume_L * 4 / 1000

    return {
        'pure_starch': pure_starch,
        'pure_starch_in_BC': pure_starch_in_BC,
        'solid_waste': solid_waste,
        'liquid_waste': liquid_waste,
        'sugar_from_solid': sugar_from_solid_waste,
        'sugar_from_liquid': sugar_from_liquid_waste,
        'total_wet_bc': daily_bc_kg,
        'bioreactor_volume': actual_volume_L,
        'wastewater': actual_volume_L - daily_bc_kg * 0.99 + liquid_waste * 22 / 8,
        'required BioReactor Volume': required_volume_L,
        'actual BioReactor Volume': actual_volume_L
    }

def calculate_financials(
    production,
    ratios,
    year,
    prices,
    freeze_dry_weight_loss,
    oven_dry_weight_loss,
    freeze_drying_energy,
    oven_drying_energy,
    energy_cost_per_kwh,
    NaOH_for_purification,
    Water_for_washing,
    Water_treatment,
    opex_breakdown,
    operating_days,
    total_capex,
    life_span
):
    wet_bc = production['total_wet_bc'] * ratios[0]
    freeze_bc = (production['total_wet_bc'] * ratios[1]) * (1 - freeze_dry_weight_loss)
    oven_bc = (production['total_wet_bc'] * ratios[2]) * (1 - oven_dry_weight_loss)

    price_increase_factor = (1 + 0.021) ** (year - 1)
    prices_inflated = {
        'starch': prices['starch'] * price_increase_factor,
        'wet_BC': prices['wet_BC'] * price_increase_factor,
        'freeze_BC': prices['freeze_BC'] * price_increase_factor,
        'oven_BC': prices['oven_BC'] * price_increase_factor
    }

    revenue_breakdown = {
        'starch': production['pure_starch'] * prices_inflated['starch'],
        'wet_BC': wet_bc * prices_inflated['wet_BC'],
        'freeze_BC': freeze_bc * prices_inflated['freeze_BC'],
        'oven_BC': oven_bc * prices_inflated['oven_BC']
    }
    revenue = sum(revenue_breakdown.values())

    inflation_factor = (1 + 0.02) ** (year - 1)

    alkali_wash_cost = production['total_wet_bc'] * (NaOH_for_purification + Water_for_washing) * inflation_factor

    freeze_drying_cost = freeze_bc * freeze_drying_energy * energy_cost_per_kwh * inflation_factor / (1 - freeze_dry_weight_loss)
    oven_drying_cost = oven_bc * oven_drying_energy * energy_cost_per_kwh * inflation_factor / (1 - oven_dry_weight_loss)

    wastewater_cost = production['wastewater'] * Water_treatment * inflation_factor

    detailed_opex = {key: value * inflation_factor for key, value in opex_breakdown.items()}
    detailed_opex['Freeze_drying_electricity'] = freeze_drying_cost
    detailed_opex['Oven_drying_electricity'] = oven_drying_cost
    detailed_opex['Alkali_wash'] = alkali_wash_cost
    detailed_opex['water_treatment'] = wastewater_cost
    adjusted_opex = sum(detailed_opex.values())

    annual_opex = adjusted_opex * operating_days
    annual_costs = total_capex if year == 1 else annual_opex

    gross_profit = revenue - adjusted_opex
    annual_gross = gross_profit * operating_days

    annual_depreciation_expense = total_capex / life_span
    taxable_income = annual_gross - annual_depreciation_expense
    annual_taxes = taxable_income * 0.25

    net_profit = taxable_income * (1 - 0.25)

    operating_cash_flow = annual_gross - annual_taxes
    investing_cash_flow = -total_capex if year == 1 else 0
    free_cash_flow = operating_cash_flow + investing_cash_flow

    return {
        'production': {
            'wet_bc (Kg/ day)': wet_bc,
            'freeze_bc (Kg/ day)': freeze_bc,
            'oven_bc (Kg/ day)': oven_bc,
        },
        'revenue_daily': {
            'revenue_starch (USD)': revenue_breakdown['starch'],
            'revenue_wet_BC (USD)': revenue_breakdown['wet_BC'],
            'revenue_freeze_BC (USD)': revenue_breakdown['freeze_BC'],
            'revenue_oven_BC (USD)': revenue_breakdown['oven_BC'],
            'revenue_total (USD)': revenue,
        },
        'costs_daily': {
            'detailed_opex (USD)': detailed_opex,
            'freeze_drying (USD)': freeze_drying_cost,
            'oven_drying (USD)': oven_drying_cost,
            'wastewater (USD)': wastewater_cost,
            'opex_total (USD)': adjusted_opex,
        },
        'annual_costs': {'CAPEX+OPEX': annual_costs},
        'profit':{
            'gross_profit (USD)': gross_profit,
            'annual_gross (USD)': annual_gross,
            'taxable_income (USD)': taxable_income,
            'net_profit (USD)': net_profit,
            'annual_roi(before_tax) (%)': 100 * annual_gross / annual_costs,
            'annual_roi(after_tax) ($)': 100 * net_profit / annual_costs,
        },
        'cash_flow': {
            'operating_cash_flow (USD)': operating_cash_flow,
            'investing_cash_flow (USD)': investing_cash_flow,
            'free_cash_flow (USD)': free_cash_flow
        }
    }

def calculate_npvs_for_production_cases(
    prices,
    discount_rate,
    potato_input_kg,
    starch_yield,
    waste_starch_content,
    waste_sugar_content,
    hydrolysis_efficiency,
    sugar_concentration,
    fermentation_time,
    max_bioreactor_volume,
    bc_productivity,
    ratios,
    freeze_dry_weight_loss,
    oven_dry_weight_loss,
    freeze_drying_energy,
    oven_drying_energy,
    energy_cost_per_kwh,
    NaOH_for_purification,
    Water_for_washing,
    Water_treatment,
    opex_breakdown,
    operating_days,
    total_capex,
    life_span
):
    flows = calculate_flows(
        potato_input_kg, starch_yield, waste_starch_content, waste_sugar_content,
        hydrolysis_efficiency, sugar_concentration, fermentation_time,
        max_bioreactor_volume, bc_productivity
    )

    def calculate_npv_for_case(local_ratios):
        cash_flows = []
        for year in range(1, int(life_span) + 1):
            financials_year = calculate_financials(
                flows, local_ratios, year, prices,
                freeze_dry_weight_loss, oven_dry_weight_loss,
                freeze_drying_energy, oven_drying_energy,
                energy_cost_per_kwh, NaOH_for_purification,
                Water_for_washing, Water_treatment,
                opex_breakdown, operating_days, total_capex, life_span
            )
            cash_flows.append(financials_year["cash_flow"]["free_cash_flow (USD)"])
        npv = npf.npv(discount_rate, cash_flows)
        return npv

    npv_wet_bc = calculate_npv_for_case([1.0, 0.0, 0.0])
    npv_freeze_bc = calculate_npv_for_case([0.0, 1.0, 0.0])
    npv_oven_bc = calculate_npv_for_case([0.0, 0.0, 1.0])

    return {'wet_BC': npv_wet_bc, 'freeze_BC': npv_freeze_bc, 'oven_BC': npv_oven_bc}

def find_price_boundaries_all_products(
    product_prices,
    step,
    discount_rate,
    potato_input_kg,
    starch_yield,
    waste_starch_content,
    waste_sugar_content,
    hydrolysis_efficiency,
    sugar_concentration,
    fermentation_time,
    max_bioreactor_volume,
    bc_productivity,
    ratios,
    freeze_dry_weight_loss,
    oven_dry_weight_loss,
    freeze_drying_energy,
    oven_drying_energy,
    energy_cost_per_kwh,
    NaOH_for_purification,
    Water_for_washing,
    Water_treatment,
    opex_breakdown,
    operating_days,
    total_capex,
    life_span
):
    def is_positive_npv(price, product):
        product_prices[product] = price
        npvs = calculate_npvs_for_production_cases(
            product_prices, discount_rate,
            potato_input_kg, starch_yield, waste_starch_content, waste_sugar_content,
            hydrolysis_efficiency, sugar_concentration, fermentation_time,
            max_bioreactor_volume, bc_productivity, ratios,
            freeze_dry_weight_loss, oven_dry_weight_loss,
            freeze_drying_energy, oven_drying_energy,
            energy_cost_per_kwh, NaOH_for_purification,
            Water_for_washing, Water_treatment,
            opex_breakdown, operating_days, total_capex, life_span
        )
        return npvs[product] > 0

    def is_negative_npv(price, product):
        product_prices[product] = price
        npvs = calculate_npvs_for_production_cases(
            product_prices, discount_rate,
            potato_input_kg, starch_yield, waste_starch_content, waste_sugar_content,
            hydrolysis_efficiency, sugar_concentration, fermentation_time,
            max_bioreactor_volume, bc_productivity, ratios,
            freeze_dry_weight_loss, oven_dry_weight_loss,
            freeze_drying_energy, oven_drying_energy,
            energy_cost_per_kwh, NaOH_for_purification,
            Water_for_washing, Water_treatment,
            opex_breakdown, operating_days, total_capex, life_span
        )
        return npvs[product] < 0

    price_boundaries = {}
    for product in ['wet_BC', 'freeze_BC', 'oven_BC']:
        low, high = 0, product_prices[product]
        while not is_positive_npv(high, product):
            high *= 10
        while high - low > step:
            mid = (low + high) / 2
            if is_positive_npv(mid, product):
                high = mid
            else:
                low = mid
        min_price = high
        product_prices[product] = min_price
        npv_min = calculate_npvs_for_production_cases(
            product_prices, discount_rate,
            potato_input_kg, starch_yield, waste_starch_content, waste_sugar_content,
            hydrolysis_efficiency, sugar_concentration, fermentation_time,
            max_bioreactor_volume, bc_productivity, ratios,
            freeze_dry_weight_loss, oven_dry_weight_loss,
            freeze_drying_energy, oven_drying_energy,
            energy_cost_per_kwh, NaOH_for_purification,
            Water_for_washing, Water_treatment,
            opex_breakdown, operating_days, total_capex, life_span
        )[product]

        low, high = 0, product_prices[product]
        while not is_negative_npv(low, product):
            low = product_prices[product] / 10 if low == 0 else low / 10
        while high - low > step:
            mid = (low + high) / 2
            if is_negative_npv(mid, product):
                low = mid
            else:
                high = mid
        max_price = low
        product_prices[product] = max_price
        npv_max = calculate_npvs_for_production_cases(
            product_prices, discount_rate,
            potato_input_kg, starch_yield, waste_starch_content, waste_sugar_content,
            hydrolysis_efficiency, sugar_concentration, fermentation_time,
            max_bioreactor_volume, bc_productivity, ratios,
            freeze_dry_weight_loss, oven_dry_weight_loss,
            freeze_drying_energy, oven_drying_energy,
            energy_cost_per_kwh, NaOH_for_purification,
            Water_for_washing, Water_treatment,
            opex_breakdown, operating_days, total_capex, life_span
        )[product]

        price_boundaries[product] = {
            'min_price': min_price,
            'max_price': max_price,
            'npv_min': npv_min,
            'npv_max': npv_max,
            'msp': (min_price + max_price) / 2
        }

    return price_boundaries