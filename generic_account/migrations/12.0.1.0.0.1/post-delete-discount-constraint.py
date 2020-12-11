import logging
_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    cr.execute("ALTER TABLE account_invoice_line DROP CONSTRAINT IF EXISTS account_invoice_line_discount_value_limit")