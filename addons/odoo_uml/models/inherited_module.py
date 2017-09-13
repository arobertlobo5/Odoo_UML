
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import logging
from base64 import b64encode
from os import path, unlink
from subprocess import Popen
from tempfile import NamedTemporaryFile

from odoo import models, fields, api, _

try:
    from odoo.addons.odoo_uml.utils.plant_uml import PlantUMLClassDiagram, bold, italic
except ImportError:
    from ..utils.plant_uml import PlantUMLClassDiagram, bold, italic

try:
    from odoo.addons.odoo_uml.utils.odoo_uml import PackageDiagram, InvPackageDiagram, ClassDiagram
except ImportError:
    from ..utils.odoo_uml import PackageDiagram, InvPackageDiagram, ClassDiagram

_logger = logging.getLogger(__name__)


def produce_package_name(module, **kwargs):
    tags = []
    if module.auto_install:
        tags.append('auto-install')

    if kwargs.get('show_package_status', True):
        tags.append('state={0}'.format(module.state))

    if kwargs.get('show_descriptive_name', False):
        tags.insert(0, 'name=%s' % module.name)
        return u'{0}\\n{{{1}}}'.format(module.short_desc, ', '.join(tags))

    if tags:
        return u'{0}\\n{{{1}}}'.format(module.name, ', '.join(tags))

    return module.name


def produce_package_stereotype(module, **kwargs):
    if module.application:
        return 'application'
    else:
        return 'module'


def produce_package_color(module, **kwargs):
    if module.application:
        return kwargs.get('color_application_package', '#Silver')
    else:
        return kwargs.get('color_module_package', '#White')

PIPE = -1
PLANT_UML_PATH = path.realpath(
    path.join(path.dirname(__file__), '..', 'bin', 'plantuml.jar')
)


def execute_cmd(*args):
    _logger.info('Run external command: %s.', ' '.join(args))
    process = Popen(args, stdout=PIPE, stderr=PIPE)
    std_out = str()
    while process.poll() is None:
        std_out += process.stdout.readline()
    return std_out


def produce_diagram_image(puml):
    f_out_puml = NamedTemporaryFile(mode='w', delete=False)
    f_out_puml.write(puml.encode('utf-8'))
    f_out_puml.close()

    log = execute_cmd(
        'java', '-jar', PLANT_UML_PATH, '-tpng',
        f_out_puml.name, '-o', '"%s"' % path.dirname(f_out_puml.name)
    )

    f_out_diagram = open(name="%s.png" % f_out_puml.name, mode='rb')
    image = b64encode(f_out_diagram.read())
    f_out_diagram.close()

    unlink(f_out_puml.name)
    unlink(f_out_diagram.name)

    return image, log


def plant_uml_wrapper(module):
    # Dependency diagram
    _logger.info(_('Producing Dependency Diagram Image'))
    module.puml_dependency_diagram_png, log = produce_diagram_image(module.puml_dependency_diagram)
    logs = log

    # Inverse dependency diagram
    _logger.info(_('Producing Inverse Dependency Diagram Image'))
    module.puml_inv_dependency_diagram_png, log = produce_diagram_image(module.puml_inv_dependency_diagram)
    log += '\n%s' % log

    # Class diagram
    _logger.info(_('Producing Class Diagram Image'))
    module.puml_class_diagram_png, log = produce_diagram_image(module.puml_class_diagram)
    log += '\n%s' % log

    return logs


# ************************************************************************************************************
# Diagram Generators:
#   1. - Dependency Diagram for a Module
#   2. - Inverse Dependency Diagram
# ************************************************************************************************************
def generate_dependency_diagram(module, **kwargs):
    marks = []
    diagram = PlantUMLClassDiagram(
        title=_('Module Dependency Diagram'),
        header=_('\n\n| **Module**: | {0} |\n| **Description**: | {1} |\n| **Author**: | {2} |\n').format(
            module.name,
            module.summary,
            module.author
        ),
        footer=_(
            '\n\n\n'
            ' \t\t//     Powered by **Odoo UML** with **PlantUML** technology// .'
            ' //Author//: Armando Robert Lobo <mailto:arobertlobo5@gmail.com> '
        )
    )
    diagram.begin_uml()
    marks.append(module.name)
    diagram.begin_package(
        produce_package_name(module, **kwargs),
        stereotype=produce_package_stereotype(module, **kwargs),
        color='#Yellow',
        alias=module.name
    )
    if kwargs.get('show_main_description', False):
        diagram.add_floating_note(
            u'<b>Summary</b>: {0}\\n<b>Author</b>: {1}'.format(
                module.summary,
                module.author
            ),
            u'note_{0}'.format(module.name)
        )
    diagram.end_package()

    def generate_dependency(dependency):
        if dependency.name not in marks:
            marks.append(dependency.name)
            diagram.begin_package(
                produce_package_name(dependency, **kwargs),
                stereotype=produce_package_stereotype(dependency, **kwargs),
                alias=dependency.name,
                color=produce_package_color(dependency, **kwargs)
            )
            if kwargs.get('show_main_description', False):
                diagram.add_floating_note(
                    u'<b>Summary</b>: {0}\\n<b>Author</b>: {1}'.format(
                        dependency.summary,
                        dependency.author
                    ),
                    u'note_{0}'.format(dependency.name)
                )
            diagram.end_package()

            for sub in dependency.dependencies_id:
                generate_dependency(sub.depend_id)
                diagram.add_dependency(alias1=dependency.name, alias2=sub.depend_id.name)

    for dependency in module.dependencies_id:
        generate_dependency(dependency.depend_id)
        diagram.add_dependency(alias1=module.name, alias2=dependency.depend_id.name)

    diagram.end_uml()
    return diagram.output()


def generate_inv_dependency_diagram(module, **kwargs):
    marks = []
    diagram = PlantUMLClassDiagram(
        title=_('Module Inverse Dependency Diagram'),
        header=_('\n\n| **Module**: | {0} |\n| **Description**: | {1} |\n| **Author**: | {2} |\n').format(
            module.name,
            module.summary,
            module.author
        ),
        footer=_(
            '\n\n\n'
            ' \t\t//     Powered by **Odoo UML** with **PlantUML** technology// .'
            ' //Author//: Armando Robert Lobo <mailto:arobertlobo5@gmail.com> '
        )
    )
    diagram.begin_uml()
    marks.append(module.name)
    diagram.begin_package(
        produce_package_name(module, **kwargs),
        stereotype=produce_package_stereotype(module, **kwargs),
        color='#Yellow',
        alias=module.name
    )
    if kwargs.get('show_main_description', False):
        diagram.add_floating_note(
            u'<b>Summary</b>: {0}\\n<b>Author</b>: {1}'.format(
                module.summary,
                module.author
            ),
            u'note_{0}'.format(module.name)
        )
    diagram.end_package()

    env = kwargs.get('env')

    def generate_dependency(depends):
        if depends.name not in marks:
            marks.append(depends.name)

            diagram.begin_package(
                produce_package_name(depends, **kwargs),
                stereotype=produce_package_stereotype(depends, **kwargs),
                alias=depends.name,
                color=produce_package_color(depends, **kwargs)
            )
            if kwargs.get('show_main_description', False):
                diagram.add_floating_note(
                    u'<b>Summary</b>: {0}\\n<b>Author</b>: {1}'.format(
                        depends.summary,
                        depends.author
                    ),
                    u'note_{0}'.format(depends.name)
                )
            diagram.end_package()

            depends_ids = env['ir.module.module'].sudo().search([('dependencies_id.name', '=', depends.name)])
            for sub in depends_ids:
                generate_dependency(sub)
                diagram.add_dependency(alias1=sub.name, alias2=depends.name)

    depends_ids = env['ir.module.module'].sudo().search([('dependencies_id.name', '=', module.name)])
    for depends in depends_ids:
        generate_dependency(depends)
        diagram.add_dependency(alias1=depends.name, alias2=module.name)

    diagram.end_uml()
    return diagram.output()


def search_models(env, module):
    models = env['ir.model'].sudo().search([])
    found = []
    for model in models:
        if module.name in model.modules.split(', '):
            found.append(model)
    return found


def produce_alias(string):
    return string.replace(' ', '_').replace('.', '_').lower()


def produce_class_name(model, **kwargs):
    name_format = '{0}'
    if not isinstance(model, (str, unicode)):
        obj_model, model = model, model.model

    # Abstract class with name in italic
    if kwargs.get('stereotype', None) in ['abstract']:
        name_format = italic(name_format)

    name = name_format.format(
        ''.join([sub.capitalize() for sub in model.replace('_', '.').split('.')])
    )

    # Show as tag the original name of model if not "show_model_onfig_options".
    if kwargs.get('show_original_model_name', False):
        name += '\\n{{{0}}}'.format(model)

    # If from dependency module add module name
    if kwargs.get('from_external_module', None) is not None:
        name += '\\n{{\\\\(**from {0}**)\\\\}}'.format(kwargs.get('from_external_module').name)

    return name


def produce_module_models_hierarchy(env, module):
    module_models = {}
    mark = []
    index = []

    stack1, stack2 = [module], []
    while stack1:
        mod = stack1.pop()
        mark.append(mod.name)
        index.append(mod)
        module_models[mod.name] = search_models(env, mod)
        for dependency in module.dependencies_id:
            dep = dependency.depend_id
            if dep.name not in mark:
                stack2.append(dep)
        if not stack1:
            stack1, stack2 = stack2, []

    return index, module_models


def resolve_module_for_model(model_name, index, module_models):
    for module in index:
        if model_name in [mod.model for mod in module_models[module]]:
            return module


def produce_class_def_from_model(module, model, **kwargs):
    model_alias = produce_alias('{0}_{1}'.format(module.name, model.model))
    model_obj = kwargs.get('env').get(model.model)
    # Produce model stereotype
    class_stereotype, class_icon, icon_color = 'model', 'M', kwargs.get('color_normal_model_icon', 'Darkorange')
    if model.transient:
        class_stereotype, class_icon = 'transient', 'W'
        icon_color = kwargs.get('color_transient_model_icon', 'SteelBlue')
    if model_obj._abstract:
        class_stereotype, class_icon = 'abstract', 'A'
        icon_color = kwargs.get('color_abstract_model_icon', 'Gray')

    return dict(
        name=produce_class_name(model, **dict(
            kwargs,
            stereotype=class_stereotype,
            show_original_model_name=not kwargs.get('show_model_config_options', True),
            from_external_module=module
        )),
        alias=model_alias,
        icon=class_icon,
        icon_color=icon_color,
        stereotype=class_stereotype,
        class_color=kwargs.get('color_class', '#Yellow')
    )


def generate_class_diagram(module, **kwargs):
    mark = []
    diagram = PlantUMLClassDiagram(
        title=_('Models Class Diagram'),
        header=_('\n\n| **Module**: | {0} |\n| **Description**: | {1} |\n| **Author**: | {2} |\n').format(
            module.name,
            module.summary,
            module.author
        ),
        footer=_(
            '\n\n\n'
            ' \t\t//     Powered by **Odoo UML** with **PlantUML** technology// .'
            ' //Author//: Armando Robert Lobo <mailto:arobertlobo5@gmail.com> '
        )
    )
    diagram.begin_uml()

    env = kwargs.get('env')
    model_list = search_models(env, module)

    if module.state == 'uninstalled':
        diagram.add_floating_note(
            _('Module not installed. Please install it first.'),
            '{0}_not_installed'.format(module.name)
        )
    if not model_list and module.state == 'installed':
        diagram.add_floating_note(
            _('No models detected in module.'),
            '{0}_no_models'.format(module.name)
        )

    agregate = []               # agregates list (to append diagram)
    composite = []              # composite list (to append diagram)
    inherit_relations = []
    prototype_relations = []
    delegate_relations = []
    external_classes = []       # new externals classes to append diagram
    dep_index, module_models = produce_module_models_hierarchy(env, module)

    for model in model_list:
        model_alias = produce_alias('{0}_{1}'.format(module.name, model.model))
        if model_alias in mark:
            continue
        mark.append(model_alias)
        model_obj = kwargs.get('env').get(model.model)
        # Produce model stereotype
        class_stereotype, class_icon, icon_color = 'model', 'M', kwargs.get('color_normal_model_icon', 'Darkorange')
        if model.transient:
            class_stereotype, class_icon = 'transient', 'W'
            icon_color = kwargs.get('color_transient_model_icon', 'SteelBlue')
        if model_obj._abstract:
            class_stereotype, class_icon = 'abstract', 'A'
            icon_color = kwargs.get('color_abstract_model_icon', 'Gray')

        diagram.begin_class(
            produce_class_name(model, **dict(
                kwargs,
                stereotype=class_stereotype,
                show_original_model_name=not kwargs.get('show_model_config_options', True)
            )),
            alias=model_alias,
            icon=class_icon,
            icon_color=icon_color,
            stereotype=class_stereotype,
            class_color='#Yellow'
        )

        # Show model features options
        if kwargs.get('show_model_config_options', True):
            if model_obj._inherit is not None:
                if isinstance(model_obj._inherit, basestring):
                    diagram.add_attribute('_inherit = \'{0}\''.format(model_obj._inherit))
                    if model.model != model_obj._inherit:
                        diagram.add_attribute('_name = \'{0}\''.format(model.model))
                if isinstance(model_obj._inherit, list):
                    if model.model != model_obj._inherit[0]:
                            diagram.add_attribute('_name = \'{0}\''.format(model.model))
                    if len(model_obj._inherit) > 1:
                        diagram.add_attribute('_inherit = [{0}]'.format(
                            ', '.join(['\'{0}\''.format(inherit) for inherit in model_obj._inherit])
                        ))
                    else:
                        diagram.add_attribute('_inherit = \'{0}\''.format(model_obj._inherit[0]))
            else:
                diagram.add_attribute('_name = \'{0}\''.format(model.model))

            if model_obj._inherits:
                pass

            if model_obj._table is not None and model_obj._table != model.model.replace('.', '_'):
                diagram.add_attribute('_table = \'{0}\''.format(model_obj._table))

            if model_obj._date_name != 'date':
                diagram.add_attribute('_date_name = \'{0}\''.format(model_obj._date_name))
            if model_obj._fold_name != 'fold':
                diagram.add_attribute('_fold_name = \'{0}\''.format(model_obj._fold_name))
            if model_obj._rec_name is not None and model_obj._rec_name != 'name':
                diagram.add_attribute('_rec_name = \'{0}\''.format(model_obj._rec_name))
            if model_obj._order != 'id':
                diagram.add_attribute('_order = \'{0}\''.format(model_obj._order))
            # MPTT
            if model_obj._parent_name != 'parent_id':
                diagram.add_attribute('_parent_name = \'{0}\''.format(model_obj._parent_name))
            if model_obj._parent_store:
                diagram.add_attribute('_parent_store = True')
            if model_obj._parent_order:
                diagram.add_attribute('_parent_order = True')

            diagram.add_section('==')

        inherited_attr = 0
        for attr in model.field_id:
            # Exclude __las_update (concurrency check field)
            if attr.name in ['__last_update', 'display_name']:
                continue

            # Exclude loggin attributes
            if not kwargs.get('show_log_attributes', False):
                if attr.name in ['create_date', 'write_date', 'create_uid', 'write_uid']:
                    continue

            # If feature "show_only_own_attrs" disabled all fields are included.
            if module.name not in attr.modules.split(', ') and kwargs.get('show_only_own_attrs', True):
                inherited_attr += 1
                continue

            tags = []
            attr_type = bold(attr.ttype.capitalize())

            def produce_association(attr):
                # Resolve module of model relation, if not include in diagram then create one.
                from_module = resolve_module_for_model(attr.relation, dep_index, module_models)
                alias2 = produce_alias('{0}_{1}'.format(from_module, attr.relation))
                if alias2 not in mark:
                    mark.append(alias2)
                    external_classes.append()

                relation = {
                    'alias1': model_alias,
                    'alias2': alias2,
                    'card1': '*',
                    'card2': '{0} 1'.format(attr.name)
                }
                if attr.on_delete in ['cascade', 'restrict']:
                    if attr.on_delete == 'restrict':
                        relation['name'] = '<<restrict>>'
                    composite.append(relation)
                else:
                    agregate.append(relation)

            if attr.ttype in ['many2one']:
                attr_type = '{0}'.format(bold(produce_class_name(attr.relation)))

            if attr.ttype in ['one2many', 'many2many']:
                attr_type = '{0}[]'.format(bold(produce_class_name(attr.relation)))
                if attr.ttype == 'many2many':
                    tags.append(italic('many2many'))

            attr_def = {
                'visibility': '+',
                'name': attr.name,
                'attr_type':  attr_type
            }

            # Attribute critical features, always show.
            if attr.required:
                tags.append(italic('required'))
            if attr.readonly:
                tags.append(italic('readonly'))

            # If feature "show_attribute_features" enabled then include tags.
            if kwargs.get('show_attribute_features', True):
                if attr.related:
                    tags.append('//related//=\'{0}\''.format(attr.related))
                else:
                    if not attr.store:
                        tags.append(italic('nostore'))
                    if not attr.copy:
                        tags.append(italic('nocopy'))
                if attr.index:
                    tags.append(italic('index'))
                if attr.translate:
                    tags.append(italic('translate'))
                if attr.ttype in ['char', 'reference'] and attr.size:
                    tags.append('//size//={0}'.format(attr.size))
                if attr.ttype in ['many2one', 'one2many', 'many2many'] and attr.domain != '[]':
                    tags.append(italic('domain'))

            if tags:
                attr_def['tags'] = ', '.join(tags)

            diagram.add_attribute(**attr_def)

        if inherited_attr > 0:
            diagram.add_attribute('//...and {0} others inherited attr.//'.format(inherited_attr))
        diagram.end_class()

    for relation in composite:
        diagram.add_composition(**relation)

    for relation in agregate:
        diagram.add_aggregation(**relation)

    return diagram.end_uml().output()


class Module(models.Model):
    _inherit = 'ir.module.module'

    # *************************************************************************
    # Dependency Diagrams
    # *************************************************************************

    # Direct Dependency
    puml_dependency_diagram = fields.Text(
        u'Dependency diagram',
        compute='_compute_diagrams'
    )

    puml_dependency_diagram_png = fields.Binary(
        string=u'Dependency Diagram Image',
        help='Dependency diagram as encode base64 PNG image.',
        compute='_compute_diagrams'
    )

    # Inverse Dependency
    puml_inv_dependency_diagram = fields.Text(
        u'Inverse Dependency diagram',
        compute='_compute_diagrams'
    )

    puml_inv_dependency_diagram_png = fields.Binary(
        string=u'Inverse Dependency Diagram Image',
        help='Dependency diagram as encode base64 PNG image.',
        compute='_compute_diagrams'
    )

    # *************************************************************************
    # Class Diagrams
    # *************************************************************************

    # Class Diagram
    puml_class_diagram = fields.Text(
        u'Class diagram',
        compute='_compute_diagrams'
    )

    puml_class_diagram_png = fields.Binary(
        string=u'Class Diagram Image',
        help='Class diagram as encode base64 PNG image.',
        compute='_compute_diagrams'
    )

    puml_diagram_log = fields.Text(
        u'Dependency diagram log',
        compute='_compute_diagrams'
    )

    puml_package_human_name = fields.Boolean(
        string=u'More descriptive name',
        help='Enable show more descriptive name of the module.',
        default=False
    )

    puml_internal_struct = fields.Boolean(
        string=u'Show internal structure',
        help='Enable show internal estructure of the module.',
        default=False
    )

    @api.depends(
        'puml_internal_struct',
        'puml_package_human_name',
        'name',
        'dependencies_id',
        'dependencies_id.depend_id',
        'dependencies_id.depend_id.name'
    )
    def _compute_diagrams(self):
        footer = _(
            '\n\n\n'
            ' \t\t//     Powered by **Odoo UML** with **PlantUML** technology// .'
            ' //Author//: Armando Robert Lobo <mailto:arobertlobo5@gmail.com> '
        )
        for module in self:
            header = _('\n\n| **Module**: | {0} |\n| **Description**: | {1} |\n| **Author**: | {2} |\n').format(
                module.name,
                module.summary,
                module.author
            )
            kwargs = {
                'show_internal': module.puml_internal_struct,
                'show_descriptive_name': module.puml_package_human_name,
                'env': self.env
            }
            diagram = PackageDiagram(
                self,
                title=_('Module Dependency Diagram'),
                header=header,
                footer=footer,
                **kwargs
            )
            module.puml_dependency_diagram_png = diagram.to_png_base64()

            diagram = InvPackageDiagram(
                self,
                title=_('Module Inverse Dependency Diagram'),
                header=header,
                footer=footer,
                **kwargs
            )
            module.puml_inv_dependency_diagram_png = diagram.to_png_base64()
            
            diagram = ClassDiagram(
                self,
                title=_('Models Class Diagram'),
                header=header,
                footer=footer,
                **kwargs
            )
            module.puml_class_diagram_png = diagram.to_png_base64()
