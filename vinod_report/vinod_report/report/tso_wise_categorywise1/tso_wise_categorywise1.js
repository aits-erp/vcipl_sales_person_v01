// Copyright (c) 2026, Sukku and contributors
// For license information, please see license.txt

frappe.query_reports["TSO WISE CATEGORYWISE1"] = {

    // ✅ FULLY DYNAMIC — loads all main_groups from Item master on load
    onload: async function(report) {
        const result = await frappe.db.get_list("Item", {
            fields: ["custom_main_group"],
            filters: [["custom_main_group", "!=", ""]],
            group_by: "custom_main_group",
            limit: 0
        });
        const groups = [...new Set(
            result.map(r => r.custom_main_group).filter(Boolean)
        )].sort();
        report.set_filter_value("custom_main_group", groups);
    },

    filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.month_end(),
            reqd: 1
        },
        {
            fieldname: "sales_person",
            label: "TSO",
            fieldtype: "Link",
            options: "Sales Person"
        },
        {
            fieldname: "parent_sales_person",
            label: "Head Sales Person",
            fieldtype: "Link",
            options: "Sales Person"
        },
        {
            fieldname: "custom_region",
            label: "Region",
            fieldtype: "MultiSelectList",
            get_data: function(txt) {
                return frappe.db.sql_list(`
                    SELECT DISTINCT custom_region
                    FROM \`tabSales Person\`
                    WHERE custom_region IS NOT NULL
                      AND custom_region != ''
                      AND custom_region LIKE %s
                `, ["%" + txt + "%"]);
            }
        },
        {
            fieldname: "custom_head_sales_code",
            label: "Head Sales Code",
            fieldtype: "MultiSelectList",
            get_data: function(txt) {
                return frappe.db.sql_list(`
                    SELECT DISTINCT custom_head_sales_code
                    FROM \`tabSales Person\`
                    WHERE custom_head_sales_code IS NOT NULL
                      AND custom_head_sales_code != ''
                      AND custom_head_sales_code LIKE %s
                `, ["%" + txt + "%"]);
            }
        },
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "customer_group",
            label: "Customer Group",
            fieldtype: "Link",
            options: "Customer Group"
        },
        {
            // ✅ FULLY DYNAMIC — reads live from Item master
            fieldname: "custom_main_group",
            label: "Category",
            fieldtype: "MultiSelectList",
            get_data: function(txt) {
                return frappe.db.sql_list(`
                    SELECT DISTINCT custom_main_group
                    FROM \`tabItem\`
                    WHERE custom_main_group IS NOT NULL
                      AND custom_main_group != ''
                      AND custom_main_group LIKE %s
                    ORDER BY custom_main_group
                `, ["%" + txt + "%"]);
            }
        },
        {
            fieldname: "show_item_details",
            label: "Include Item Code & Item Name",
            fieldtype: "Check",
            default: 0
        }
    ],

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname && column.fieldname.includes("_achieved")) {
            const num = parseFloat(String(value).replace(/,/g, ""));
            if (num > 0) {
                value = `<span style="color:#28a745;font-weight:600;">${value}</span>`;
            } else {
                value = `<span style="color:#dc3545;">${value}</span>`;
            }
        }

        if (column.fieldname && column.fieldname.includes("_target")) {
            const num = parseFloat(String(value).replace(/,/g, ""));
            if (num > 0) {
                value = `<span style="color:#007bff;font-weight:600;">${value}</span>`;
            }
        }

        return value;
    }
};