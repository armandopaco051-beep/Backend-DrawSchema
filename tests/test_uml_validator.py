import unittest

from app.services.uml_validator import validate_uml_relations


def class_node(node_id: str):
    return {"id": node_id, "data": {"name": node_id}}


class UmlValidatorCardinalityTest(unittest.TestCase):
    def test_generalization_removes_multiplicities(self):
        content = {
            "nodes": [class_node("child"), class_node("parent")],
            "edges": [
                {
                    "id": "inheritance-1",
                    "source": "child",
                    "target": "parent",
                    "data": {
                        "relationType": "generalization",
                        "sourceClassId": "child",
                        "targetClassId": "parent",
                        "sourceCardinality": "1",
                        "targetCardinality": "0..*",
                    },
                }
            ],
        }

        self.assertIsNone(validate_uml_relations(content))
        data = content["edges"][0]["data"]
        self.assertNotIn("sourceCardinality", data)
        self.assertNotIn("targetCardinality", data)

    def test_composition_keeps_valid_multiplicities(self):
        content = {
            "nodes": [class_node("order"), class_node("item")],
            "edges": [
                {
                    "id": "composition-1",
                    "source": "order",
                    "target": "item",
                    "data": {
                        "relationType": "composition",
                        "sourceClassId": "order",
                        "targetClassId": "item",
                        "sourceCardinality": "1",
                        "targetCardinality": "1..*",
                    },
                }
            ],
        }

        self.assertIsNone(validate_uml_relations(content))
        self.assertEqual(content["edges"][0]["data"]["targetCardinality"], "1..*")

    def test_composition_rejects_multiple_wholes_for_one_part(self):
        content = {
            "nodes": [class_node("order"), class_node("item")],
            "edges": [
                {
                    "id": "composition-1",
                    "source": "order",
                    "target": "item",
                    "data": {
                        "relationType": "composition",
                        "sourceClassId": "order",
                        "targetClassId": "item",
                        "sourceCardinality": "0..*",
                        "targetCardinality": "1..*",
                    },
                }
            ],
        }

        error = validate_uml_relations(content)
        self.assertIn("sourceCardinality debe ser 1 o 0..1", error or "")


if __name__ == "__main__":
    unittest.main()
