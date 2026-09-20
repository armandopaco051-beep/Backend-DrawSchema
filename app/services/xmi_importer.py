from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


RELATION_TYPES = {
    "association": "association",
    "generalization": "generalization",
    "composition": "composition",
    "aggregation": "aggregation",
    "realization": "realization",
}


def local_name(tag: str):
    if "}" in tag:
        return tag.rsplit("}", 1)[1]

    return tag.split(":")[-1]


def attr_by_suffix(element: ET.Element, suffix: str):
    for key, value in element.attrib.items():
        if key == suffix or key.endswith(f"}}{suffix}") or key.endswith(f":{suffix}"):
            return value

    return None


def xmi_id(element: ET.Element):
    return (
        attr_by_suffix(element, "id")
        or attr_by_suffix(element, "xmi:id")
        or element.get("id")
    )


def xmi_type(element: ET.Element):
    return (
        attr_by_suffix(element, "type")
        or attr_by_suffix(element, "xmi:type")
        or ""
    )


def is_uml_type(element: ET.Element, expected: str):
    value = xmi_type(element).lower()
    return value.endswith(expected.lower())


def get_type_name(type_id: str | None, primitive_types: dict[str, str]):
    if not type_id:
        return "String"

    return primitive_types.get(type_id, type_id)


def parse_lower_nullable(element: ET.Element):
    lower = element.get("lower")

    for child in element:
        if local_name(child.tag) == "lowerValue":
            lower = child.get("value", lower)

    return lower in {None, "0"}


def parse_attributes(class_element: ET.Element, primitive_types: dict[str, str]):
    attributes: list[dict[str, Any]] = []

    for child in class_element:
        if local_name(child.tag) != "ownedAttribute":
            continue

        name = child.get("name") or "atributo"
        attr_type = get_type_name(child.get("type"), primitive_types)

        attributes.append(
            {
                "name": name,
                "type": attr_type,
                "primaryKey": name.lower() in {"id", "codigo"},
                "nullable": parse_lower_nullable(child),
            }
        )

    return attributes


def parse_methods(class_element: ET.Element, primitive_types: dict[str, str]):
    methods: list[dict[str, Any]] = []

    for child in class_element:
        if local_name(child.tag) != "ownedOperation":
            continue

        parameters = []
        return_type = "void"

        for parameter in child:
            if local_name(parameter.tag) != "ownedParameter":
                continue

            parameter_name = parameter.get("name") or "parametro"
            direction = parameter.get("direction")
            parameter_type = get_type_name(parameter.get("type"), primitive_types)

            if direction == "return":
                return_type = parameter_type
            else:
                parameters.append(
                    {
                        "name": parameter_name,
                        "type": parameter_type,
                    }
                )

        methods.append(
            {
                "name": child.get("name") or "metodo",
                "returnType": return_type,
                "parameters": parameters,
            }
        )

    return methods


def collect_primitive_types(root: ET.Element):
    primitive_types: dict[str, str] = {}

    for element in root.iter():
        if is_uml_type(element, "PrimitiveType") or local_name(element.tag) == "packagedElement":
            element_id = xmi_id(element)
            name = element.get("name")

            if element_id and name:
                primitive_types[element_id] = name

    return primitive_types


def collect_classes(root: ET.Element, primitive_types: dict[str, str]):
    nodes = []
    class_ids: set[str] = set()

    class_elements = [
        element
        for element in root.iter()
        if is_uml_type(element, "Class") or is_uml_type(element, "Interface")
    ]

    for index, element in enumerate(class_elements):
        class_id = xmi_id(element) or f"class-imported-{index + 1}"
        class_ids.add(class_id)

        kind = "interface" if is_uml_type(element, "Interface") else "class"

        nodes.append(
            {
                "id": class_id,
                "type": "classNode",
                "position": {
                    "x": 120 + (index % 4) * 260,
                    "y": 100 + (index // 4) * 220,
                },
                "data": {
                    "name": element.get("name") or f"Clase{index + 1}",
                    "kind": kind,
                    "attributes": parse_attributes(element, primitive_types),
                    "methods": parse_methods(element, primitive_types),
                },
            }
        )

    return nodes, class_ids


def collect_generalizations(root: ET.Element, class_ids: set[str]):
    edges = []

    for class_element in root.iter():
        child_id = xmi_id(class_element)

        if child_id not in class_ids:
            continue

        for relation in class_element:
            if local_name(relation.tag) != "generalization":
                continue

            parent_id = relation.get("general")

            if parent_id not in class_ids:
                continue

            relation_id = xmi_id(relation) or f"rel-generalization-{child_id}-{parent_id}"

            edges.append(
                {
                    "id": relation_id,
                    "source": child_id,
                    "target": parent_id,
                    "type": "generalization",
                    "data": {
                        "relationType": "generalization",
                        "sourceClassId": child_id,
                        "targetClassId": parent_id,
                        "childClassId": child_id,
                        "parentClassId": parent_id,
                    },
                }
            )

    return edges


def relation_type_from_association(element: ET.Element):
    aggregation_values = [
        child.get("aggregation")
        for child in element
        if local_name(child.tag) in {"ownedEnd", "memberEnd"}
    ]

    if "composite" in aggregation_values:
        return "composition"

    if "shared" in aggregation_values:
        return "aggregation"

    return "association"


def collect_associations(root: ET.Element, class_ids: set[str]):
    edges = []

    for element in root.iter():
        if not is_uml_type(element, "Association"):
            continue

        relation_id = xmi_id(element) or f"rel-association-{len(edges) + 1}"
        relation_type = relation_type_from_association(element)
        source_id = None
        target_id = None

        member_end_ids = (element.get("memberEnd") or "").split()
        owned_types = [
            child.get("type")
            for child in element
            if local_name(child.tag) in {"ownedEnd", "memberEnd"}
        ]

        candidate_ids = [item for item in owned_types + member_end_ids if item in class_ids]

        if len(candidate_ids) >= 2:
            source_id = candidate_ids[0]
            target_id = candidate_ids[1]

        if source_id not in class_ids or target_id not in class_ids:
            continue

        data = {
            "relationType": relation_type,
            "sourceClassId": source_id,
            "targetClassId": target_id,
        }

        if relation_type in {"composition", "aggregation"}:
            data["wholeClassId"] = source_id
            data["partClassId"] = target_id

        edges.append(
            {
                "id": relation_id,
                "source": source_id,
                "target": target_id,
                "type": relation_type,
                "data": data,
            }
        )

    return edges


def parse_xmi_to_diagram_content(xmi_text: str):
    try:
        root = ET.fromstring(xmi_text)
    except ET.ParseError as exc:
        raise ValueError("El archivo XMI no tiene un XML valido") from exc

    primitive_types = collect_primitive_types(root)
    nodes, class_ids = collect_classes(root, primitive_types)
    edges = []
    edges.extend(collect_generalizations(root, class_ids))
    edges.extend(collect_associations(root, class_ids))

    return {
        "nodes": nodes,
        "edges": edges,
    }
