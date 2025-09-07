{
    'name': 'Creación Automática de Proyectos',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Creación automática de proyectos al aprobar presupuestos y generar facturas',
    'description': """
        Módulo que automatiza el proceso de:
        1. Crear factura automáticamente al aprobar presupuesto
        2. Crear proyecto basado en la categoría del producto
        3. Duplicar plantilla base de proyecto
        4. Ejecutar método "Eliminar tareas con copia"
    """,
    'author': 'Nahuel Dumo',
    'depends': [
        'base',
        'sale',
        'account',
        'project',
        'sale_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_template_views.xml',
        'views/product_category_views.xml',
        'data/project_template_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
