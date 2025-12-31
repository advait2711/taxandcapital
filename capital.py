import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta

# --- CII Table (Cost Inflation Index) ---
# Using official data up to 2024-25, and projecting for 2025-26
# This is necessary for the "20% with indexation" option for property.
CII = {
    "2001-02": 100, "2002-03": 105, "2003-04": 109, "2004-05": 113,
    "2005-06": 117, "2006-07": 122, "2007-08": 129, "2008-09": 137,
    "2009-10": 148, "2010-11": 167, "2011-12": 184, "2012-13": 200,
    "2013-14": 220, "2014-15": 240, "2015-16": 254, "2016-17": 264,
    "2017-18": 272, "2018-19": 280, "2019-20": 289, "2020-21": 301,
    "2021-22": 317, "2022-23": 331, "2023-24": 348, "2024-25": 363,
    "2025-26": 380, # Assumed/Projected for sales in FY 2025-26
}
CII_YEARS = list(CII.keys())

# --- Streamlit App UI ---
st.set_page_config(layout="wide", page_title="Capital Gains Calculator")
st.title("Capital Gains Tax Calculator (FY 2025-26)")
st.info("This calculator uses the specific tax rules provided in your images for FY 2025-26.")

# --- Sidebar for Global Inputs ---
st.sidebar.header("Global Settings")
taxpayer_status = st.sidebar.radio(
    "1. Select Taxpayer Status",
    ["Individual / HUF", "Firm / LLP / Company"],
    key="status",
    help="This is crucial for Land/Building LTCG, as Individuals/HUFs get an option."
)

with st.sidebar.expander("Cost Inflation Index (CII) Table", expanded=False):
    st.dataframe(CII)

# --- Main Page for Asset Entry ---
tab1, tab2, tab3 = st.tabs([
    "📈 Listed Equity / Equity MFs", 
    "🏠 Land or Building", 
    "🏅 Other Assets (Gold, Debt MFs, etc.)"
])

# --- Tab 1: Listed Equity / Equity MF ---
with tab1:
    st.subheader("Listed Equity & Equity Mutual Funds")
    st.info("""
    **Rules (from your images):**
    * **Holding Period:** 1 Year (<= 1 year is Short-Term, > 1 year is Long-Term)
    * **STCG Tax:** **20%**
    * **LTCG Tax:** **12.5%** on gains *over* **₹1,25,000**
    """)

    with st.form("equity_form"):
        col1, col2 = st.columns(2)
        with col1:
            purchase_date_eq = st.date_input("Purchase Date", datetime.date(2019, 1, 1))
            purchase_price_eq = st.number_input("Purchase Price (Cost)", min_value=0.0, value=100000.0)
            is_grandfathered = st.checkbox("Purchased before Jan 31, 2018 (Grandfathering)")
            fmv_2018 = 0.0
            if is_grandfathered:
                fmv_2018 = st.number_input("Fair Market Value (FMV) as on Jan 31, 2018", min_value=0.0, value=120000.0)

        with col2:
            sale_date_eq = st.date_input("Date of Sale", datetime.date(2025, 6, 1))
            sale_price_eq = st.number_input("Sale Price (Full Value)", min_value=0.0, value=250000.0)

        submitted_eq = st.form_submit_button("Calculate Equity Gain", use_container_width=True)
    
    if submitted_eq:
        holding_period = sale_date_eq - purchase_date_eq
        
        st.subheader("Calculation Result (Equity)")
        if holding_period.days <= 365:
            # Short-Term Capital Gain (STCG)
            stcg = sale_price_eq - purchase_price_eq
            tax_rate = 0.20 
            final_tax = stcg * tax_rate
            
            st.metric(label=f"Holding Period: {holding_period.days} days (Short-Term)", value=f"STCG: ₹{stcg:,.2f}")
            st.metric(label=f"Tax Rate (as provided): {tax_rate*100:.0f}%", value=f"Final Tax: ₹{final_tax:,.2f}")
        
        else:
            # Long-Term Capital Gain (LTCG)
            cost_of_acquisition = purchase_price_eq
            if is_grandfathered:
                # Apply grandfathering logic
                cost_for_ltcg = min(fmv_2018, sale_price_eq)
                cost_of_acquisition = max(purchase_price_eq, cost_for_ltcg)
                st.caption(f"Grandfathering applied. Cost of acquisition is ₹{cost_of_acquisition:,.2f} (Higher of actual cost and (lower of FMV or sale price))")

            ltcg = sale_price_eq - cost_of_acquisition
            taxable_ltcg = max(0, ltcg - 125000) 
            tax_rate = 0.125 
            final_tax = taxable_ltcg * tax_rate

            st.metric(label=f"Holding Period: {holding_period.days} days (Long-Term)", value=f"LTCG: ₹{ltcg:,.2f}")
            st.metric(label=f"Taxable LTCG (after ₹1.25L exemption): ₹{taxable_ltcg:,.2f}", value=f"Final Tax: ₹{final_tax:,.2f}")
            st.caption(f"Tax Rate (as provided): {tax_rate*100:.1f}% on gains over ₹1,25,000")
            
# --- Helper function to determine Financial Year ---
def get_financial_year(input_date):
    """Calculates the Indian financial year (e.g., "2015-16") for a given date."""
    if input_date.month >= 4:
        # Apr 1st onwards
        start_year = input_date.year
        end_year = input_date.year + 1
    else:
        # Jan, Feb, March
        start_year = input_date.year - 1
        end_year = input_date.year
    return f"{start_year}-{str(end_year)[-2:]}"            

# --- Tab 2: Land or Building ---
with tab2:
    st.subheader("Land or Building")
    st.info("""
    **Rules (from your images):**
    * **Holding Period:** 2 Years (<= 2 years is Short-Term, > 2 years is Long-Term)
    * **STCG Tax:** Added to your total income and taxed at your applicable slab/flat rate.
    * **LTCG Tax (Individual/HUF):** You get two options to choose from.
    * **LTCG Tax (Firm/Company):** 12.5% without indexation.
    """)

    MIN_PURCHASE_DATE = datetime.date(1970, 1, 1) 
    BASE_CII_START_DATE = datetime.date(2001, 4, 1) 

    # --- Section 1: Purchase Details (Outside Form) ---
    st.subheader("1. Enter Purchase Details")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.number_input(
            "Purchase Price (Cost)", 
            min_value=0.0, 
            value=2000000.0,
            key="purchase_price_prop" 
        )
        
    with p_col2:
        current_purchase_date = st.date_input(
            "Purchase Date", 
            datetime.date(2015, 6, 1), 
            min_value=MIN_PURCHASE_DATE,
            max_value=datetime.date.today(),
            help="Used to determine holding period and CII.",
            key="purchase_date_widget" 
        )
        
    # Live CII display for Purchase
    if current_purchase_date < BASE_CII_START_DATE:
        display_cii_value = 100
        st.caption(f"Purchase Year CII (Base): **{display_cii_value}**")
        st.info("Purchase is before FY 2001-02. Base CII of 100 will be used.")
    else:
        purchase_year = get_financial_year(current_purchase_date)
        display_cii_value = CII.get(purchase_year, 100) 
        st.caption(f"Purchase Year CII ({purchase_year}): **{display_cii_value}**")
    
    st.divider()

    # --- Section 2: Sale Details (Outside Form) ---
    st.subheader("2. Enter Sale Details")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.number_input(
            "Sale Price (Full Value)", 
            min_value=0.0, 
            value=5000000.0,
            key="sale_price_prop" 
        )
        
    with s_col2:
        current_sale_date = st.date_input(
            "Date of Sale", 
            datetime.date(2025, 6, 1), 
            help="Used to determine holding period and CII.",
            key="sale_date_widget" 
        )

    # Live CII display for Sale
    try:
        sale_year = get_financial_year(current_sale_date)
        display_sale_cii = CII.get(sale_year)
        if display_sale_cii:
            st.caption(f"Sale Year CII ({sale_year}): **{display_sale_cii}**")
        else:
            st.warning(f"CII for {sale_year} not found. Please check your CII table.")
    except Exception:
        st.error("Could not determine Sale Year CII.")
    
    st.divider()

    # --- Section 3: Improvement & Calculation (Inside Form) ---
    st.subheader("3. Enter Improvements & Calculate")
    with st.form("property_form"):
        cost_of_improvement = st.number_input("Cost of Improvement (if any)", min_value=0.0, value=0.0)
        coi_year = "2001-02"
        if cost_of_improvement > 0:
            coi_year = st.selectbox("Year of Improvement (for CII)", options=CII_YEARS, index=CII_YEARS.index("2020-21"))

        submitted_prop = st.form_submit_button("Calculate Property Gain", use_container_width=True)
    
    if submitted_prop:
        # --- Read ALL price/date values from session_state ---
        final_purchase_price = st.session_state.purchase_price_prop
        final_purchase_date = st.session_state.purchase_date_widget
        final_sale_price = st.session_state.sale_price_prop
        final_sale_date = st.session_state.sale_date_widget
        
        # ---
        
        final_sale_year = get_financial_year(final_sale_date)

        holding_period = relativedelta(final_sale_date, final_purchase_date)
        holding_months = holding_period.years * 12 + holding_period.months
        
        st.subheader("Calculation Result (Property)")
        st.metric(label="Holding Period", value=f"{holding_period.years} years, {holding_period.months} months ({holding_months} months)")

        if holding_months <= 24:
            # Short-Term Capital Gain (STCG)
            stcg = final_sale_price - final_purchase_price - cost_of_improvement
            st.error("This is a Short-Term Capital Gain (STCG)")
            st.metric(label="Taxable STCG", value=f"₹{stcg:,.2f}")
            st.info("This gain will be added to your total income and taxed at your applicable slab/flat rate.")
        
        else:
            # Long-Term Capital Gain (LTCG)
            st.success("This is a Long-Term Capital Gain (LTCG)")
            
            # Option 1: 12.5% without indexation
            gain_no_index = final_sale_price - final_purchase_price - cost_of_improvement
            tax_no_index = gain_no_index * 0.125

            # Option 2: 20% with indexation
            try:
                if final_purchase_date < BASE_CII_START_DATE:
                    cii_purchase = 100  
                else:
                    calc_purchase_year = get_financial_year(final_purchase_date)
                    cii_purchase = CII[calc_purchase_year]
                
                # Use the calculated final_sale_year
                cii_sale = CII[final_sale_year] 
                
                indexed_cost_acq = final_purchase_price * (cii_sale / cii_purchase)
                
                indexed_cost_imp = 0.0
                if cost_of_improvement > 0:
                     cii_coi = CII.get(coi_year, cii_sale)
                     indexed_cost_imp = cost_of_improvement * (cii_sale / cii_coi)
                
                gain_with_index = final_sale_price - indexed_cost_acq - indexed_cost_imp
                tax_with_index = gain_with_index * 0.20

            except KeyError as e:
                st.error(f"Error: CII value not found for year {e}. Please update the `CII` dictionary.")
                gain_with_index = 0
                tax_with_index = 0
                indexed_cost_acq = 0
                indexed_cost_imp = 0
            except Exception as e:
                st.error(f"Error in CII calculation: {e}.")
                gain_with_index = 0
                tax_with_index = 0
                indexed_cost_acq = 0
                indexed_cost_imp = 0

            # --- Display results based on taxpayer status ---
            if taxpayer_status == "Individual / HUF":
                st.info("As an Individual/HUF, you can choose the option that results in lower tax.")
                col1_res, col2_res = st.columns(2)
                with col1_res:
                    st.subheader("Option 1: 20% (With Indexation)")
                    
                    if final_purchase_date < BASE_CII_START_DATE:
                        st.caption(f"Using Base CII (100) for pre-2001 purchase.")
                    
                    st.caption(f"Indexed Purchase Cost: ₹{indexed_cost_acq:,.2f}")
                    
                    if cost_of_improvement > 0:
                        st.caption(f"Indexed Improvement Cost: ₹{indexed_cost_imp:,.2f}")
                    st.metric(label="Taxable Gain", value=f"₹{gain_with_index:,.2f}")
                    st.metric(label="Final Tax @ 20%", value=f"₹{tax_with_index:,.2f}")
                
                with col2_res:
                    st.subheader("Option 2: 12.5% (No Indexation)")
                    st.caption("No indexation benefit is applied.")
                    if cost_of_improvement > 0:
                         st.caption(" ") 
                    st.metric(label="Taxable Gain", value=f"₹{gain_no_index:,.2f}")
                    st.metric(label="Final Tax @ 12.5%", value=f"₹{tax_no_index:,.2f}")
            
            else: # Firm / LLP / Company
                st.info("For Firms/Companies, the only option is 12.5% without indexation.")
                st.subheader("Tax @ 12.5% (No Indexation)")
                st.metric(label="Taxable Gain", value=f"₹{gain_no_index:,.2f}")
                st.metric(label="Final Tax @ 12.5%", value=f"₹{tax_no_index:,.2f}")
                
# --- Tab 3: Other Assets (Gold, Debt MF, etc.) ---
with tab3:
    st.subheader("Other Assets (Gold, Debt MFs, etc.)")
    st.info("""
    **Rules (from your images):**
    * **Holding Period:** 2 Years (<= 2 years is Short-Term, > 2 years is Long-Term)
    * **STCG Tax:** Added to your total income and taxed at your applicable slab/flat rate.
    * **LTCG Tax:** **12.5%** without indexation.
    """)

    with st.form("other_form"):
        col1, col2 = st.columns(2)
        with col1:
            purchase_date_other = st.date_input("Purchase Date", datetime.date(2021, 1, 1))
            purchase_price_other = st.number_input("Purchase Price (Cost)", min_value=0.0, value=200000.0)
        with col2:
            sale_date_other = st.date_input("Date of Sale", datetime.date(2025, 6, 1))
            sale_price_other = st.number_input("Sale Price (Full Value)", min_value=0.0, value=300000.0)

        submitted_other = st.form_submit_button("Calculate Other Gain", use_container_width=True)

    if submitted_other:
        holding_period = relativedelta(sale_date_other, purchase_date_other)
        holding_months = holding_period.years * 12 + holding_period.months

        st.subheader("Calculation Result (Other Assets)")
        st.metric(label="Holding Period", value=f"{holding_period.years} years, {holding_period.months} months ({holding_months} months)")
        
        if holding_months <= 24:
            # Short-Term Capital Gain (STCG)
            stcg = sale_price_other - purchase_price_other
            st.error("This is a Short-Term Capital Gain (STCG)")
            st.metric(label="Taxable STCG", value=f"₹{stcg:,.2f}")
            st.info("This gain will be added to your total income and taxed at your applicable slab/flat rate.")
        
        else:
            # Long-Term Capital Gain (LTCG)
            ltcg = sale_price_other - purchase_price_other
            tax_rate = 0.125 
            final_tax = ltcg * tax_rate
            
            st.success("This is a Long-Term Capital Gain (LTCG)")
            st.metric(label="Taxable Gain", value=f"₹{ltcg:,.2f}")
            st.metric(label=f"Tax Rate (as provided): {tax_rate*100:.1f}%", value=f"Final Tax: ₹{final_tax:,.2f}")

