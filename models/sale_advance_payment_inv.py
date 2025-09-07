from odoo import models
import logging
import datetime
import locale

_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        """
        Sobrescribe el método para disparar la creación de proyectos
        después de crear la factura.
        """
        _logger.info("=== INICIANDO CREACIÓN DE FACTURAS Y PROYECTOS ===")
        
        # Primero, ejecutar la lógica original para crear las facturas
        res = super(SaleAdvancePaymentInv, self).create_invoices()

        # Después, para cada pedido de venta asociado, crear los proyectos
        for order in self.sale_order_ids:
            _logger.info(f"Procesando pedido: {order.name}")
            try:
                order._create_automatic_projects()
                _logger.info(f"Proyectos creados exitosamente para pedido: {order.name}")
            except Exception as e:
                _logger.error(f"Error al crear proyectos para pedido {order.name}: {str(e)}")

        _logger.info("=== FINALIZANDO CREACIÓN DE FACTURAS Y PROYECTOS ===")
        return res
