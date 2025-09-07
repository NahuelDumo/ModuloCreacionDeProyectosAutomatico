from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def copy_project_with_stages(self, default=None):
        """
        Método personalizado para duplicar proyecto manteniendo la estructura de etapas
        """
        if default is None:
            default = {}

        # Duplicar el proyecto usando el método estándar
        new_project = super(ProjectProject, self).copy(default)
        
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
