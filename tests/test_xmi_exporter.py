import unittest
import xml.etree.ElementTree as ET

from app.services.xmi_exporter import XMI_NS, diagram_content_to_xmi


def xmi_type(element: ET.Element):
    return element.get(f"{{{XMI_NS}}}type")


class XmiExporterTest(unittest.TestCase):
    def test_exports_binary_association_with_multiplicities(self):
        content = {
            "nodes": [
                {"id": "class-a", "data": {"name": "Cliente"}},
                {"id": "class-b", "data": {"name": "Pedido"}},
            ],
            "edges": [
                {
                    "id": "rel-1",
                    "source": "class-a",
                    "target": "class-b",
                    "data": {
                        "relationType": "association",
                        "sourceCardinality": "1",
                        "targetCardinality": "0..*",
                    },
                }
            ],
        }

        root = ET.fromstring(diagram_content_to_xmi(content, "Ventas"))
        association = next(
            item for item in root.iter() if xmi_type(item) == "uml:Association"
        )
        ends = [item for item in association if item.tag == "ownedEnd"]

        self.assertEqual(association.get("memberEnd"), "rel_1_source rel_1_target")
        self.assertNotIn("name", association.attrib)
        self.assertEqual(len(ends), 2)
        self.assertTrue(all(xmi_type(item) == "uml:Property" for item in ends))
        self.assertEqual(ends[0].find("lowerValue").get("value"), "1")
        self.assertEqual(ends[0].find("upperValue").get("value"), "1")
        self.assertEqual(ends[1].find("lowerValue").get("value"), "0")
        self.assertEqual(ends[1].find("upperValue").get("value"), "*")

    def test_exports_composition_diamond_on_whole_end(self):
        content = {
            "nodes": [
                {"id": "order", "data": {"name": "Pedido"}},
                {"id": "item", "data": {"name": "DetallePedido"}},
            ],
            "edges": [
                {
                    "id": "composition-1",
                    "source": "order",
                    "target": "item",
                    "data": {
                        "relationType": "composition",
                        "sourceCardinality": "1",
                        "targetCardinality": "1..*",
                    },
                }
            ],
        }

        root = ET.fromstring(diagram_content_to_xmi(content, "Pedidos"))
        association = next(
            item for item in root.iter() if xmi_type(item) == "uml:Association"
        )
        ends = [item for item in association if item.tag == "ownedEnd"]

        self.assertEqual(ends[0].get("type"), "order")
        self.assertEqual(ends[0].get("aggregation"), "composite")
        self.assertIsNone(ends[1].get("aggregation"))
        self.assertEqual(ends[0].find("lowerValue").get("value"), "1")
        self.assertEqual(ends[1].find("lowerValue").get("value"), "1")
        self.assertEqual(ends[1].find("upperValue").get("value"), "*")

    def test_exports_association_class_as_uml_association_class(self):
        content = {
            "nodes": [
                {"id": "student", "data": {"name": "Estudiante"}},
                {"id": "subject", "data": {"name": "Materia"}},
                {
                    "id": "enrollment",
                    "data": {
                        "name": "Inscripcion",
                        "attributes": [{"name": "fecha", "type": "DATE"}],
                    },
                },
            ],
            "edges": [
                {
                    "id": "association-class-1",
                    "source": "student",
                    "target": "subject",
                    "data": {
                        "relationType": "associationClass",
                        "associationClassId": "enrollment",
                        "sourceCardinality": "0..*",
                        "targetCardinality": "0..*",
                    },
                }
            ],
        }

        root = ET.fromstring(diagram_content_to_xmi(content, "Academico"))
        association_class = next(
            item for item in root.iter() if xmi_type(item) == "uml:AssociationClass"
        )
        association_elements = [
            item for item in root.iter() if xmi_type(item) == "uml:Association"
        ]

        self.assertEqual(association_class.get("name"), "Inscripcion")
        self.assertEqual(
            association_class.get("memberEnd"),
            "association_class_1_source association_class_1_target",
        )
        self.assertEqual(len(association_elements), 0)
        self.assertEqual(
            [item.get("association") for item in association_class.findall("ownedEnd")],
            ["enrollment", "enrollment"],
        )


if __name__ == "__main__":
    unittest.main()
