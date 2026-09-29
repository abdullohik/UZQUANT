from __future__ import annotations
import re

CANONICAL_CONCEPTS=("Revenue","COGS","Gross Profit","Operating Expenses","EBITDA","D&A","EBIT","Interest Expense","Pretax Income","Taxes","Net Income","Minority Interest","EPS","Cash","Receivables","Inventory","Current Assets","PP&E","Investments","Intangibles","Other Assets","Total Assets","Accounts Payable","Short-Term Debt","Long-Term Debt","Other Liabilities","Total Liabilities","Share Capital","Retained Earnings","Equity","Operating Cash Flow","CapEx","Investing Cash Flow","Financing Cash Flow","Dividends","Free Cash Flow","Loans","Deposits","Net Interest Income","Average Earning Assets","Nonperforming Loans","Loan Loss Provisions","Regulatory Capital","Risk Weighted Assets","Non-Interest Income","Premiums","Claims","Underwriting Expenses","Investment Income","Insurance Reserves","Available Solvency Capital","Required Solvency Capital")

# Shared phrase rules: English plus Russian and Uzbek labels. Specific source row codes
# are deliberately not used because their meanings differ across report templates.
RULES=(
 ("Total Assets",r"^(?:14\. )?total assets|^итого актив|^jami aktiv"),
 ("Total Liabilities",r"^(?:25\. )?total liabilities$|^итого обязательств$|^jami majburiyat"),
 ("Equity",r"^(?:30\. )?total equity$|^total own funds$|^итого.*капитал$|^jami.*kapital$"),
 ("Cash",r"^cash, total|^1\. cash and other payment|денежные средства|pul mablag"),
 ("Receivables",r"^debtors, total|^accounts receivable|дебитор|debitor"),
 ("Inventory",r"^inventor(?:y|ies), total|запас|zaxira"),
 ("Current Assets",r"total for section ii|итого.*оборотн|joriy aktiv.*jami"),
 ("PP&E",r"residual \((?:book|balance)\) value|fixed assets, net|основные средства.*остат|asosiy vosita"),
 ("Investments",r"long-term investments, total|investments, net|долгосрочные инвестиции|uzoq muddatli invest"),
 ("Intangibles",r"at residual value|intangible assets, net|нематериальн.*остат|nomoddiy aktiv"),
 ("Other Assets",r"^13\. other assets$|^other assets$|прочие активы|boshqa aktiv"),
 ("Accounts Payable",r"^accounts payable, total|кредиторская задолженность|kreditor"),
 ("Long-Term Debt",r"long-term (?:bank )?loans|долгосрочн.*кредит|uzoq muddatli kredit"),
 ("Short-Term Debt",r"short-term (?:bank )?loans|краткосрочн.*кредит|qisqa muddatli kredit"),
 ("Other Liabilities",r"^24\. other liabilities|^other liabilities|прочие обязательства|boshqa majburiyat"),
 ("Share Capital",r"authorized capital|share capital|charter capital|уставн.*капитал|ustav kapital"),
 ("Retained Earnings",r"retained earnings|нераспределенн.*прибыл|taqsimlanmagan foyda"),
 ("Revenue",r"net revenue from sales|^revenue$|выручк|sotishdan sof tushum"),
 ("COGS",r"cost of goods sold|себестоимость|sotilgan.*tannarx"),
 ("Gross Profit",r"gross profit|валовая прибыль|yalpi foyda"),
 ("Operating Expenses",r"period expenses, total|operating expenses|расходы периода|davr xarajat"),
 ("Interest Expense",r"^interest expenses$|процентные расходы|foiz xarajat"),
 ("Pretax Income",r"profit .* before income tax|прибыль.*до налог|soliq.*oldingi foyda"),
 ("Taxes",r"^income \(profit\) tax$|income tax assessment|налог на прибыль|foyda solig"),
 ("Net Income",r"net profit .* for the period|^\d+\. net profit$|чистая прибыль|sof foyda"),
 ("EPS",r"earnings per share|прибыль на акцию|aksiya.*foyda"),
 ("Operating Cash Flow",r"net cash.*operating|чист.*денеж.*операцион|operatsion.*pul"),
 ("Investing Cash Flow",r"net cash.*investing|инвестицион.*денеж|investitsion.*pul"),
 ("Financing Cash Flow",r"net cash.*financing|финансов.*денеж|moliyaviy.*pul"),
 ("CapEx",r"capital expenditures|капитальн.*затрат|kapital xarajat"),
 ("Dividends",r"^dividends$|^дивиденды$|^dividendlar$"),
 ("D&A",r"depreciation and amorti|амортизац|amortizats"),
 ("Loans",r"^loans(?: to customers)?(?:, net)?$|loans and leasing operations, net|кредит.*клиент|mijoz.*kredit"),
 ("Deposits",r"customer deposits|deposits from customers|средства клиентов|депозит.*клиент|mijoz.*depozit"),
 ("Net Interest Income",r"net interest income|чист.*процентн.*доход|sof foizli daromad"),
 ("Average Earning Assets",r"average interest.earning assets|средн.*доходн.*актив"),
 ("Nonperforming Loans",r"non.?performing loans|проблемн.*кредит|npl"),
 ("Loan Loss Provisions",r"loan loss provision|provision for possible loan and leasing losses|impairment.*loans|резерв.*кредит"),
 ("Regulatory Capital",r"regulatory capital|регулятивн.*капитал|regulyativ kapital"),
 ("Risk Weighted Assets",r"risk.weighted assets|актив.*взвешенн.*риск"),
 ("Non-Interest Income",r"^(?:f\.\s+)?total non.interest income$|^non.interest income$|непроцентн.*доход"),
 ("Premiums",r"insurance premiums|gross written premiums|страхов.*преми|sug.urta mukofot"),
 ("Claims",r"insurance claims|claims incurred|страхов.*выплат|sug.urta to.lov"),
 ("Underwriting Expenses",r"underwriting expenses|расход.*страхов.*деятель"),
 ("Investment Income",r"investment income|инвестиционн.*доход|investitsion daromad"),
 ("Insurance Reserves",r"insurance reserves|страхов.*резерв|sug.urta zaxira"),
 ("Available Solvency Capital",r"available solvency|фактическ.*марж.*платеж"),
 ("Required Solvency Capital",r"required solvency|нормативн.*марж.*платеж"),
)
def normalize_label(label:str)->str: return " ".join(label.casefold().replace("’","'").split())
def map_concept(label:str)->str|None:
    value=normalize_label(label)
    for concept,pattern in RULES:
        if re.search(pattern,value,re.I): return concept
    return None

def map_source_concept(label:str,row_code:str|None=None,statement_type:str|None=None,sector:str|None=None)->str|None:
    """Deterministic mappings for labels actually observed in approved Openinfo forms."""
    value=normalize_label(label)
    # The statutory bank form reports both pre- and post-provision subtotals.
    # The canonical NII concept is the explicit pre-provision subtotal; mapping
    # both would silently make the same document internally ambiguous.
    if "net interest income after provision" in value:
        return None
    # Form row 100 is a balance-sheet construction/capital-investment asset,
    # never period cash-flow CapEx despite the English portal translation.
    if statement_type=="BALANCE_SHEET" and row_code=="100" and "capital" in value:
        return None
    if statement_type=="BALANCE_SHEET":
        if row_code=="480" and re.search(r"(?:total|section i).*(?:410|420|430|440|450|460|470)",value): return "Equity"
        if row_code=="570" and re.search(r"section i total.*500.*510",value): return "Equity"
        if row_code in {"770","720"} and "section ii total" in value: return "Total Liabilities"
        if "current liabilities, total" in value: return "Current Liabilities"
    if statement_type=="INCOME_STATEMENT" and row_code in {"270","320"} and "net profit" in value:
        return "Net Income"
    return map_concept(label)
