from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt


class SalesPersonTarget(Document):

    def validate(self):
        self.validate_customer()
        self.validate_child_sales_persons()
        self.calculate_parent_totals()

    # =========================================================
    # VALIDATIONS
    # =========================================================

    def validate_customer(self):
        if self.customer and not frappe.db.exists("Customer", self.customer):
            frappe.throw(_("Customer {0} does not exist").format(self.customer))

    def validate_child_sales_persons(self):
        child_tables = [
            "monthly_targets",
            "quarterly_targets",
            "yearly_targets"
        ]

        for table in child_tables:
            for row in self.get(table) or []:

                sales_person = row.get("sales_person")

                if sales_person and not frappe.db.exists(
                    "Sales Person",
                    sales_person
                ):
                    frappe.throw(
                        _("Sales Person {0} does not exist in row {1} of {2}").format(
                            sales_person,
                            row.idx,
                            table
                        )
                    )

    # =========================================================
    # MONTHLY TOTAL HELPER
    # =========================================================

    def get_monthly_total(self, row):
        return (
            flt(row.get("jan_target")) +
            flt(row.get("feb_target")) +
            flt(row.get("mar_target")) +
            flt(row.get("apr_target")) +
            flt(row.get("may_target")) +
            flt(row.get("jun_target")) +
            flt(row.get("jul_target")) +
            flt(row.get("aug_target")) +
            flt(row.get("sep_target")) +
            flt(row.get("oct_target")) +
            flt(row.get("nov_target")) +
            flt(row.get("dec_target"))
        )

    # =========================================================
    # MAIN CALCULATIONS
    # =========================================================

    def calculate_parent_totals(self):

        total_target = 0.0
        total_achieved = 0.0

        # =====================================================
        # MONTHLY TARGETS
        # =====================================================

        for row in self.monthly_targets or []:

            monthly_total = self.get_monthly_total(row)

            total_target += monthly_total

            # last year achieved
            total_achieved += flt(row.get("achieved_amount"))

        # =====================================================
        # QUARTERLY TARGETS
        # =====================================================

        for row in self.quarterly_targets or []:

            total_target += flt(row.get("target_amount"))
            total_achieved += flt(row.get("achieved_amount"))

        # =====================================================
        # YEARLY TARGETS
        # =====================================================

        for row in self.yearly_targets or []:

            total_target += flt(row.get("target_amount"))
            total_achieved += flt(row.get("achieved_amount"))

        # =====================================================
        # FINAL TOTALS
        # =====================================================

        self.total_target = total_target
        self.total_achieved = total_achieved
        self.total_balance = total_target - total_achieved

        self.achievement_percent = (
            (total_achieved / total_target) * 100
            if total_target else 0
        )


# from __future__ import unicode_literals
# import frappe
# from frappe.model.document import Document
# from frappe import _
# from frappe.utils import flt


# class SalesPersonTarget(Document):
#     def validate(self):
#         self.validate_customer()
#         # self.validate_year()
#         self.validate_child_sales_persons()
#         self.calculate_parent_totals()

#     def validate_customer(self):
#         if self.customer and not frappe.db.exists("Customer", self.customer):
#             frappe.throw(_("Customer {0} does not exist").format(self.customer))

#     def validate_year(self):
#         year = self.get("year")

#         if self.period_type == "Yearly" and not year:
#             frappe.throw(_("Please select Fiscal Year"))

#     def validate_child_sales_persons(self):
#         child_tables = ["monthly_targets", "quarterly_targets", "yearly_targets"]

#         for table in child_tables:
#             for row in self.get(table) or []:
#                 if row.get("sales_person"):
#                     if not frappe.db.exists("Sales Person", row.get("sales_person")):
#                         frappe.throw(
#                             _("Sales Person {0} does not exist in row {1} of {2}").format(
#                                 row.get("sales_person"), row.idx, table
#                             )
#                         )

#     def calculate_parent_totals(self):
#         total_target = 0.0
#         total_achieved = 0.0

#         child_tables = ["monthly_targets", "quarterly_targets", "yearly_targets"]

#         for table in child_tables:
#             for row in self.get(table) or []:
#                 target_amount = flt(row.get("target_amount", 0))
#                 last_year_target = flt(row.get("last_year_target", 0))

#                 achieved_amount = flt(row.get("achieved_amount", 0))
#                 last_year_achievement = flt(row.get("last_year_achievement", 0))
#                 last_year_achivement = flt(row.get("last_year_achivement", 0))

#                 total_target += target_amount if target_amount else last_year_target
#                 total_achieved += (
#                     achieved_amount
#                     if achieved_amount
#                     else (last_year_achievement if last_year_achievement else last_year_achivement)
#                 )

#         self.total_target = total_target
#         self.total_achieved = total_achieved
#         self.total_balance = total_target - total_achieved
#         self.achievement_percent = (total_achieved / total_target * 100) if total_target else 0