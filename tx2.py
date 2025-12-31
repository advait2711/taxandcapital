import streamlit as st

# --- Tax Calculation Engine (Helper Functions) ---

def get_tax_slabs(regime, age):
    """
    Returns the correct tax slabs and rates based on regime and age.
    Slabs are (upper_limit, rate)
    """
    if regime == "New (Default)":
        return [
            (400000, 0.0),
            (800000, 0.05),
            (1200000, 0.10),
            (1600000, 0.15),
            (2000000, 0.20),
            (2400000, 0.25),
            (float('inf'), 0.30),
        ]
    else:  # Old Regime
        if age >= 80:  # Super Senior Citizen
            return [
                (500000, 0.0),
                (1000000, 0.20),
                (float('inf'), 0.30),
            ]
        elif age >= 60:  # Senior Citizen
            return [
                (300000, 0.0),
                (500000, 0.05),
                (1000000, 0.20),
                (float('inf'), 0.30),
            ]
        else:  # Below 60
            return [
                (250000, 0.0),
                (500000, 0.05),
                (1000000, 0.20),
                (float('inf'), 0.30),
            ]

def calculate_slab_tax(income, slabs):
    """Calculates tax based on income and a given slab structure."""
    tax = 0
    last_limit = 0
    for limit, rate in slabs:
        if income > last_limit:
            taxable_amount_in_slab = min(income - last_limit, limit - last_limit)
            tax += taxable_amount_in_slab * rate
            last_limit = limit
        else:
            break
    return tax

def calculate_rebate_and_relief(regime, net_taxable_income, basic_tax):
    """
    Calculates Tax Rebate under Sec 87A and its associated Marginal Relief.
    Returns (rebate, marginal_relief_87a, tax_after_rebate)
    """
    rebate = 0
    marginal_relief_87a = 0
    tax_after_rebate = basic_tax

    if regime == "New (Default)":
        if net_taxable_income <= 1200000:
            rebate = min(basic_tax, 60000)
            tax_after_rebate = basic_tax - rebate
        elif net_taxable_income > 1200000 and net_taxable_income <= 1270000: # Approx limit for relief
            # Marginal Relief for Rebate
            income_over_limit = net_taxable_income - 1200000
            if basic_tax > income_over_limit:
                marginal_relief_87a = basic_tax - income_over_limit
                tax_after_rebate = basic_tax - marginal_relief_87a
    else: # Old Regime
        if net_taxable_income <= 500000:
            rebate = min(basic_tax, 12500)
            tax_after_rebate = basic_tax - rebate
            
    return rebate, marginal_relief_87a, tax_after_rebate


def calculate_surcharge(total_taxable_income, regime, tax_on_normal, tax_on_special_capped, tax_on_special_uncapped):
    """
    Calculates the 'blended' surcharge with the 15% cap on special incomes.
    Returns (total_surcharge, surcharge_rate_normal, surcharge_rate_special_cap)
    """
    surcharge_rate_normal = 0
    surcharge_rate_special_cap = 0
    
    # 1. Determine the applicable surcharge rate based on Total Income
    if total_taxable_income > 50000000: # 5 Crore
        surcharge_rate_normal = 0.37 if regime == "Old (Opt-in)" else 0.25
    elif total_taxable_income > 20000000: # 2 Crore
        surcharge_rate_normal = 0.25
    elif total_taxable_income > 10000000: # 1 Crore
        surcharge_rate_normal = 0.15
    elif total_taxable_income > 5000000: # 50 Lakh
        surcharge_rate_normal = 0.10
    
    # 2. The surcharge on special income (111A, 112A, etc.) is CAPPED at 15%
    surcharge_rate_special_cap = min(surcharge_rate_normal, 0.15)

    # 3. Calculate blended surcharge
    # 'Winnings' (uncapped) are surcharged at the full normal rate
    surcharge_on_normal_and_winnings = (tax_on_normal + tax_on_special_uncapped) * surcharge_rate_normal
    surcharge_on_special_capped_tax = tax_on_special_capped * surcharge_rate_special_cap
    
    total_surcharge = surcharge_on_normal_and_winnings + surcharge_on_special_capped_tax
    
    return total_surcharge, surcharge_rate_normal, surcharge_rate_special_cap

def calculate_marginal_relief_surcharge(total_taxable_income, tax_after_rebate, total_surcharge, regime, age, special_incomes):
    """
    Calculates marginal relief on surcharge.
    This is a simplified model for demonstration.
    """
    
    tax_plus_surcharge = tax_after_rebate + total_surcharge
    relief = 0
    
    thresholds = [(50000000, 0.37 if regime == "Old (Opt-in)" else 0.25), 
                  (20000000, 0.25), 
                  (10000000, 0.15), 
                  (5000000, 0.10)]
    
    # Find the highest threshold breached
    for threshold, rate in thresholds:
        if total_taxable_income > threshold:
            
            income_over_threshold = total_taxable_income - threshold
            
            # --- Simplified Recalculation at Threshold ---
            # This simplification calculates tax on the threshold amount as if it's all "normal income"
            # for the purpose of finding the base tax.
            slabs = get_tax_slabs(regime, age)
            tax_at_threshold_basic = calculate_slab_tax(threshold, slabs)
            
            # Surcharge at threshold (is 0, 10, 15, 25)
            
            surcharge_at_threshold = 0
            if threshold == 50000000: surcharge_at_threshold = tax_at_threshold_basic * 0.25
            elif threshold == 20000000: surcharge_at_threshold = tax_at_threshold_basic * 0.15
            elif threshold == 10000000: surcharge_at_threshold = tax_at_threshold_basic * 0.10
            elif threshold == 5000000: surcharge_at_threshold = 0 # Surcharge *starts* after 50L
            
            tax_at_threshold_total = tax_at_threshold_basic + surcharge_at_threshold
            
            # This is the core logic
            max_payable = tax_at_threshold_total + income_over_threshold
            
            if tax_plus_surcharge > max_payable:
                relief = tax_plus_surcharge - max_payable
                
            break # We only apply relief from the *first* threshold breached
            
    return relief

# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="Indian Tax Calculator FY 2025-26")

st.title("🇮🇳 Indian Income Tax Calculator")
st.subheader("For Financial Year 2025-26 (Assessment Year 2026-27)")

# --- Sidebar for Global Settings ---
st.sidebar.header("Global Settings")
tax_regime = st.sidebar.radio(
    "1. Choose Your Tax Regime",
    ["New (Default)", "Old (Opt-in)"],
    help="The New Regime is the default. You must specifically opt-in to use the Old Regime."
)

age = st.sidebar.slider("2. Your Age", 18, 100, 30)
age_category = "Below 60"
if age >= 80:
    age_category = "Super Senior (80+)"
elif age >= 60:
    age_category = "Senior (60-79)"
st.sidebar.markdown(f"**Age Category:** `{age_category}`")


is_salaried = st.sidebar.checkbox("Are you a Salaried Individual or Pensioner?", True)
st.sidebar.markdown("---")
st.sidebar.info(
    """
    **FY 2025-26 (AY 2026-27) Updates:**
    * **New Regime:** Default, Rebate up to **₹12,00,000** taxable income, Standard Deduction of **₹75,000**.
    * **Old Regime:** Rebate up to **₹5,00,000** taxable income, Standard Deduction of **₹50,000**.
    * **Capital Gains:** STCG (Equity) @ **20%**, LTCG (Equity) @ **12.5%** over ₹1.25L.
    """
)

# --- Main Page Layout (Income & Deductions) ---

col1, col2 = st.columns(2)

# --- Column 1: Income Details ---
with col1:
    st.header("1. Your Annual Income")
    st.info("Enter all your income from different sources for the full year.")

    salary_income = st.number_input(
        "Income from Salary / Pension",
        min_value=0.0,
        value=1000000.0,
        step=10000.0,
        help="Enter your gross salary. Standard Deduction will be applied automatically."
    )
    
    house_property_income = st.number_input(
        "Income from House Property (Gross Rent)",
        min_value=0.0,
        value=0.0,
        step=5000.0,
        help="Enter your *gross* rental income. A 30% standard deduction will be applied automatically."
    )
    
    other_sources_income = st.number_input(
        "Income from Other Sources",
        min_value=0.0,
        value=50000.0,
        step=1000.0,
        help="Interest from Savings, FDs, etc. (Do not include lottery or capital gains here)"
    )

    with st.expander("Enter Special Rate Incomes (Capital Gains, Lottery)"):
        winnings_lottery = st.number_input(
            "Winnings from Lottery, Games, etc.",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            help="Taxed at a flat 30%. No deductions or basic exemption apply."
        )
        ltcg_equity_112a = st.number_input(
            "LTCG (Equity Shares / Equity MF > 1 yr)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            help="Taxed at 12.5% on gains *above* ₹1,25,000."
        )
        stcg_equity_111a = st.number_input(
            "STCG (Equity Shares / Equity MF < 1 yr)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            help="Taxed at a flat 20%."
        )
        ltcg_other = st.number_input(
            "LTCG (Debt MF*, Gold, Real Estate)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            help="Taxed at 12.5% (without indexation). *Debt MFs purchased after 1 Apr 2023 are taxed at slab rate."
        )

# --- Column 2: Deduction Details (Chapter VI-A) ---
with col2:
    st.header("2. Your Annual Deductions")
    
    # This variable will *only* store Chapter VI-A deductions (80C, 80D, etc.)
    # Standard Deductions for Salary/Rent are applied *before* this.
    total_chapter_via_deductions = 0
    
    if tax_regime == "New (Default)":
        st.info("The New Regime has lower tax rates but fewer deductions. Only the following are allowed.")
        
        deduction_80ccd_2 = st.number_input(
            "Employer's NPS Contribution (80CCD(2))",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            help="Up to 14% of your salary (Basic + DA) is allowed."
        )
        
        deduction_family_pension = st.number_input(
            "Family Pension Deduction (57(iia))",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            max_value=15000.0,
            help="Max ₹15,000 or 1/3 of pension, whichever is lower."
        )
        
        # We sum them up. Standard Deduction for Salary is handled in the calculation block.
        total_chapter_via_deductions = deduction_80ccd_2 + deduction_family_pension

    else: # Old Regime
        st.info("The Old Regime allows a wide range of deductions to lower your taxable income.")
        
        deduction_80c = st.number_input(
            "80C (PPF, EPF, LIC, ELSS, etc.)",
            min_value=0.0,
            value=0.0,
            step=5000.0,
            max_value=150000.0,
            help="Total limit for 80C, 80CCC, 80CCD(1) is ₹1.5 Lakh"
        )
        
        deduction_nps_80ccd_1b = st.number_input(
            "80CCD(1B) (NPS Self-Contribution)",
            min_value=0.0,
            value=0.0,
            step=5000.0,
            max_value=50000.0,
            help="Additional deduction for NPS, over and above 80C."
        )

        deduction_80d = st.number_input(
            "80D (Medical Insurance Premium)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            help="e.g., ₹25k for self + ₹50k for senior citizen parents = ₹75k"
        )
        
        deduction_house_loan_interest = st.number_input(
            "Interest on Home Loan (Self-Occupied) (Sec 24b)",
            min_value=0.0,
            value=0.0,
            step=5000.0,
            max_value=200000.0,
            help="Max deduction of ₹2,00,000. This is deducted from House Property income."
        )
        
        deduction_80tta = st.number_input(
            "80TTA (Savings Account Interest)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            max_value=10000.0,
            help="Max ₹10,000. Not for Senior Citizens."
        ) if age < 60 else 0.0
        
        deduction_80ttb = st.number_input(
            "80TTB (Deposit Interest - Senior Citizen)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            max_value=50000.0,
            help="Max ₹50,000 on Savings and FD interest."
        ) if age >= 60 else 0.0

        deduction_80e = st.number_input(
            "80E (Education Loan Interest)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            help="No upper limit on the interest amount."
        )
        
        deduction_80ccd_2_old = st.number_input(
            "Employer's NPS Contribution (80CCD(2))",
            min_value=0.0,
            value=0.0,
            step=1000.0
        )
        
        # Note: Sec 24(b) (Home Loan Interest) is technically not a Chapter VI-A deduction.
        # It's deducted from "Income from House Property". We will handle this in the main calculation.
        # All others are summed up.
        total_chapter_via_deductions = (deduction_80c + deduction_nps_80ccd_1b + deduction_80d + 
                                        deduction_80tta + deduction_80ttb +
                                        deduction_80e + deduction_80ccd_2_old)


# --- Calculation Button and Output ---

st.markdown("---")
if st.button("Calculate My Tax", type="primary", use_container_width=True):
    
    # --- 1. Calculate Net Income from Each Head FIRST ---
    
    # --- Head 1: Income from Salary ---
    standard_deduction_salary = 0.0
    if is_salaried:
        standard_deduction_salary = 75000.0 if tax_regime == "New (Default)" else 50000.0
    net_salary_income = salary_income - standard_deduction_salary

    # --- Head 2: Income from House Property ---
    # Both regimes allow the 30% standard deduction on rent
    standard_deduction_rent = house_property_income * 0.30
    net_house_property_income = house_property_income - standard_deduction_rent
    
    # In Old Regime, you can also deduct home loan interest (Sec 24b)
    if tax_regime == "Old (Opt-in)":
        net_house_property_income -= deduction_house_loan_interest
        # This can result in a loss (up to -200,000) which can be offset against salary.
        # For simplicity, we'll cap the loss offset at 200k (which is the input max anyway)
        net_house_property_income = max(-200000.0, net_house_property_income)


    # --- Head 3: Income from Other Sources ---
    net_other_sources_income = other_sources_income
    
    # --- Head 4: Capital Gains & Winnings (Handled Separately) ---
    special_incomes = {
        "ltcg_112a": ltcg_equity_112a,
        "stcg_111a": stcg_equity_111a,
        "ltcg_other": ltcg_other,
        "winnings": winnings_lottery
    }
    total_special_income = sum(special_incomes.values())

    # --- 2. Calculate Gross Taxable Income (GTI) ---
    # This is the sum of the *NET* of all "Normal" heads.
    # House property loss can be offset against salary income
    gti_normal_income = net_salary_income + net_house_property_income + net_other_sources_income
    gti_total = gti_normal_income + total_special_income
    
    # --- 3. Apply Chapter VI-A Deductions (80C, 80D, etc.) ---
    # These deductions (calculated in col2) are applied *after* summing all heads.
    # Crucially, these deductions CANNOT be applied to special incomes.
    
    # We can only deduct from our 'Normal Income' bucket
    deductions_to_apply = min(gti_normal_income, total_chapter_via_deductions)
    
    # This is the "Normal Income" that will be taxed at slab rates
    net_normal_taxable_income = max(0, gti_normal_income - deductions_to_apply)
    
    # This is the final total income used for Surcharge calculation
    total_taxable_income = net_normal_taxable_income + total_special_income

    # --- 4. Calculate Basic Tax ---
    
    # 4a. Tax on Special Incomes (flat rates)
    tax_on_ltcg_112a = max(0, special_incomes["ltcg_112a"] - 125000) * 0.125
    tax_on_stcg_111a = special_incomes["stcg_111a"] * 0.20
    tax_on_ltcg_other = special_incomes["ltcg_other"] * 0.125 # Simplified
    tax_on_winnings = special_incomes["winnings"] * 0.30
    
    # We must separate tax on "winnings" from other special incomes for surcharge
    tax_on_special_capped = tax_on_ltcg_112a + tax_on_stcg_111a + tax_on_ltcg_other
    tax_on_special_uncapped = tax_on_winnings
    
    # 4b. Tax on Normal Income (slab rates)
    # This is the tax on the "Normal Income" bucket
    slabs = get_tax_slabs(tax_regime, age)
    tax_on_normal = calculate_slab_tax(net_normal_taxable_income, slabs)
    
    # 4c. Total Basic Tax
    # This is the sum of tax from BOTH buckets
    total_basic_tax = tax_on_normal + tax_on_special_capped + tax_on_special_uncapped

    # --- 5. Apply Rebate & 87A Relief ---
    rebate, marginal_relief_87a, tax_after_rebate = calculate_rebate_and_relief(
        tax_regime, total_taxable_income, total_basic_tax
    )

    # --- 6. Calculate Surcharge & Marginal Relief (Surcharge) ---
    surcharge_rate_normal = 0
    surcharge_rate_special_cap = 0
    total_surcharge = 0
    
    if tax_after_rebate > 0: # No surcharge if tax is zero
        total_surcharge, surcharge_rate_normal, surcharge_rate_special_cap = calculate_surcharge(
            total_taxable_income, tax_regime, tax_on_normal, tax_on_special_capped, tax_on_special_uncapped
        )
    
    # Marginal Relief on Surcharge
    tax_plus_surcharge = tax_after_rebate + total_surcharge
    marginal_relief_surcharge = calculate_marginal_relief_surcharge(
        total_taxable_income, tax_after_rebate, total_surcharge, tax_regime, age, special_incomes
    )

    # --- 7. Apply Relief and Calculate Cess ---
    tax_payable_before_cess = tax_after_rebate + total_surcharge - marginal_relief_surcharge
    cess = tax_payable_before_cess * 0.04
    
    # --- 8. Final Tax ---
    final_tax_payable = tax_payable_before_cess + cess

    # --- 9. Display Results ---
    st.header("Tax Calculation Summary (FY 2025-26)")
    
    st.metric(
        label=f"Total Tax Payable (AY 2026-27) for {tax_regime}",
        value=f"₹ {final_tax_payable:,.2f}"
    )
    
    st.markdown("---")
    st.subheader("Detailed Breakdown")
    
    res_col1, res_col2 = st.columns(2)
    
    # Create a string for Gross Total Income breakdown
    gti_breakdown = f" (Salary: ₹{net_salary_income:,.2f} + Rent: ₹{net_house_property_income:,.2f} + Other: ₹{net_other_sources_income:,.2f})"

    
    with res_col1:
        st.markdown(f"**Total Gross Income (All Heads):** `₹ {gti_total:,.2f}`")
        st.markdown(f"  - *Net Normal Income (GTI):* `₹ {gti_normal_income:,.2f}`")
        st.caption(gti_breakdown)
        st.markdown(f"  - *Total Special Income:* `₹ {total_special_income:,.2f}`")
        st.markdown(f"**Total Deductions (80C, etc):** `- ₹ {deductions_to_apply:,.2f}`")
        st.markdown(f"**Net Taxable Income:** `= ₹ {total_taxable_income:,.2f}`")
        st.markdown("---")
        st.markdown(f"**Tax on Normal Income (Slabs):** `₹ {tax_on_normal:,.2f}`")
        st.markdown(f"**Tax on Special Incomes (Flat):** `₹ {tax_on_special_capped + tax_on_special_uncapped:,.2f}`")
        st.markdown(f"**Total Basic Tax:** `= ₹ {total_basic_tax:,.2f}`")
    
    with res_col2:
        st.markdown(f"**Rebate (Sec 87A):** `- ₹ {rebate:,.2f}`")
        st.markdown(f"**Marginal Relief (Rebate):** `- ₹ {marginal_relief_87a:,.2f}`")
        st.markdown(f"**Tax After Rebate:** `= ₹ {tax_after_rebate:,.2f}`")
        st.markdown("---")
        st.markdown(f"**Surcharge:** `+ ₹ {total_surcharge:,.2f}`")
        if total_surcharge > 0:
            st.caption(f"Based on blended rates (Normal @ {surcharge_rate_normal*100}%, Special @ {surcharge_rate_special_cap*100}%)")
        st.markdown(f"**Marginal Relief (Surcharge):** `- ₹ {marginal_relief_surcharge:,.2f}`")
        st.markdown(f"**Total Tax before Cess:** `= ₹ {tax_payable_before_cess:,.2f}`")
    
    st.markdown("---")
    st.subheader("Final Tax")
    st.markdown(
        f"**Health & Education Cess:** `+ ₹ {cess:,.2f}`"
    )
    # This addresses the user's specific request
    st.caption(f"**Note:** This 4% cess is calculated on the 'Total Tax before Cess' (₹ {tax_payable_before_cess:,.2f})")
    
    st.markdown(
        f"### **Final Tax Payable: `₹ {final_tax_payable:,.2f}`**"
    )

