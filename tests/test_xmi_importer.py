import unittest

from app.services.uml_validator import validate_uml_relations
from app.services.xmi_importer import parse_xmi_to_diagram_content


EA_XMI = """<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://www.omg.org/spec/XMI/20131001"
         xmlns:uml="http://www.omg.org/spec/UML/20131001">
  <uml:Model xmi:id="model-1" name="Ventas">
    <packagedElement xmi:type="uml:Class" xmi:id="cliente" name="Cliente">
      <ownedAttribute xmi:type="uml:Property" xmi:id="cliente-id" name="id">
        <type xmi:idref="EAJava_long" />
        <lowerValue xmi:type="uml:LiteralInteger" value="1" />
      </ownedAttribute>
    </packagedElement>
    <packagedElement xmi:type="uml:Class" xmi:id="pedido" name="Pedido" />
    <packagedElement xmi:type="uml:Class" xmi:id="helper" name="List of Elements in Package Ventas" />
    <packagedElement xmi:type="uml:Association" xmi:id="cliente-pedido">
      <memberEnd xmi:idref="EAID_src_cliente_pedido" />
      <memberEnd xmi:idref="EAID_dst_cliente_pedido" />
      <ownedEnd xmi:type="uml:Property" xmi:id="EAID_src_cliente_pedido">
        <type xmi:idref="cliente" />
        <lowerValue xmi:type="uml:LiteralInteger" value="1" />
        <upperValue xmi:type="uml:LiteralUnlimitedNatural" value="1" />
      </ownedEnd>
      <ownedEnd xmi:type="uml:Property" xmi:id="EAID_dst_cliente_pedido">
        <type xmi:idref="pedido" />
        <lowerValue xmi:type="uml:LiteralInteger" value="0" />
        <upperValue xmi:type="uml:LiteralUnlimitedNatural" value="-1" />
      </ownedEnd>
    </packagedElement>
  </uml:Model>
  <xmi:Extension extender="Enterprise Architect">
    <elements>
      <element xmi:idref="cliente" xmi:type="uml:Class" name="Cliente" />
      <element xmi:idref="pedido" xmi:type="uml:Class" name="Pedido" />
      <element xmi:idref="cliente" xmi:type="uml:Class" name="Cliente" />
      <element xmi:idref="pedido" xmi:type="uml:Class" name="Pedido" />
    </elements>
    <diagrams>
      <diagram xmi:id="diagram-1" name="Principal">
        <elements>
          <element subject="cliente" geometry="Left=20;Top=30;Right=180;Bottom=130;" />
          <element subject="pedido" geometry="Left=360;Top=30;Right=520;Bottom=130;" />
        </elements>
      </diagram>
    </diagrams>
  </xmi:Extension>
</xmi:XMI>
"""


class XmiImporterTest(unittest.TestCase):
    def test_imports_ea_classes_once_and_resolves_nested_association_ends(self):
        content = parse_xmi_to_diagram_content(EA_XMI)

        self.assertEqual([node["data"]["name"] for node in content["nodes"]], ["Cliente", "Pedido"])
        self.assertEqual(content["nodes"][0]["data"]["attributes"][0]["type"], "long")
        self.assertEqual(len(content["edges"]), 1)

        edge = content["edges"][0]
        self.assertEqual(edge["source"], "cliente")
        self.assertEqual(edge["target"], "pedido")
        self.assertEqual(edge["type"], "umlRelation")
        self.assertEqual(edge["data"]["sourceCardinality"], "1")
        self.assertEqual(edge["data"]["targetCardinality"], "0..*")
        self.assertIsNone(validate_uml_relations(content))

    def test_imports_association_class_as_one_node_and_one_relation(self):
        xmi = """<xmi:XMI xmlns:xmi="http://www.omg.org/spec/XMI/20131001"
                            xmlns:uml="http://www.omg.org/spec/UML/20131001">
          <uml:Model xmi:id="model">
            <packagedElement xmi:type="uml:Class" xmi:id="student" name="Estudiante" />
            <packagedElement xmi:type="uml:Class" xmi:id="subject" name="Materia" />
            <packagedElement xmi:type="uml:AssociationClass" xmi:id="enrollment" name="Inscripcion">
              <ownedEnd xmi:type="uml:Property" xmi:id="src-enrollment" type="student" />
              <ownedEnd xmi:type="uml:Property" xmi:id="dst-enrollment" type="subject" />
            </packagedElement>
          </uml:Model>
        </xmi:XMI>"""

        content = parse_xmi_to_diagram_content(xmi)

        self.assertEqual(len(content["nodes"]), 3)
        self.assertEqual(len(content["edges"]), 1)
        self.assertEqual(content["edges"][0]["data"]["relationType"], "associationClass")
        self.assertEqual(content["edges"][0]["data"]["associationClassId"], "enrollment")
        self.assertIsNone(validate_uml_relations(content))


if __name__ == "__main__":
    unittest.main()
