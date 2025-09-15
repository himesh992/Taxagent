#!/usr/bin/env python
# coding: utf-8

# In[3]:


import streamlit as st
import pandas as pd

st.set_page_config(page_title="Income Tax Calculator FY 2024-25", layout="wide")
st.title("💰 Indian Income Tax Calculator (FY 2024–25, AY 2025–26)")

# -------------------------
# Instructions for Users
# -------------------------
st.header("ℹ️ Instructions & Tax Rules")

st.markdown("""
### Residency Status
- **Resident (R):** Taxed on **global income**.  
- **Non-Resident (NR):** Taxed only on **Indian income**.  
- **Resident but Not Ordinarily Resident (RNOR):** Taxed on **Indian income + foreign income received in India**.  

### Tax Regimes
**New Tax Regime (Default):**
- Standard deduction ₹75,000 (for salaried individuals)  
- Minimal deductions allowed  
- Section 87A rebate up to ₹25,000 if taxable income ≤ ₹7,00,000  
- Slabs (FY 2024–25):  
  - 0–3,00,000 → Nil  
  - 3,00,001–7,00,000 → 5%  
  - 7,00,001–10,00,000 → 10%  
  - 10,00,001–12,00,000 → 15%  
  - 12,00,001–15,00,000 → 20%  
  - Above 15,00,000 → 30%  

**Old Tax Regime (Optional):**
- Standard deduction ₹50,000  
- Allows deductions under 80C, 80D, HRA, home loan interest, etc.  
- Section 87A rebate up to ₹12,500 if taxable income ≤ ₹5,00,000  
- Slabs for individuals <60 years (NR taxed same as R):  
  - 0–2,50,000 → Nil  
  - 2,50,001–5,00,000 → 5%  
  - 5,00,001–10,00,000 → 20%  
  - Above 10,00,000 → 30%  

*Senior and super senior citizens have higher exemption limits.*
""")

# -------------------------
# User Info
# -------------------------
st.sidebar.header("User Information")
res_status = st.sidebar.selectbox("Residency Status", ["Resident", "Non-Resident", "Resident but Not Ordinarily Resident"])
age = st.sidebar.selectbox("Age Category", ["Below 60", "Senior (60-80)", "Super Senior (80+)"])

# -------------------------
# Input Income Sections
# -------------------------
st.header("Salary Income")
salary_monthly = st.number_input("Monthly Salary (Basic + DA) ₹", 0, step=1000)
bonus = st.number_input("Annual Bonus ₹", 0, step=1000)
salary_total = salary_monthly * 12 + bonus
st.write(f"Total Salary Income: ₹{salary_total:,}")

st.header("House Property Income")
rent_received = st.number_input("Annual Rent Received (₹)", 0, step=1000)
municipal_taxes = st.number_input("Municipal Taxes Paid (₹)", 0, step=500)
loan_interest = st.number_input("Home Loan Interest (₹)", 0, step=1000)
nav = max(0, rent_received - municipal_taxes)
house_income = nav - 0.3 * nav - loan_interest
st.write(f"Net House Property Income: ₹{house_income:,}")

st.header("Business/Professional Income")
business_income = st.number_input("Net Business/Professional Income ₹", 0, step=1000)

st.header("Capital Gains")
stcg = st.number_input("Short-Term Capital Gains (STCG, Sec 111A) ₹", 0, step=1000)
ltcg = st.number_input("Long-Term Capital Gains (LTCG, Sec 112A) ₹", 0, step=1000)
ltcg_taxable = max(0, ltcg - 100000)

st.header("Other Income & Deductions")
other_income = st.number_input("Other Income (FD, Savings Interest, Dividends) ₹", 0, step=1000)
ded_80c = st.number_input("80C Investments ₹", 0, step=1000)
ded_80d = st.number_input("80D Medical Insurance ₹", 0, step=1000)
ded_80tta = st.number_input("80TTA/TTB Savings Interest Deduction ₹", 0, step=1000)

# -------------------------
# Compute Taxable Income
# -------------------------
gross_income = salary_total + house_income + business_income + other_income

deductions_old = min(150000, ded_80c) + ded_80d + ded_80tta + 50000  # std deduction included
taxable_old = max(0, gross_income - deductions_old)
taxable_new = max(0, gross_income - 75000)  # new regime standard deduction

st.subheader("Taxable Income")
st.write(f"Old Regime Taxable Income: ₹{taxable_old:,}")
st.write(f"New Regime Taxable Income: ₹{taxable_new:,}")

# -------------------------
# Tax Calculation Functions
# -------------------------
def compute_old_tax(income, age_cat):
    tax, breakdown = 0, []
    if age_cat == "Below 60" or res_status != "Resident":
        slabs = [(250000, 0.05), (500000, 0.2), (float("inf"), 0.3)]
        base_exemption = 250000
    elif age_cat == "Senior (60-80)":
        slabs = [(200000, 0.05), (500000, 0.2), (float("inf"), 0.3)]
        base_exemption = 300000
    else:  # Super Senior
        slabs = [(500000, 0.2), (float("inf"), 0.3)]
        base_exemption = 500000

    limit = base_exemption
    for slab, rate in slabs:
        if income > limit:
            taxable = min(income - limit, slab if slab != float("inf") else income - limit)
            tax += taxable * rate
            breakdown.append((limit+1, limit+slab if slab != float("inf") else income, rate*100, taxable*rate))
            limit += slab if slab != float("inf") else income - limit

    if res_status == "Resident" and income <= 500000:  # 87A rebate
        rebate = min(12500, tax)
        tax -= rebate
        breakdown.append(("87A Rebate", rebate))
    return tax, breakdown

def compute_new_tax(income):
    tax, breakdown = 0, []
    slabs = [(300000, 0.05), (400000, 0.1), (300000, 0.15),
             (300000, 0.2), (300000, 0.3)]
    limit = 300000
    for slab, rate in slabs:
        if income > limit:
            taxable = min(income - limit, slab)
            tax += taxable * rate
            breakdown.append((limit+1, limit+slab, rate*100, taxable*rate))
            limit += slab
    if res_status == "Resident" and income <= 700000:
        rebate = min(25000, tax)
        tax -= rebate
        breakdown.append(("87A Rebate", rebate))
    return tax, breakdown

# -------------------------
# Compute Tax
# -------------------------
tax_old, breakdown_old = compute_old_tax(taxable_old, age)
tax_new, breakdown_new = compute_new_tax(taxable_new)

# Add CGT
tax_old += 0.15*stcg + 0.10*ltcg_taxable
tax_new += 0.15*stcg + 0.10*ltcg_taxable

# -------------------------
# Display Slab-wise Tax
# -------------------------
st.subheader("Old Regime Slab-wise Tax")
for row in breakdown_old:
    st.write(row)

st.subheader("New Regime Slab-wise Tax")
for row in breakdown_new:
    st.write(row)

# -------------------------
# Final Tax Comparison
# -------------------------
st.subheader("Final Tax")
st.write(f"Old Regime Tax (incl. CGT): ₹{tax_old:,}")
st.write(f"New Regime Tax (incl. CGT): ₹{tax_new:,}")

if tax_old < tax_new:
    st.success(f"✅ Old Regime is better. You save ₹{tax_new - tax_old:,}")
else:
    st.success(f"✅ New Regime is better. You save ₹{tax_old - tax_new:,}")

