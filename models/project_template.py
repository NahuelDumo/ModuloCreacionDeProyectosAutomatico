from odoo import models, fields, api


class ProjectTemplate(models.Model):
    _name = 'project.template'
    _description = 'Plantillas de Proyecto para Creación Automática'
    _order = 'name'

    name = fields.Char(
        string='Nombre de Plantilla',
        required=True,
        help='Nombre descriptivo de la plantilla'
    )
    
    product_category_id = fields.Many2one(
        'product.category',
        string='Categoría de Producto',
        help='Categoría de producto asociada a esta plantilla'
    )
    
    base_project_id = fields.Many2one(
        'project.project',
        string='Proyecto Base',
        required=True,
        help='Proyecto que se utilizará como plantilla para duplicar'
    )
    
    is_active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está activo, se utilizará para crear proyectos automáticamente'
    )
    
    is_default = fields.Boolean(
        string='Plantilla por Defecto',
        default=False,
        help='Se utilizará cuando no haya plantilla específica para una categoría'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción de la plantilla y su uso'
    )
    
    @api.constrains('is_default')
    def _check_single_default(self):
        """Asegurar que solo haya una plantilla por defecto activa"""
        if self.is_default and self.is_active:
            other_defaults = self.search([
                ('is_default', '=', True),
                ('is_active', '=', True),
                ('id', '!=', self.id)
            ])
            if other_defaults:
                raise models.ValidationError(
                    'Solo puede haber una plantilla por defecto activa a la vez.'
                )
    
    @api.model
    def get_template_for_category(self, category_id):
        """Obtener plantilla para una categoría específica"""
        template = self.search([
            ('product_category_id', '=', category_id),
            ('is_active', '=', True)
        ], limit=1)
        
        if not template:
            # Buscar plantilla por defecto
            template = self.search([
                ('is_default', '=', True),
                ('is_active', '=', True)
            ], limit=1)
        
        return template
