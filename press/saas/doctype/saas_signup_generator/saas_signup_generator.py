# Copyright (c) 2022, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.website.website_generator import WebsiteGenerator


class SaasSignupGenerator(WebsiteGenerator):
	website = frappe._dict(
		template="templates/saas/signup.html",
		condition_field="publish",
		page_title_field="app_title",
	)

	def get_context(self, context):
		context.parents = [{"name": "Marketplace App"}]

	def validate(self):
		if not self.custom_route:
			self.route = f"{self.app.replace('_', '')}/signup"
