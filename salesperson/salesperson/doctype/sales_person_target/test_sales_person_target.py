from __future__ import unicode_literals
import frappe
import unittest

class TestSalesPersonTarget(unittest.TestCase):
    
    def setUp(self):
        """Setup before each test"""
        # Create test records if needed
        pass
    
    def tearDown(self):
        """Cleanup after each test"""
        frappe.db.rollback()
    
    def test_create_target_with_months(self):
        """Test creating a sales person target with monthly entries"""
        target = frappe.get_doc({
            "doctype": "Sales Person Target",
            "monthly_targets": [
                {
                    "month": "January",
                    "target_amount": 50000,
                    "contribution_": 25
                },
                {
                    "month": "February",
                    "target_amount": 50000,
                    "contribution_": 25
                },
                {
                    "month": "March",
                    "target_amount": 50000,
                    "contribution_": 25
                },
                {
                    "month": "April",
                    "target_amount": 50000,
                    "contribution_": 25
                }
            ]
        })
        
        target.insert()
        self.assertEqual(len(target.monthly_targets), 4)
    
    def test_duplicate_month_validation(self):
        """Test that duplicate months are not allowed"""
        target = frappe.get_doc({
            "doctype": "Sales Person Target",
            "monthly_targets": [
                {
                    "month": "January",
                    "target_amount": 100000,
                    "contribution_": 50
                },
                {
                    "month": "January",  # Duplicate month
                    "target_amount": 100000,
                    "contribution_": 50
                }
            ]
        })
        
        with self.assertRaises(frappe.ValidationError):
            target.insert()
    
    def test_total_contribution_warning(self):
        """Test that warning is shown for incorrect total contribution"""
        target = frappe.get_doc({
            "doctype": "Sales Person Target",
            "monthly_targets": [
                {
                    "month": "January",
                    "target_amount": 100000,
                    "contribution_": 60
                },
                {
                    "month": "February",
                    "target_amount": 100000,
                    "contribution_": 30  # Total only 90%
                }
            ]
        })
        
        # This should save but show warning
        target.insert()
        self.assertEqual(len(target.monthly_targets), 2)

if __name__ == '__main__':
    unittest.main()