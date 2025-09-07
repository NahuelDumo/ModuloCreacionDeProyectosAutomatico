from odoo import models

import logging
_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        """
        Sobrescribe el método para disparar la creación de proyectos
        después de crear la factura.
        """
        # Primero, ejecutar la lógica original para crear las facturas
        res = super(SaleAdvancePaymentInv, self).create_invoices()

        # Después, para cada pedido de venta asociado, crear los proyectos
        for order in self.sale_order_ids:
            _logger.info(f"Disparando creación de proyecto para el pedido: {order.name}")
            order._create_automatic_projects()

        return res
