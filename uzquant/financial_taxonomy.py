from __future__ import annotations
import re

CANONICAL_CONCEPTS=("Revenue","COGS","Gross Profit","Operating Expenses","EBITDA","D&A","EBIT","Interest Expense","Pretax Income","Taxes","Net Income","Minority Interest","EPS","Cash","Receivables","Inventory","Current Assets","PP&E","Investments","Intangibles","Other Assets","Total Assets","Accounts Payable","Short-Term Debt","Long-Term Debt","Other Liabilities","Total Liabilities","Share Capital","Retained Earnings","Equity","Operating Cash Flow","CapEx","Investing Cash Flow","Financing Cash Flow","Dividends","Free Cash Flow")

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
 ("Share Capital",r"authorized capital|share capital|уставн.*капитал|ustav kapital"),
 ("Retained Earnings",r"retained earnings|нераспределенн.*прибыл|taqsimlanmagan foyda"),
 ("Revenue",r"net revenue from sales|^revenue$|выручк|sotishdan sof tushum"),
 ("COGS",r"cost of goods sold|себестоимость|sotilgan.*tannarx"),
 ("Gross Profit",r"gross profit|валовая прибыль|yalpi foyda"),
 ("Operating Expenses",r"period expenses, total|operating expenses|расходы периода|davr xarajat"),
 ("Interest Expense",r"^interest expenses$|процентные расходы|foiz xarajat"),
 ("Pretax Income",r"profit .* before income tax|прибыль.*до налог|soliq.*oldingi foyda"),
 ("Taxes",r"^income \(profit\) tax$|налог на прибыль|foyda solig"),
 ("Net Income",r"net profit .* for the period|чистая прибыль|sof foyda"),
 ("EPS",r"earnings per share|прибыль на акцию|aksiya.*foyda"),
 ("Operating Cash Flow",r"net cash.*operating|чист.*денеж.*операцион|operatsion.*pul"),
 ("Investing Cash Flow",r"net cash.*investing|инвестицион.*денеж|investitsion.*pul"),
 ("Financing Cash Flow",r"net cash.*financing|финансов.*денеж|moliyaviy.*pul"),
 ("CapEx",r"capital expenditures|капитальн.*затрат|kapital xarajat"),
 ("Dividends",r"^dividends$|^дивиденды$|^dividendlar$"),
)
def normalize_label(label:str)->str: return " ".join(label.casefold().replace("’","'").split())
def map_concept(label:str)->str|None:
    value=normalize_label(label)
    for concept,pattern in RULES:
        if re.search(pattern,value,re.I): return concept
    return None
