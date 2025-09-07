from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def copy_project_with_stages(self, default=None):
        """
        Método personalizado para duplicar proyecto con etapas correctamente
        """
        if default is None:
            default = {}

        # Mapeo de etapas y tareas originales
        old_stages_map = {stage.id: stage.name for stage in self.type_ids}
        old_tasks_stage_map = {task.id: task.stage_id.id for task in self.task_ids}

        # 1. Duplicar el proyecto usando el método estándar
        new_project = super(ProjectProject, self).copy(default)

        # 2. Duplicar las etapas manualmente y crear mapeo
        new_stages_map = {}
        for stage in self.type_ids:
            new_stage = stage.copy({'project_ids': [(6, 0, [new_project.id])]})
            new_stages_map[stage.id] = new_stage

        # 3. Reasignar las tareas a las nuevas etapas
        for task in new_project.task_ids:
            # Buscar la tarea original correspondiente
            original_task_name = task.name.replace('(copia) ', '')
            original_task = self.task_ids.filtered(lambda t: t.name == original_task_name)
            if not original_task:
                original_task = self.task_ids.filtered(lambda t: t.name == task.name)

            if original_task:
                original_stage_id = old_tasks_stage_map.get(original_task[0].id)
                if original_stage_id and original_stage_id in new_stages_map:
                    task.stage_id = new_stages_map[original_stage_id].id

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
