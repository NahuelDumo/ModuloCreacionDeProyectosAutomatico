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
                # Duplicar proyecto desde el proyecto base (o obtener existente)
                project_result = self._duplicate_project_from_base(base_project, category, order_line)
                
                if project_result:
                    project, was_created = project_result if isinstance(project_result, tuple) else (project_result, True)
                    
                    if was_created:
                        # Es un proyecto nuevo, aplicar configuraciones
                        # Asignar a la etapa del mes correspondiente
                        self._assign_project_to_monthly_stage(project)

                        # Ejecutar método "Eliminar tareas con copia"
                        project.eliminar_tareas_con_copia()
                        _logger.info(f"Proyecto creado y procesado: {project.name}")
                    else:
                        # El proyecto ya existía
                        _logger.info(f"Proyecto ya existía: {project.name}. No se realizaron cambios al proyecto.")
            else:
                _logger.warning(f"No se encontró proyecto base para la categoría {category.name}")
                
        except Exception as e:
            _logger.error(f"Error al crear proyecto para categoría {category.name}: {str(e)}")

    def _duplicate_project_from_base(self, base_project, category, order_line):
        """Duplicar proyecto desde proyecto base o retornar existente"""
        if not base_project:
            _logger.warning(f"No se proporcionó proyecto base para duplicar")
            return False
            
        # Obtener el nombre del primer producto del presupuesto
        first_product_name = ""
        if self.order_line:
            first_line = self.order_line[0]
            if first_line.product_id:
                first_product_name = first_line.product_id.name
        
        # Preparar valores para el nuevo proyecto
        # Formato: "Nombre de producto - N° presupuesto"
        project_name = f"{first_product_name} - {self.name}" if first_product_name else f"{base_project.name} - {self.name}"
        
        # Verificar si ya existe un proyecto con el mismo nombre
        existing_project = self.env['project.project'].search([
            ('name', '=', project_name)
        ], limit=1)
        
        if existing_project:
            _logger.info(f"Proyecto ya existe: {project_name}. No se creará un duplicado.")
            # Mostrar mensaje en pantalla usando el bus de mensajes
            self.env.user.notify_info(f"El proyecto '{project_name}' ya existe. No se creará un duplicado.")
            return (existing_project, False)  # Retorna el proyecto existente y False (no fue creado)
        
        project_vals = {
            'name': project_name,
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'description': f"Proyecto creado automáticamente desde presupuesto {self.name} para categoría {category.name}",
            'active': True,
        }
        
        # Duplicar el proyecto base usando el método `copy()`
        new_project = base_project.copy(project_vals)
        
        # Asegurar que se cree desarchivado (active=True) en caso de que copy() lo inactive por defecto
        if new_project and not new_project.active:
            new_project.write({'active': True})
            
        # Reorganizar y mantener las tareas en sus etapas correspondientes del proyecto base,
        # desarchivarlas explícitamente (con active_test=False) y corregir parent_id
        TaskEnv = self.env['project.task'].with_context(active_test=False)
        orig_tasks = TaskEnv.search([('project_id', '=', base_project.id)])
        new_tasks = TaskEnv.search([('project_id', '=', new_project.id)])
        
        if orig_tasks and new_tasks:
            # Desarchivar todas las tareas del proyecto recién duplicado
            new_tasks.write({'active': True})
            
            task_map = {}
            if len(orig_tasks) == len(new_tasks):
                for orig_task, new_task in zip(orig_tasks, new_tasks):
                    task_map[orig_task.id] = new_task
            else:
                for new_task in new_tasks:
                    clean_name = new_task.name.replace(' (copia)', '').replace('(copia)', '').replace(' (copy)', '').replace('(copy)', '').strip()
                    orig_task = orig_tasks.filtered(lambda t: t.name == clean_name)
                    if orig_task:
                        task_map[orig_task[0].id] = new_task
                    else:
                        orig_task_partial = orig_tasks.filtered(lambda t: clean_name in t.name)
                        if orig_task_partial:
                            task_map[orig_task_partial[0].id] = new_task

            for orig_id, new_task in task_map.items():
                orig_task = TaskEnv.browse(orig_id)
                clean_name = new_task.name.replace(' (copia)', '').replace('(copia)', '').replace(' (copy)', '').replace('(copy)', '').strip()
                
                vals_to_write = {
                    'name': clean_name,
                    'active': True,
                }
                
                # Corregir parent_id para que las tareas principales no queden vinculadas a la plantilla base
                if not orig_task.parent_id:
                    vals_to_write['parent_id'] = False
                elif orig_task.parent_id.id in task_map:
                    vals_to_write['parent_id'] = task_map[orig_task.parent_id.id].id
                else:
                    vals_to_write['parent_id'] = False

                # Mantener la etapa (stage_id) original de cada tarea
                if orig_task.stage_id:
                    vals_to_write['stage_id'] = orig_task.stage_id.id

                new_task.write(vals_to_write)
        
        return (new_project, True)  # Retorna el nuevo proyecto y True (fue creado)

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
