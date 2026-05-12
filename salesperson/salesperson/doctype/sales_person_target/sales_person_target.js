frappe.ui.form.on("Sales Person Target", {
    refresh(frm) {
        add_customer_fetch_button(frm);
    }
});

function add_customer_fetch_button(frm) {
    frm.remove_custom_button("Get Data From Customer");

    frm.add_custom_button("Get Data From Customer", () => {
        fetch_customer_data_into_table(frm);
    });
}

function fetch_customer_data_into_table(frm) {
    if (!frm.doc.customer) {
        frappe.msgprint({
            title: __("Customer Required"),
            message: __("Please select Customer first."),
            indicator: "orange"
        });
        return;
    }

    if (!frm.doc.period_type) {
        frappe.msgprint({
            title: __("Period Type Required"),
            message: __("Please select Period Type first."),
            indicator: "orange"
        });
        return;
    }

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Customer",
            name: frm.doc.customer
        },
        freeze: true,
        freeze_message: __("Fetching customer data..."),
        callback: function (r) {
            if (!r.message) {
                frappe.msgprint({
                    title: __("Not Found"),
                    message: __("Customer data not found."),
                    indicator: "red"
                });
                return;
            }

            const customer = r.message;
            const sales_team = customer.sales_team || [];
            const period = frm.doc.period_type;

            console.log("Customer Full Data:", customer);
            console.log("Customer Sales Team:", sales_team);

            if (!sales_team.length) {
                frappe.msgprint({
                    title: __("No Sales Team Found"),
                    message: __("Selected customer has no Sales Team rows."),
                    indicator: "orange"
                });
                return;
            }

            if (period === "Monthly") {
                fill_table(frm, "monthly_targets", customer, sales_team, "year");
            } else if (period === "Quarterly") {
                fill_table(frm, "quarterly_targets", customer, sales_team, "year");
            } else if (period === "Yearly") {
                fill_table(frm, "yearly_targets", customer, sales_team, "year_label");
            } else {
                frappe.msgprint({
                    title: __("Invalid Period Type"),
                    message: __("Please select a valid Period Type."),
                    indicator: "red"
                });
                return;
            }

            frm.dirty();

            frappe.msgprint({
                title: __("Success"),
                message: __("Customer data fetched into table."),
                indicator: "green"
            });
        }
    });
}

function fill_table(frm, table_fieldname, customer, sales_team, year_fieldname) {
    frm.clear_table(table_fieldname);

    sales_team.forEach(st => {
        let row = frm.add_child(table_fieldname);

        console.log("Source sales team row:", st);
        console.log("Target child row before mapping:", row);

        // sales team fields
        if (has_field(row, "sales_person")) {
            row.sales_person = st.sales_person || "";
        }

        if (has_field(row, "contribution_")) {
            row.contribution_ = flt(st.allocated_percentage || st.contribution || 0);
        }

        if (has_field(row, "contribution_percent")) {
            row.contribution_percent = flt(st.allocated_percentage || st.contribution || 0);
        }

        if (has_field(row, "contribution")) {
            row.contribution = flt(st.allocated_percentage || st.contribution || 0);
        }

        if (has_field(row, "allocated_percentage")) {
            row.allocated_percentage = flt(st.allocated_percentage || 0);
        }

        if (has_field(row, "commission_rate")) {
            row.commission_rate = flt(st.commission_rate || 0);
        }

        // customer parent fields
        if (has_field(row, "customer")) {
            row.customer = frm.doc.customer || "";
        }

        if (has_field(row, year_fieldname)) {
            row[year_fieldname] = frm.doc.year || "";
        }

        // territory / region / location / codes
        if (has_field(row, "territory")) {
            row.territory = customer.territory || "";
        }

        if (has_field(row, "territory_code")) {
            row.territory_code = customer.territory || "";
        }

        if (has_field(row, "region")) {
            row.region = customer.region || customer.custom_region || "";
        }

        if (has_field(row, "location")) {
            row.location = customer.customer_primary_address || customer.custom_location || "";
        }

        if (has_field(row, "head_sales_code")) {
            row.head_sales_code = customer.custom_head_sales_code || "";
        }

        if (has_field(row, "territory_name")) {
            row.territory_name = customer.custom_territory_name || customer.territory || "";
        }

        if (has_field(row, "customer_name")) {
            row.customer_name = customer.customer_name || "";
        }

        // optional defaults
        if (has_field(row, "item_category")) {
            row.item_category = row.item_category || "";
        }

        if (has_field(row, "last_year_target")) {
            row.last_year_target = row.last_year_target || 0;
        }

        if (has_field(row, "last_year_achievement")) {
            row.last_year_achievement = row.last_year_achievement || 0;
        }

        if (has_field(row, "last_year_achivement")) {
            row.last_year_achivement = row.last_year_achivement || 0;
        }

        if (has_field(row, "target_amount")) {
            row.target_amount = row.target_amount || 0;
        }

        if (has_field(row, "achieved_amount")) {
            row.achieved_amount = row.achieved_amount || 0;
        }

        console.log("Target child row after mapping:", row);
    });

    frm.refresh_field(table_fieldname);
}

function has_field(row, fieldname) {
    return !!frappe.meta.get_docfield(row.doctype, fieldname);
}