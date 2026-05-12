from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt


class SalesPersonTarget(Document):
    def validate(self):
        self.validate_customer()
        self.validate_year()
        self.validate_child_sales_persons()
        self.calculate_parent_totals()

    def validate_customer(self):
        if self.customer and not frappe.db.exists("Customer", self.customer):
            frappe.throw(_("Customer {0} does not exist").format(self.customer))

    def validate_year(self):
        if self.period_type == "Yearly" and not self.year:
            frappe.throw(_("Please select Fiscal Year"))

    def validate_child_sales_persons(self):
        child_tables = ["monthly_targets", "quarterly_targets", "yearly_targets"]

        for table in child_tables:
            for row in self.get(table) or []:
                if row.get("sales_person"):
                    if not frappe.db.exists("Sales Person", row.get("sales_person")):
                        frappe.throw(
                            _("Sales Person {0} does not exist in row {1} of {2}").format(
                                row.get("sales_person"), row.idx, table
                            )
                        )

    def calculate_parent_totals(self):
        total_target = 0.0
        total_achieved = 0.0

        child_tables = ["monthly_targets", "quarterly_targets", "yearly_targets"]

        for table in child_tables:
            for row in self.get(table) or []:
                target_amount = flt(row.get("target_amount", 0))
                last_year_target = flt(row.get("last_year_target", 0))

                achieved_amount = flt(row.get("achieved_amount", 0))
                last_year_achievement = flt(row.get("last_year_achievement", 0))
                last_year_achivement = flt(row.get("last_year_achivement", 0))

                total_target += target_amount if target_amount else last_year_target
                total_achieved += (
                    achieved_amount
                    if achieved_amount
                    else (last_year_achievement if last_year_achievement else last_year_achivement)
                )

        self.total_target = total_target
        self.total_achieved = total_achieved
        self.total_balance = total_target - total_achieved
        self.achievement_percent = (total_achieved / total_target * 100) if total_target else 0