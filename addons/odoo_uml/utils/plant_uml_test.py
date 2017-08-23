# -*- coding: utf-8 -*-
import unittest

from plant_uml import StringUtil, PlantUMLClassDiagram


class TestStringUtil(unittest.TestCase):
    def setUp(self):
        self.util = StringUtil()

    def test_newline(self):
        self.assertEqual(self.util.newline().output(), '\n')

    def test_tab(self):
        self.assertEqual(self.util.tab().output(), '\t')

    def test_clear(self):
        self.assertEqual(self.util.clear().output(), '', "Clear failed!")

    def test_restart(self):
        self.assertEqual(
            self.util.append('A').restart().output(),
            ''
        )

    def test_append(self):
        self.assertEqual(self.util.append('A').output(), 'A')
        self.assertEqual(self.util.append('B').output(), 'AB')

    def test_push(self):
        self.assertEqual(
            self.util.append('A').push().output(),
            ''
        )
        self.assertEqual(
            self.util.pop().output(),
            'A'
        )

    def test_pop(self):
        self.assertEqual(
            self.util
            .append('A')
            .push()
            .append('B')
            .pop()
            .output(),
            'AB'
        )


class TestPlantUMLClassDiagram(unittest.TestCase):
    def setUp(self):
        self.diagram = PlantUMLClassDiagram()

    def test_begin_uml(self):
        self.assertEqual(
            self.diagram.begin_uml().end_uml().output(),
            '@startuml\n@enduml'
        )

    def test_begin_package(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" {\n\t\n}\n@enduml'
        )

    def test_begin_package_stetreotype(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" <<Cloud>> {\n\t\n}\n@enduml'
        )

    def test_begin_package_alias(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud', alias='pd0000')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" as pd0000 <<Cloud>> {\n\t\n}\n@enduml'
        )

    def test_begin_package_color(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud', alias='pd0000', color='#DDDDDD')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" as pd0000 <<Cloud>> #DDDDDD {\n\t\n}\n@enduml'
        )

    def test_begin_package_inner(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud', alias='pd0000', color='#DDDDDD')
            .begin_package('inner', stereotype='Cloud', alias='pd0001', color='#DDDDDD')
            .end_package()
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" as pd0000 <<Cloud>> #DDDDDD {\n\tpackage "inner"'
            ' as pd0001 <<Cloud>> #DDDDDD {\n\t\t\n\t}\n\t\n}\n@enduml'
        )

    def test_add_dependency(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .add_dependency('A', 'B')
            .end_uml()
            .output(),
            '@startuml\nA ..> B\n@enduml'
        )

    def test_add_dependency_alias(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .add_dependency('A', 'B')
            .end_uml()
            .output(),
            '@startuml\nA ..> B\n@enduml'
        )


if __name__ == '__main__':
    unittest.main()
