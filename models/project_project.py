from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """
        Sobrescribe el método copy para asegurar una duplicación exacta de las etapas
        y tareas del proyecto, evitando la pérdida de estructura.
        """
        if default is None:
            default = {}

        # 1. Preparar los datos del nuevo proyecto sin etapas ni tareas
        project_data = self.copy_data(default)[0]
        project_data.pop('type_ids', None)
        project_data.pop('task_ids', None)
        new_project = self.create(project_data)

        # 2. Duplicar las etapas y crear un mapa de IDs (antiguo -> nuevo)
        stage_map = {}
        for stage in self.type_ids:
            new_stage = stage.copy({'project_ids': [(6, 0, [new_project.id])]})
            stage_map[stage.id] = new_stage.id

        # 3. Duplicar las tareas y asignarlas a las nuevas etapas y proyecto
        task_map = {}
        for task in self.task_ids:
            task_data = task.copy_data()[0]
            task_data.update({
                'project_id': new_project.id,
                'stage_id': stage_map.get(task.stage_id.id),
                'name': task.name # Evitar el prefijo "(copia)"
            })
            new_task = self.env['project.task'].create(task_data)
            task_map[task.id] = new_task.id

        return new_project

    def eliminar_tareas_con_copia(self):
        """
        Método para eliminar tareas que contengan la palabra 'copia' en el nombre
        Se ejecuta automáticamente después de duplicar un proyecto desde plantilla
        """
        for project in self:
            # Buscar tareas que contengan 'copia' en el nombre (case insensitive)
            tasks_to_delete = self.env['project.task'].search([
                ('project_id', '=', project.id),
                ('name', 'ilike', '%copia%')
            ])
            
            if tasks_to_delete:
                task_names = tasks_to_delete.mapped('name')
                _logger.info(f"Eliminando {len(tasks_to_delete)} tareas con 'copia' del proyecto {project.name}: {task_names}")
                
                # Eliminar las tareas
                tasks_to_delete.unlink()
                
                _logger.info(f"Tareas eliminadas exitosamente del proyecto {project.name}")
            else:
                _logger.info(f"No se encontraron tareas con 'copia' en el proyecto {project.name}")
        
        return True

    def action_eliminar_tareas_copia(self):
        """
        Acción manual para eliminar tareas con copia
        Puede ser llamada desde la interfaz de usuario
        """
        self.eliminar_tareas_con_copia()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Tareas Eliminadas',
                'message': 'Se han eliminado las tareas que contenían "copia" en el nombre.',
                'type': 'success',
                'sticky': False,
            }
        }
