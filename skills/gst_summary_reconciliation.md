# Skill: GST Summary & Reconciliation (CFO Division)

## Purpose
Enables the CFO worker agent to parse monthly invoices, calculate output CGST/SGST/IGST, reconcile input tax credit (ITC), and draft a filing summary.

## Safety & Governance
- **Risk Level**: Level 1 for internal draft calculations.
- **Risk Level**: Level 3 for tax portal submission (MUST pause for owner approval).
- **Default State**: Read-only extraction.

## Step-by-Step Procedure
1. Query sales and purchase registers from the `business` schema.
2. Verify total taxable value and calculate applicable GST slabs (5%, 12%, 18%, 28%).
3. Check for mismatches between purchase register and GSTR-2B ITC reports.
4. Export the summary table into an audit draft.
5. Notify the human owner for professional sign-off.
