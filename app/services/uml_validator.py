from collections import defaultdict
from typing import Any


VALID_RELATION_TYPES = {
    "association",
    "generalization",
    "composition",
    "aggregation",
    "associationClass",
    "realization",
    "templateBinding",
}

VALID_CARDINALITIES = {
    "1",
    "0..1",
    "0..*",
    "1..*",
}


def get_relation_type(edge: dict[str, Any]):
    data = edge.get("data") or {}
    return data.get("relationType") or data.get("type") or edge.get("type")


def get_source_class_id(edge: dict[str, Any]):
    data = edge.get("data") or {}
    return data.get("sourceClassId") or edge.get("source")


def get_target_class_id(edge: dict[str, Any]):
    data = edge.get("data") or {}
    return data.get("targetClassId") or edge.get("target")


def get_node_data(node: dict[str, Any]):
    data = node.get("data")
    return data if isinstance(data, dict) else {}


def has_cycle(graph: dict[str, list[str]]):
    visited = set()
    visiting = set()

    def visit(node_id: str):
        if node_id in visiting:
            return True

        if node_id in visited:
            return False

        visiting.add(node_id)

        for next_id in graph.get(node_id, []):
            if visit(next_id):
                return True

        visiting.remove(node_id)
        visited.add(node_id)
        return False

    return any(visit(node_id) for node_id in graph)


def node_is_template(node: dict[str, Any]):
    data = get_node_data(node)
    name = str(data.get("name") or "")
    parameters = data.get("templateParameters")

    return (
        isinstance(parameters, list)
        and len(parameters) > 0
    ) or ("<" in name and ">" in name)


def validate_uml_relations(contenido: dict[str, Any]):
    nodes = contenido.get("nodes", [])
    edges = contenido.get("edges", [])

    if not isinstance(nodes, list):
        return "contenido.nodes debe ser una lista"

    if not isinstance(edges, list):
        return "contenido.edges debe ser una lista"

    node_by_id = {}

    for node in nodes:
        node_id = node.get("id")

        if not node_id:
            return "Todos los nodes deben tener id"

        node_by_id[node_id] = node
        node_by_id[str(node_id).strip()] = node

    relation_keys = set()
    generalization_parent_by_child = {}
    generalization_graph = defaultdict(list)
    composition_whole_by_part = {}
    composition_graph = defaultdict(list)
    association_class_links = set()

    for edge in edges:
        edge_id = edge.get("id")
        data = edge.get("data") or {}
        relation_type = get_relation_type(edge)
        source_class_id = get_source_class_id(edge)
        target_class_id = get_target_class_id(edge)

        if not edge_id:
            return "Todas las relaciones deben tener id"

        if relation_type not in VALID_RELATION_TYPES:
            return f"Tipo de relacion no permitido: {relation_type}"

        if source_class_id not in node_by_id:
            return f"sourceClassId no existe en nodes: {source_class_id}"

        if target_class_id not in node_by_id:
            return f"targetClassId no existe en nodes: {target_class_id}"

        if edge.get("source") != source_class_id:
            return f"source del edge debe coincidir con data.sourceClassId en la relacion {edge_id}"

        if edge.get("target") != target_class_id:
            return f"target del edge debe coincidir con data.targetClassId en la relacion {edge_id}"

        for key in ("sourceCardinality", "targetCardinality", "cardinality"):
            cardinality = data.get(key)

            if cardinality is not None and cardinality not in VALID_CARDINALITIES:
                return f"Cardinalidad no permitida en {edge_id}: {cardinality}"

        if relation_type in {"association", "associationClass"}:
            relation_key = (relation_type, *sorted([source_class_id, target_class_id]))
        else:
            relation_key = (relation_type, source_class_id, target_class_id)

        if relation_key in relation_keys:
            return f"Relacion duplicada: {relation_type} entre {source_class_id} y {target_class_id}"

        relation_keys.add(relation_key)

        if relation_type not in {"association", "associationClass"} and source_class_id == target_class_id:
            return f"La relacion {relation_type} no puede ser recursiva"

        if relation_type == "generalization":
            if source_class_id == target_class_id:
                return "Una clase no puede heredar de si misma"

            if source_class_id in generalization_parent_by_child:
                return f"La clase {source_class_id} ya tiene una clase padre"

            generalization_parent_by_child[source_class_id] = target_class_id
            generalization_graph[source_class_id].append(target_class_id)
            data["childClassId"] = source_class_id
            data["parentClassId"] = target_class_id

        if relation_type == "composition":
            if source_class_id == target_class_id:
                return "Una composicion no puede ser consigo misma"

            if target_class_id in composition_whole_by_part:
                return f"La parte {target_class_id} ya pertenece a otro todo por composicion"

            composition_whole_by_part[target_class_id] = source_class_id
            composition_graph[source_class_id].append(target_class_id)
            data["wholeClassId"] = source_class_id
            data["partClassId"] = target_class_id

        if relation_type == "aggregation":
            if source_class_id == target_class_id:
                return "Una agregacion no puede ser consigo misma"

            data["wholeClassId"] = source_class_id
            data["partClassId"] = target_class_id

        if relation_type == "associationClass":
            association_class_id = data.get("associationClassId")

            if association_class_id not in node_by_id:
                return f"associationClassId no existe en nodes: {association_class_id}"

            if association_class_id in {source_class_id, target_class_id}:
                return "La clase de asociacion debe ser una clase diferente a las clases relacionadas"

            link_key = tuple(sorted([source_class_id, target_class_id]))

            if link_key in association_class_links:
                return f"Ya existe una associationClass para el vinculo {source_class_id}-{target_class_id}"

            association_class_links.add(link_key)

        if relation_type == "realization":
            target_data = get_node_data(node_by_id[target_class_id])

            if target_data.get("kind") != "interface":
                return "En realization, targetClassId debe ser una interfaz"

        if relation_type == "templateBinding":
            target_node = node_by_id[target_class_id]

            if not node_is_template(target_node):
                return "En templateBinding, targetClassId debe ser una plantilla"

            template_bindings = data.get("templateBindings")

            if not isinstance(template_bindings, dict) or not template_bindings:
                return "templateBinding debe tener templateBindings completos"

            target_data = get_node_data(target_node)
            expected_params = target_data.get("templateParameters")

            if isinstance(expected_params, list) and expected_params:
                missing = [param for param in expected_params if not template_bindings.get(param)]

                if missing:
                    return f"Faltan templateBindings para: {', '.join(missing)}"

        edge["data"] = data

    if has_cycle(generalization_graph):
        return "No se permiten ciclos de herencia"

    if has_cycle(composition_graph):
        return "No se permite composicion circular"

    return None
