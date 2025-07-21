import base64
import logging

from odoo import models
from markupsafe import Markup

_logger = logging.getLogger(__name__)


class WayBillReportMixin(models.AbstractModel):
    _name = 'report.sot_forestry.report_sot_forestry_waybill_template'
    _description = 'WayBill Report PDF'

    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': self.env['waybill.waybill'],
            'docs': self.env['waybill.waybill'].browse(docids),
            'data': data,
        }
