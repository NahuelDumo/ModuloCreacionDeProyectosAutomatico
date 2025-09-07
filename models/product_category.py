from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    project_template_ids = fields.One2many(
        'project.template',
        'product_category_id',
        string='Plantillas de Proyecto',
        help='Plantillas de proyecto asociadas a esta categoría'
    )
    
    project_template_count = fields.Integer(
        string='Número de Plantillas',
        compute='_compute_project_template_count'
    )
    
    auto_create_project = fields.Boolean(
        string='Crear Proyecto Automáticamente',
        default=False,
        help='Si está marcado, se creará automáticamente un proyecto cuando se facture un producto de esta categoría'
    )
    
    base_project_id = fields.Many2one(
        'project.project',
        string='Proyecto Base',
        help='Proyecto que se utilizará como plantilla para duplicar cuando se cree un proyecto automáticamente'
    )

    @api.depends('project_template_ids')
    def _compute_project_template_count(self):
        for category in self:
            category.project_template_count = len(category.project_template_ids)

    def action_view_project_templates(self):
        """Acción para ver las plantillas de proyecto de esta categoría"""
        self.ensure_one()
        return {
            'name': f'Plantillas de Proyecto - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'project.template',
            'view_mode': 'tree,form',
            'domain': [('product_category_id', '=', self.id)],
            'context': {'default_product_category_id': self.id},
        }
