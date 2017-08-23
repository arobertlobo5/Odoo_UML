
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################
from base64 import b64encode
from os import path, unlink
from subprocess import Popen
from tempfile import NamedTemporaryFile

from odoo import models, fields, api

from odoo.addons.odoo_uml.utils.plant_uml import PlantUMLClassDiagram


def produce_package_name(module, **kwargs):
    if kwargs.get('show_descriptive_name', False):
        return u'{0}\\n{{{1}}}'.format(
            module.shortdesc,
            module.name
        )
    else:
        return module.name


def produce_package_stereotype(module, **kwargs):
    if module.application:
        return 'application'
    else:
        return 'module'


def produce_package_color(module, **kwargs):
    if module.application:
        return '#Silver'
    else:
        return '#White'

PIPE = -1
PLANT_UML_PATH = path.realpath(
    path.join(path.dirname(__file__), '..', 'bin', 'plantuml.jar')
)


def plant_uml_wrapper(module):
    f_out_puml = NamedTemporaryFile(mode='w', delete=False)
    f_out_puml.write(module.puml_dependency_diagram)
    f_out_puml.close()

    process = Popen([
        'java', '-jar', PLANT_UML_PATH, '-tpng',
        f_out_puml.name, '-o', '"%s"' % path.dirname(f_out_puml.name)
    ], stdout=PIPE, stderr=PIPE)

    std_out = str()
    while process.poll() is None:
        std_out += process.stdout.readline()

    f_out_diagram = open(name="%s.png" % f_out_puml.name, mode='rb')
    module.puml_dependency_diagram_png = b64encode(f_out_diagram.read())
    f_out_diagram.close()

    unlink(f_out_puml.name)
    unlink(f_out_diagram.name)
    return std_out


def generate_dependency_diagram(module, **kwargs):
    marks = []
    diagram = PlantUMLClassDiagram()
    diagram.begin_uml()
    marks.append(module.name)
    diagram.begin_package(
        produce_package_name(module, **kwargs),
        stereotype=produce_package_stereotype(module, **kwargs),
        color='#Yellow',
        alias=module.name
    ).end_package()

    def generate_dependency(dependency):
        if dependency.name not in marks:
            marks.append(dependency.name)
            diagram.begin_package(
                produce_package_name(dependency, **kwargs),
                stereotype=produce_package_stereotype(dependency, **kwargs),
                alias=dependency.name,
                color=produce_package_color(dependency, **kwargs)
            ).end_package()

            for sub in dependency.dependencies_id:
                generate_dependency(sub.depend_id)
                diagram.add_dependency(alias1=dependency.name, alias2=sub.depend_id.name)

    for dependency in module.dependencies_id:
        generate_dependency(dependency.depend_id)
        diagram.add_dependency(alias1=module.name, alias2=dependency.depend_id.name)

    diagram.end_uml()
    return diagram.output()


class Module(models.Model):
    _inherit = 'ir.module.module'

    puml_dependency_diagram = fields.Text(
        u'Dependency diagram',
        compute='_compute_dependency_diagram'
    )

    puml_dependency_diagram_log = fields.Text(
        u'Dependency diagram log',
        compute='_compute_dependency_diagram'
    )

    puml_dependency_diagram_png = fields.Binary(
        string=u'Dependency Diagram Image',
        help='Dependency diagram as encode base64 PNG image.',
        compute='_compute_dependency_diagram'
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
    def _compute_dependency_diagram(self):
        for module in self:
            kwargs = {
                'show_internal': module.puml_internal_struct,
                'show_descriptive_name': module.puml_package_human_name
            }
            module.puml_dependency_diagram = generate_dependency_diagram(module, **kwargs)
            module.puml_dependency_diagram_log = plant_uml_wrapper(module)
