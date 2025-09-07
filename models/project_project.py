from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def copy_project_with_stages(self, default=None):
        """
        Método personalizado para duplicar proyecto SOLO con las etapas,
        manteniendo las tareas originales sin duplicar
        """
        if default is None:
            default = {}

        # Mapeo de etapas originales por nombre
        old_stages_by_name = {stage.name: stage for stage in self.type_ids}
        
        # 1. Duplicar el proyecto con las tareas originales (sin prefijo "copia")
        new_project = super(ProjectProject, self).copy(default)

        # 2. Limpiar las etapas duplicadas automáticamente
        new_project.type_ids.unlink()

        # 3. Recrear SOLO las etapas del proyecto base (sin tareas)
        new_stages_map = {}
        for stage in self.type_ids:
            new_stage = stage.copy({
                'project_ids': [(6, 0, [new_project.id])],
                'task_ids': [(5, 0, 0)]  # No copiar tareas en las etapas
            })
            new_stages_map[stage.name] = new_stage

        # 4. Reasignar las tareas del nuevo proyecto a las etapas correctas
        for task in new_project.task_ids:
            # Buscar la tarea original correspondiente
            original_task_name = task.name.replace('(copia) ', '')
            original_task = self.task_ids.filtered(lambda t: t.name == original_task_name)
            
            if original_task and original_task.stage_id:
                stage_name = original_task.stage_id.name
                if stage_name in new_stages_map:
                    task.stage_id = new_stages_map[stage_name].id

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
