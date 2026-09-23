from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from typing import Any


XMI_NS = "http://www.omg.org/spec/XMI/20131001"
UML_NS = "http://www.omg.org/spec/UML/20131001"

ET.register_namespace("xmi", XMI_NS)
ET.register_namespace("uml", UML_NS)


def safe_id(value: str):
    return (
        str(value)
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace(":", "_")
    )


def xmi_attr(name: str):
    return f"{{{XMI_NS}}}{name}"


def get_node_name(node: dict[str, Any]):
    data = node.get("data") or {}
    return data.get("name") or node.get("id") or "Clase"


def get_relation_type(edge: dict[str, Any]):
    data = edge.get("data") or {}
    return data.get("relationType") or edge.get("type") or "association"


def normalize_parameter(parameter: Any, index: int):
    if isinstance(parameter, dict):
        return {
            "name": str(parameter.get("name") or parameter.get("nombre") or f"parametro{index + 1}"),
            "type": str(parameter.get("type") or parameter.get("tipo") or "String"),
        }

    return {
        "name": str(parameter or f"parametro{index + 1}"),
        "type": "String",
    }


def create_class_element(
    model: ET.Element,
    node: dict[str, Any],
    force_association_class: bool = False,
):
    data = node.get("data") or {}
    node_id = str(node.get("id"))
    kind = data.get("kind") or "class"

    if force_association_class:
        element_type = "uml:AssociationClass"
    else:
        element_type = "uml:Interface" if kind == "interface" else "uml:Class"

    element_attributes = {
        xmi_attr("type"): element_type,
        xmi_attr("id"): safe_id(node_id),
        "name": str(get_node_name(node)),
    }
    if kind == "abstractClass":
        element_attributes["isAbstract"] = "true"

    class_element = ET.SubElement(
        model,
        "packagedElement",
        element_attributes,
    )

    for attr_index, attribute in enumerate(data.get("attributes") or []):
        attr_id = f"{safe_id(node_id)}_attr_{attr_index + 1}"
        owned_attribute = ET.SubElement(
            class_element,
            "ownedAttribute",
            {
                xmi_attr("id"): attr_id,
                "name": str(attribute.get("name") or f"atributo{attr_index + 1}"),
                "type": str(attribute.get("type") or "String"),
            },
        )

        if attribute.get("nullable") is False:
            ET.SubElement(
                owned_attribute,
                "lowerValue",
                {
                    xmi_attr("type"): "uml:LiteralInteger",
                    xmi_attr("id"): f"{attr_id}_lower",
                    "value": "1",
                },
            )

    for method_index, method in enumerate(data.get("methods") or []):
        method_id = f"{safe_id(node_id)}_op_{method_index + 1}"
        operation = ET.SubElement(
            class_element,
            "ownedOperation",
            {
                xmi_attr("id"): method_id,
                "name": str(method.get("name") or f"metodo{method_index + 1}"),
            },
        )

        for param_index, parameter in enumerate(method.get("parameters") or []):
            normalized_parameter = normalize_parameter(parameter, param_index)

            ET.SubElement(
                operation,
                "ownedParameter",
                {
                    xmi_attr("id"): f"{method_id}_param_{param_index + 1}",
                    "name": normalized_parameter["name"],
                    "type": normalized_parameter["type"],
                },
            )

        return_type = method.get("returnType")

        if return_type and return_type != "void":
            ET.SubElement(
                operation,
                "ownedParameter",
                {
                    xmi_attr("id"): f"{method_id}_return",
                    "name": "return",
                    "type": str(return_type),
                    "direction": "return",
                },
            )

    return class_element


def add_generalization(class_elements: dict[str, ET.Element], edge: dict[str, Any]):
    source = str(edge.get("source"))
    target = str(edge.get("target"))
    source_element = class_elements.get(source)

    if source_element is None:
        return

    ET.SubElement(
        source_element,
        "generalization",
        {
            xmi_attr("id"): safe_id(str(edge.get("id") or f"gen_{source}_{target}")),
            "general": safe_id(target),
        },
    )


def cardinality_bounds(cardinality: Any):
    return {
        "1": ("1", "1"),
        "0..1": ("0", "1"),
        "0..*": ("0", "*"),
        "1..*": ("1", "*"),
    }.get(str(cardinality), ("1", "1"))


def add_multiplicity(
    owned_end: ET.Element,
    cardinality: Any,
    end_id: str,
):
    lower, upper = cardinality_bounds(cardinality)
    ET.SubElement(
        owned_end,
        "lowerValue",
        {
            xmi_attr("type"): "uml:LiteralInteger",
            xmi_attr("id"): f"{end_id}_lower",
            "value": lower,
        },
    )
    ET.SubElement(
        owned_end,
        "upperValue",
        {
            xmi_attr("type"): "uml:LiteralUnlimitedNatural",
            xmi_attr("id"): f"{end_id}_upper",
            "value": upper,
        },
    )


def add_binary_association_ends(
    association: ET.Element,
    edge: dict[str, Any],
    association_id: str,
):
    relation_type = get_relation_type(edge)
    data = edge.get("data") or {}
    source = safe_id(str(edge.get("source")))
    target = safe_id(str(edge.get("target")))
    edge_id = safe_id(str(edge.get("id") or f"rel_{source}_{target}"))
    source_end_id = f"{edge_id}_source"
    target_end_id = f"{edge_id}_target"

    source_attrs = {
        xmi_attr("type"): "uml:Property",
        xmi_attr("id"): source_end_id,
        "type": source,
        "association": association_id,
    }
    target_attrs = {
        xmi_attr("type"): "uml:Property",
        xmi_attr("id"): target_end_id,
        "type": target,
        "association": association_id,
    }

    if data.get("sourceRole"):
        source_attrs["name"] = str(data["sourceRole"])
    if data.get("targetRole"):
        target_attrs["name"] = str(data["targetRole"])

    if relation_type == "composition":
        source_attrs["aggregation"] = "composite"

    if relation_type == "aggregation":
        source_attrs["aggregation"] = "shared"

    source_end = ET.SubElement(association, "ownedEnd", source_attrs)
    target_end = ET.SubElement(association, "ownedEnd", target_attrs)
    add_multiplicity(source_end, data.get("sourceCardinality", "1"), source_end_id)
    add_multiplicity(target_end, data.get("targetCardinality", "0..*"), target_end_id)

    existing_member_ends = association.get("memberEnd", "").split()
    association.set(
        "memberEnd",
        " ".join([*existing_member_ends, source_end_id, target_end_id]),
    )
    association.set("navigableOwnedEnd", f"{source_end_id} {target_end_id}")


def add_association(model: ET.Element, edge: dict[str, Any]):
    data = edge.get("data") or {}
    source = safe_id(str(edge.get("source")))
    target = safe_id(str(edge.get("target")))
    relation_id = safe_id(str(edge.get("id") or f"rel_{source}_{target}"))
    association_attributes = {
        xmi_attr("type"): "uml:Association",
        xmi_attr("id"): relation_id,
    }
    if data.get("name"):
        association_attributes["name"] = str(data["name"])

    association = ET.SubElement(model, "packagedElement", association_attributes)
    add_binary_association_ends(association, edge, relation_id)


def add_association_class(
    class_elements: dict[str, ET.Element],
    edge: dict[str, Any],
):
    data = edge.get("data") or {}
    association_class_id = str(data.get("associationClassId") or "")
    association_class = class_elements.get(association_class_id)
    if association_class is None:
        return

    add_binary_association_ends(
        association_class,
        edge,
        safe_id(association_class_id),
    )


def diagram_content_to_xmi(contenido: dict[str, Any], nombre: str = "DrawSchemaModel"):
    root = ET.Element(
        f"{{{XMI_NS}}}XMI",
        {
            xmi_attr("version"): "2.1",
        },
    )

    model = ET.SubElement(
        root,
        f"{{{UML_NS}}}Model",
        {
            xmi_attr("id"): "DrawSchemaModel",
            "name": html.escape(nombre),
        },
    )

    class_elements: dict[str, ET.Element] = {}
    association_class_ids = {
        str((edge.get("data") or {}).get("associationClassId"))
        for edge in contenido.get("edges", [])
        if get_relation_type(edge) == "associationClass"
        and (edge.get("data") or {}).get("associationClassId")
    }

    for node in contenido.get("nodes", []):
        node_id = str(node.get("id"))
        class_elements[node_id] = create_class_element(
            model,
            node,
            force_association_class=node_id in association_class_ids,
        )

    for edge in contenido.get("edges", []):
        relation_type = get_relation_type(edge)

        if relation_type == "generalization":
            add_generalization(class_elements, edge)
        elif relation_type in {"association", "composition", "aggregation"}:
            add_association(model, edge)
        elif relation_type == "associationClass":
            add_association_class(class_elements, edge)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
