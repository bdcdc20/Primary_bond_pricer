"""Parser tests on synthetic term sheets.

The fixtures are hand-built in the two layouts seen on EDGAR. Values in the side-by-side
fixture follow the Santander SNP term sheet of 7 Jan 2025 (public FWP), so the parsed
numbers can be checked against the filing.
"""

from datetime import date

from primary_bond_pricer.data.termsheet import (
    match_field, parse_spread_bp, parse_termsheet,
)


def _table(rows):
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<html><body><table>{body}</table></body></html>"


SIDE_BY_SIDE = _table([
    ["Issuer:", "Banco Santander, S.A."],
    ["Title of Securities:", "SNP 2030 Fixed Rate Notes (Senior Non Preferred)",
     "SNP 2035 Fixed Rate Notes (Senior Non Preferred)"],
    ["Aggregate Principal Amount:", "US$1,000,000,000", "US$1,000,000,000"],
    ["Trade Date:", "January 7, 2025"],
    ["Settlement Date:", "January 17, 2025 (T+8)"],
    ["Maturity Date:", "January 17, 2030", "January 17, 2035"],
    ["Interest Rate:", "5.565% per annum", "6.033% per annum"],
    ["Benchmark Treasury:", "4.375% UST due December 31, 2029", "4.250% UST due November 15, 2034"],
    ["Benchmark Treasury Yield:", "4.465%", "4.683%"],
    ["Spread to Benchmark Treasury:", "T+110 bps", "T+135 bps"],
    ["Re-offer Yield:", "5.565%", "6.033%"],
    ["Issue Price:", "100.000%", "100.000%"],
    ["Optional Redemption:", "Not Applicable", "Not Applicable"],
    ["CUSIP:", "05964HBJ3", "05964HBK0"],
    ["ISIN:", "US05964HBJ32", "US05964HBK05"],
])

SEQUENTIAL = _table([
    ["Issuer:", "Example Bank plc"],
    ["Trade Date:", "March 3, 2025"],
    ["Title of Securities:", "6NC5 Senior Fixed-to-Fixed Reset Rate Notes"],
    ["Principal Amount:", "$1,250,000,000"],
    ["Maturity Date:", "March 10, 2031"],
    ["Interest Rate:", "5.100% per annum until the Reset Date"],
    ["Optional Redemption:", "In whole on March 10, 2030"],
    ["Benchmark Treasury:", "UST 4.000% due February 28, 2030"],
    ["Benchmark Treasury Price and Yield:", "99-30+ / 4.020%"],
    ["Spread to Benchmark Treasury:", "+108 basis points"],
    ["Re-offer Yield:", "5.100%"],
    ["CUSIP:", "123456AB7"],
    ["Title of Securities:", "11NC10 Senior Fixed-to-Fixed Reset Rate Notes"],
    ["Principal Amount:", "$750,000,000"],
    ["Maturity Date:", "March 10, 2036"],
    ["Interest Rate:", "5.600% per annum until the Reset Date"],
    ["Optional Redemption:", "In whole on March 10, 2035"],
    ["Benchmark Treasury:", "UST 4.250% due February 15, 2035"],
    ["Benchmark Treasury Price and Yield:", "99-16 / 4.330%"],
    ["Spread to Benchmark Treasury:", "+127 basis points"],
    ["Re-offer Yield:", "5.600%"],
    ["CUSIP:", "123456AC5"],
])


def test_side_by_side_two_tranches():
    recs = parse_termsheet(SIDE_BY_SIDE)
    assert len(recs) == 2
    a, b = recs
    assert a["cusip"] == "05964HBJ3" and b["cusip"] == "05964HBK0"
    assert a["spread_bp"] == 110 and b["spread_bp"] == 135
    assert a["benchmark_yield_pct"] == 4.465 and b["benchmark_yield_pct"] == 4.683
    assert a["reoffer_yield_pct"] == 5.565
    assert a["trade_date"] == date(2025, 1, 7) == b["trade_date"]
    assert a["maturity_date"] == date(2030, 1, 17)
    assert a["principal_usd"] == 1e9
    assert a["seniority"] == "SNP"
    assert a["call_date"] is None
    assert a["issuer"] == "Banco Santander, S.A."
    # term-sheet identity: reoffer = benchmark + spread
    assert abs(a["benchmark_yield_pct"] + a["spread_bp"] / 100 - a["reoffer_yield_pct"]) < 1e-9


def test_sequential_two_tranches_shared_fields_broadcast():
    recs = parse_termsheet(SEQUENTIAL)
    assert len(recs) == 2
    a, b = recs
    assert (a["cusip"], b["cusip"]) == ("123456AB7", "123456AC5")
    assert (a["spread_bp"], b["spread_bp"]) == (108, 127)
    assert (a["benchmark_yield_pct"], b["benchmark_yield_pct"]) == (4.020, 4.330)
    assert a["trade_date"] == b["trade_date"] == date(2025, 3, 3)
    assert a["issuer"] == b["issuer"] == "Example Bank plc"
    assert a["call_date"] == date(2030, 3, 10)
    assert b["principal_usd"] == 7.5e8
    assert a["rate_type"] == "FIXED_TO_RESET"


def test_label_matching():
    assert match_field("Benchmark Treasury Price and Yield") == "benchmark_yield"
    assert match_field("Benchmark Treasury") == "benchmark"
    assert match_field("Re-offer Spread") == "spread"
    assert match_field("Price to Public") == "issue_price"
    assert match_field("Expected Ratings") == "ratings"
    assert match_field("Interest Payment Dates") is None


def test_spread_formats():
    assert parse_spread_bp("T+110 bps") == 110
    assert parse_spread_bp("+108 basis points") == 108
    assert parse_spread_bp("UST + 95 bp") == 95
    assert parse_spread_bp(None) is None
