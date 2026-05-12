# Copyright (c) 2026, Sukku and contributors
# For license information, please see license.txt

# import frappe


# Copyright (c) 2026, Sukku and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate
from frappe import _

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]


def execute(filters=None):
    filters = frappe._dict(filters or {})

    if filters.get("from_date") and filters.get("to_date"):
        if getdate(filters.from_date) > getdate(filters.to_date):
            frappe.throw(_("From Date must be before To Date"))

    categories = get_categories(filters)
    columns   = get_columns(categories, filters)
    data      = get_data(filters, categories)
    chart     = get_chart_data(data, categories)
    summary   = get_summary(data, categories)

    return columns, data, None, chart, summary


# ─────────────────────────────────────────────
# CATEGORIES  — fully dynamic from Item master
# ─────────────────────────────────────────────
def get_categories(filters):
    if filters.get("custom_main_group"):
        val = filters.custom_main_group
        return val if isinstance(val, list) else [val]

    conditions = ""
    values = {}

    if filters.get("from_date"):
        conditions += " AND si.posting_date >= %(from_date)s"
        values["from_date"] = filters.from_date

    if filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"
        values["to_date"] = filters.to_date

    rows = frappe.db.sql(f"""
        SELECT DISTINCT i.custom_main_group
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        INNER JOIN `tabItem` i ON i.name = sii.item_code
        WHERE si.docstatus = 1
          AND i.custom_main_group IS NOT NULL
          AND i.custom_main_group != ''
          {conditions}
        ORDER BY i.custom_main_group
    """, values)

    return [r[0] for r in rows if r[0]]


# ─────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────
def get_columns(categories, filters=None):
    columns = []

    if filters and filters.get("show_item_details"):
        columns.extend([
            {"label": _("Item Code"),  "fieldname": "item_code",  "fieldtype": "Link", "options": "Item", "width": 150},
            {"label": _("Item Name"),  "fieldname": "item_name",  "fieldtype": "Data", "width": 200},
        ])

    columns.extend([
        {"label": _("Month"),              "fieldname": "month",               "fieldtype": "Data",     "width": 100},
        {"label": _("TSO"),                "fieldname": "tso_name",            "fieldtype": "Link",     "options": "Sales Person", "width": 200},
        {"label": _("Customer Name"),      "fieldname": "customer_name",       "fieldtype": "Data",     "width": 200},
        {"label": _("Region"),             "fieldname": "custom_region",       "fieldtype": "Data",     "width": 150},
        {"label": _("Head Sales Person"),  "fieldname": "parent_sales_person", "fieldtype": "Link",     "options": "Sales Person", "width": 200},
        {"label": _("Invoice Count"),      "fieldname": "invoice_count",       "fieldtype": "Int",      "width": 120},
        {"label": _("Item Count"),         "fieldname": "item_count",          "fieldtype": "Int",      "width": 120},
        {"label": _("Total Achieved"),     "fieldname": "total_achieved",      "fieldtype": "Currency", "width": 150},
        {"label": _("Total Target"),       "fieldname": "total_target",        "fieldtype": "Currency", "width": 150},
    ])

    for cat in categories:
        safe = frappe.scrub(cat)
        columns.append({"label": _(f"{cat} (Target)"),   "fieldname": f"{safe}_target",   "fieldtype": "Currency", "width": 150})
        columns.append({"label": _(f"{cat} (Achieved)"), "fieldname": f"{safe}_achieved", "fieldtype": "Currency", "width": 150})

    return columns


# ─────────────────────────────────────────────
# TARGET CACHE  — fetch once per (tso, month, year)
# avoids N×categories DB hits
# ─────────────────────────────────────────────
_target_cache = {}

def _load_targets_for_tso(tso_name, month_num, year):
    """
    Load all main_group targets for a given TSO + month + year
    from the Monthly Target Detail child table and cache them.
    Returns a dict  { main_group: target_amount }
    """
    cache_key = (tso_name, month_num, year)
    if cache_key in _target_cache:
        return _target_cache[cache_key]

    rows = frappe.db.sql("""
        SELECT
            mtd.main_group,
            mtd.target_amount
        FROM `tabMonthly Target Detail` mtd
        INNER JOIN `tabSales Person Target` spt
            ON spt.name = mtd.parent
        WHERE spt.customer  = %(tso_name)s
          AND mtd.month     = %(month_num)s
          AND mtd.year      = %(year)s
          AND spt.docstatus = 1
    """, {
        "tso_name":  tso_name,
        "month_num": month_num,
        "year":      year
    }, as_dict=1)

    result = {r.main_group: flt(r.target_amount) for r in rows}
    _target_cache[cache_key] = result
    return result


def get_month_target_from_sales_team(tso_name, month_num, year, category):
    """Return the target amount for one TSO + month + year + category."""
    targets = _load_targets_for_tso(tso_name, month_num, year)
    return flt(targets.get(category, 0))


# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
def get_data(filters, categories):
    # reset cache for each report run
    global _target_cache
    _target_cache = {}

    conditions = ["si.docstatus = 1",
                  "i.custom_main_group IS NOT NULL",
                  "i.custom_main_group != ''"]
    values = {}

    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        values["from_date"] = filters.from_date

    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        values["to_date"] = filters.to_date

    if filters.get("sales_person"):
        conditions.append("sp.name = %(sales_person)s")
        values["sales_person"] = filters.sales_person

    if filters.get("parent_sales_person"):
        conditions.append("sp.parent_sales_person = %(parent_sales_person)s")
        values["parent_sales_person"] = filters.parent_sales_person

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.customer

    if filters.get("customer_group"):
        conditions.append("si.customer_group = %(customer_group)s")
        values["customer_group"] = filters.customer_group

    if filters.get("custom_region"):
        regions = filters.custom_region
        if isinstance(regions, str):
            regions = [x.strip() for x in regions.split(",") if x.strip()]
        conditions.append("sp.custom_region IN %(custom_region)s")
        values["custom_region"] = tuple(regions)

    if filters.get("custom_head_sales_code"):
        codes = filters.custom_head_sales_code
        if isinstance(codes, str):
            codes = [x.strip() for x in codes.split(",") if x.strip()]
        conditions.append("sp.custom_head_sales_code IN %(custom_head_sales_code)s")
        values["custom_head_sales_code"] = tuple(codes)

    if filters.get("custom_main_group"):
        cat_filter = filters.custom_main_group
        if isinstance(cat_filter, str):
            cat_filter = [x.strip() for x in cat_filter.split(",") if x.strip()]
        conditions.append("i.custom_main_group IN %(custom_main_group)s")
        values["custom_main_group"] = tuple(cat_filter)

    where_clause = " AND ".join(conditions)

    group_by = """
        YEAR(si.posting_date),
        MONTH(si.posting_date),
        sp.name,
        sp.parent_sales_person,
        sp.custom_region,
        c.customer_name,
        i.custom_main_group
    """
    if filters.get("show_item_details"):
        group_by += ", sii.item_code, i.item_name"

    query = f"""
        SELECT
            YEAR(si.posting_date)              AS year,
            MONTH(si.posting_date)             AS month_num,
            sp.name                            AS tso_name,
            sp.parent_sales_person,
            sp.custom_region,
            c.customer_name,
            i.custom_main_group                AS category,
            sii.item_code,
            i.item_name,
            SUM(sii.base_net_amount)           AS achieved,
            COUNT(DISTINCT si.name)            AS invoice_count,
            COUNT(DISTINCT sii.item_code)      AS item_count
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        INNER JOIN `tabItem` i                 ON i.name = sii.item_code
        INNER JOIN `tabSales Team` st          ON st.parent = si.name AND st.idx = 1
        INNER JOIN `tabSales Person` sp        ON sp.name = st.sales_person
        INNER JOIN `tabCustomer` c             ON c.name = si.customer
        WHERE {where_clause}
        GROUP BY {group_by}
        ORDER BY YEAR(si.posting_date), MONTH(si.posting_date), sp.name
    """

    raw = frappe.db.sql(query, values, as_dict=1)

    result = {}

    for row in raw:
        if filters.get("show_item_details"):
            key = (row.year, row.month_num, row.tso_name,
                   row.customer_name, row.parent_sales_person,
                   row.custom_region, row.item_code)
        else:
            key = (row.year, row.month_num, row.tso_name,
                   row.customer_name, row.parent_sales_person,
                   row.custom_region)

        if key not in result:
            entry = {
                "month":               f"{MONTHS[int(row.month_num)-1]}-{row.year}",
                "month_num":           row.month_num,
                "year":                row.year,
                "tso_name":            row.tso_name or "Unassigned",
                "customer_name":       row.customer_name or "",
                "parent_sales_person": row.parent_sales_person or "",
                "custom_region":       row.custom_region or "",
                "invoice_count":       0,
                "item_count":          0,
                "total_achieved":      0,
                "total_target":        0,
            }

            if filters.get("show_item_details"):
                entry["item_code"] = row.item_code
                entry["item_name"] = row.item_name

            # initialise category columns & fetch targets
            for cat in categories:
                safe = frappe.scrub(cat)
                entry[f"{safe}_achieved"] = 0

                target = get_month_target_from_sales_team(
                    row.tso_name, row.month_num, row.year, cat
                )
                entry[f"{safe}_target"]  = flt(target)
                entry["total_target"]   += flt(target)

            result[key] = entry

        # accumulate achieved
        safe = frappe.scrub(row.category)
        result[key][f"{safe}_achieved"] += flt(row.achieved)
        result[key]["total_achieved"]   += flt(row.achieved)
        result[key]["invoice_count"]    += int(row.invoice_count)
        result[key]["item_count"]       += int(row.item_count)

    return list(result.values())


# ─────────────────────────────────────────────
# CHART
# ─────────────────────────────────────────────
def get_chart_data(data, categories):
    if not data:
        return None

    month_totals = {}
    for row in data:
        m = row.get("month")
        month_totals[m] = month_totals.get(m, 0) + flt(row.get("total_achieved"))

    return {
        "data": {
            "labels": list(month_totals.keys()),
            "datasets": [{"name": "Achieved", "values": list(month_totals.values())}]
        },
        "type": "bar",
        "height": 300
    }


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
def get_summary(data, categories):
    total_achieved = total_target = total_invoice = total_item = 0

    for row in data:
        total_achieved += flt(row.get("total_achieved"))
        total_target   += flt(row.get("total_target"))
        total_invoice  += flt(row.get("invoice_count"))
        total_item     += flt(row.get("item_count"))

    return [
        {"label": _("Total Achieved"), "value": total_achieved, "indicator": "Green",  "datatype": "Currency"},
        {"label": _("Total Target"),   "value": total_target,   "indicator": "Blue",   "datatype": "Currency"},
        {"label": _("Invoice Count"),  "value": total_invoice,  "indicator": "Orange", "datatype": "Int"},
        {"label": _("Item Count"),     "value": total_item,     "indicator": "Purple", "datatype": "Int"},
    ]
cd