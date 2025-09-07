# Módulo de Creación Automática de Proyectos

## Descripción
Este módulo automatiza el proceso de creación de proyectos cuando se aprueban presupuestos en Odoo 16.

## Funcionalidades

### 1. Creación Automática de Factura
- Al aprobar un presupuesto (action_confirm), se crea automáticamente la factura correspondiente
- Utiliza los métodos estándar de Odoo para garantizar la integridad de los datos

### 2. Creación Automática de Proyectos
- Se crean proyectos automáticamente basados en la categoría de los productos del presupuesto
- Cada categoría de producto puede tener una plantilla de proyecto asociada
- Si no hay plantilla específica, se utiliza la plantilla por defecto

### 3. Sistema de Plantillas
- **Plantillas de Proyecto**: Definen qué proyecto base se duplicará para cada categoría
- **Plantilla por Defecto**: Se utiliza cuando no hay plantilla específica para una categoría
- **Duplicación Exacta**: El proyecto se duplica exactamente como está en la plantilla

### 4. Limpieza Automática de Tareas
- Después de duplicar el proyecto, se ejecuta automáticamente el método "Eliminar tareas con copia"
- Elimina todas las tareas que contengan la palabra "copia" en el nombre

## Configuración

### 1. Configurar Plantillas de Proyecto
1. Ir a **Proyecto > Configuración > Plantillas de Proyecto**
2. Crear una nueva plantilla
3. Asignar una categoría de producto (opcional)
4. Seleccionar el proyecto base que se duplicará
5. Marcar como "Plantilla por Defecto" si es necesario

### 2. Configurar Categorías de Producto
1. Ir a **Inventario > Configuración > Categorías de Producto**
2. Editar una categoría existente
3. En la pestaña "Configuración de Proyectos":
   - Marcar "Crear Proyecto Automáticamente"
   - Ver las plantillas asociadas

## Flujo de Trabajo

```
Presupuesto Aprobado
        ↓
Creación Automática de Factura
        ↓
Identificación de Categorías de Productos
        ↓
Búsqueda de Plantilla por Categoría
        ↓
Duplicación de Proyecto Base
        ↓
Ejecución de "Eliminar tareas con copia"
        ↓
Proyecto Listo para Uso
```

## Instalación

1. Copiar el módulo en el directorio de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Instalar el módulo "Creación Automática de Proyectos"
4. Configurar las plantillas de proyecto según las necesidades

## Dependencias

- `base`: Funcionalidades básicas de Odoo
- `sale`: Módulo de ventas para presupuestos
- `account`: Módulo de contabilidad para facturas
- `project`: Módulo de proyectos
- `sale_project`: Integración entre ventas y proyectos

## Notas Técnicas

- El módulo intercepta el método `action_confirm` de `sale.order`
- Utiliza logging para rastrear las operaciones realizadas
- Maneja errores de forma robusta con try/catch
- Evita duplicar proyectos para la misma categoría en un mismo presupuesto

## Personalización

El módulo puede ser fácilmente personalizado para:
- Cambiar los criterios de creación de proyectos
- Modificar el método de limpieza de tareas
- Agregar campos adicionales a las plantillas
- Implementar validaciones específicas del negocio
