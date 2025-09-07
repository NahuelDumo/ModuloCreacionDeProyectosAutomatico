from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """
        Sobrescribes el método copy para duplicar las etapas (project.task.type)
        y reasignar las tareas a las etapas correctas.
        """
        if default is None:
            default = {}

        # Forzar la duplicación de tareas si no está ya establecido
        if 'task_ids' not in default:
            default['task_ids'] = [(0, 0, task.copy_data()[0]) for task in self.task_ids]

        # Mapeo de etapas antiguas a nombres para la búsqueda posterior
        old_stages_map = {stage.id: stage.name for stage in self.type_ids}
        old_tasks_stage_map = {task.id: task.stage_id.id for task in self.task_ids}

        # 1. Duplicar el proyecto base sin las etapas para evitar conflictos
        project_without_stages = self.with_context(no_create_folder=True).copy(default={'type_ids': False})

        # 2. Duplicar las etapas manualmente
        new_stages_map = {}
        for stage in self.type_ids:
            new_stage = stage.copy({'project_ids': [project_without_stages.id]})
            new_stages_map[stage.id] = new_stage

        # 3. Reasignar las tareas a las nuevas etapas
        for task in project_without_stages.task_ids:
            # El nombre de la tarea copiada puede tener el prefijo "(copia)"
            original_task_name = task.name.replace('(copia) ', '')
            original_task = self.task_ids.filtered(lambda t: t.name == original_task_name)
            if not original_task:
                 original_task = self.task_ids.filtered(lambda t: t.name == task.name)

            if original_task:
                original_stage_id = old_tasks_stage_map.get(original_task[0].id)
                if original_stage_id and original_stage_id in new_stages_map:
                    task.stage_id = new_stages_map[original_stage_id].id

        return project_without_stages

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
