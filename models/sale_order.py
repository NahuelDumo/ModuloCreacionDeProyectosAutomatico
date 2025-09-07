from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import datetime
import locale

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """
        Override del método action_confirm.
        La lógica de creación de proyectos se ha movido al asistente de facturación.
        """
        result = super(SaleOrder, self).action_confirm()
        return result

    def _create_automatic_projects(self):
        """Crear proyectos automáticamente basados en categorías de productos"""
        categories_processed = set()
        
        for line in self.order_line:
            if line.product_id and line.product_id.categ_id:
                category = line.product_id.categ_id
                
                # Evitar duplicar proyectos para la misma categoría
                if category.id not in categories_processed:
                    self._create_project_for_category(category, line)
                    categories_processed.add(category.id)

    def _create_project_for_category(self, category, order_line):
        """Crear proyecto para una categoría específica"""
        try:
            # Verificar si la categoría tiene configurado crear proyecto automáticamente
            if not category.auto_create_project:
                _logger.info(f"Categoría {category.name} no tiene habilitada la creación automática de proyectos")
                return
            
            base_project = None
            
            # Primero verificar si la categoría tiene un proyecto base directo
            if category.base_project_id:
                base_project = category.base_project_id
                _logger.info(f"Usando proyecto base directo de categoría: {base_project.name}")
            else:
                # Buscar plantilla base para esta categoría
                template = self.env['project.template'].search([
                    ('product_category_id', '=', category.id),
                    ('is_active', '=', True)
                ], limit=1)
                
                if not template:
                    # Si no hay plantilla específica, buscar plantilla por defecto
                    template = self.env['project.template'].search([
                        ('is_default', '=', True),
                        ('is_active', '=', True)
                    ], limit=1)
                
                if template and template.base_project_id:
                    base_project = template.base_project_id
                    _logger.info(f"Usando proyecto base desde plantilla: {base_project.name}")
            
            if base_project:
                # Duplicar proyecto desde el proyecto base
                new_project = self._duplicate_project_from_base(base_project, category, order_line)
                
                # Asignar a la etapa del mes correspondiente
                if new_project:
                    self._assign_project_to_monthly_stage(new_project)

                # Ejecutar método "Eliminar tareas con copia"
                if new_project:
                    new_project.eliminar_tareas_con_copia()
                    _logger.info(f"Proyecto creado y procesado: {new_project.name}")
            else:
                _logger.warning(f"No se encontró proyecto base para la categoría {category.name}")
                
        except Exception as e:
            _logger.error(f"Error al crear proyecto para categoría {category.name}: {str(e)}")

    def _duplicate_project_from_base(self, base_project, category, order_line):
        """Duplicar proyecto desde proyecto base"""
        if not base_project:
            _logger.warning(f"No se proporcionó proyecto base para duplicar")
            return False
            
        # Preparar valores para el nuevo proyecto
        project_vals = {
            'name': f"{base_project.name} - {self.name} - {category.name}",
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'description': f"Proyecto creado automáticamente desde presupuesto {self.name} para categoría {category.name}",
        }
        
        # Duplicar el proyecto base usando el método `copy()` sobrescrito
        new_project = base_project.copy(project_vals)
        
        return new_project

    def _assign_project_to_monthly_stage(self, project):
        """
        Asigna un proyecto a la etapa correspondiente al mes actual.
        Si la etapa no existe, la crea.
        """
        try:
            # Intentar configurar el locale a español para obtener el nombre del mes
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
                month_name = datetime.date.today().strftime('%B').capitalize()
            except locale.Error:
                # Fallback si el locale 'es_ES' no está disponible
                months_es = {
                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                }
                month_name = months_es[datetime.date.today().month]

            Stage = self.env['project.project.stage']
            # Buscar la etapa del mes actual
            stage = Stage.search([('name', 'ilike', month_name)], limit=1)

            if not stage:
                # Si no existe, crearla
                stage = Stage.create({'name': month_name})
                _logger.info(f"Etapa '{month_name}' creada.")

            # Asignar el proyecto a la etapa
            project.stage_id = stage.id
            _logger.info(f"Proyecto '{project.name}' asignado a la etapa '{month_name}'.")
            
        except Exception as e:
            _logger.error(f"Error al asignar proyecto a etapa mensual: {str(e)}")
