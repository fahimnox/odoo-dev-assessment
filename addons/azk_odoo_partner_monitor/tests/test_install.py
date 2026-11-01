from bs4 import BeautifulSoup

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestModuleInstalled(TransactionCase):
    """Environment smoke tests: the addon installs, its tests are discovered and
    run, and the HTML parsing library it depends on works in this runtime."""

    def test_module_is_installed(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "azk_odoo_partner_monitor")]
        )
        self.assertEqual(module.state, "installed")

    def test_beautifulsoup_parses_html(self):
        soup = BeautifulSoup('<p class="status">gold</p>', "html.parser")
        self.assertEqual(soup.find("p", class_="status").get_text(), "gold")
