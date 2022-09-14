# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam

__all__ = ['mermaidx']


DIRECTION_TD = 'TD'
DIRECTION_DT = 'DT'
DIRECTION_LR = 'LR'
DIRECTION_RL = 'RL'


def mermaidx(graph, direction=DIRECTION_TD):
    """
    Creates an utf8 representation of a directed acyclic graph (DAG) for use with mermaid.js.
    """
    import networkx as nx

    if direction not in [DIRECTION_TD, DIRECTION_DT, DIRECTION_LR, DIRECTION_RL]:
        raise Exception('Invalid direction given')

    print_buffer = []
    _write = print_buffer.append

    if len(graph.nodes):
        print_buffer.append(f'graph {direction}\n')

        sources = [n for n in graph.nodes]
        stack = sources

        edge_choice_payload_display = nx.get_edge_attributes(graph, 'choice_payload_display')
        seen = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue  # Node already processed so skip it
            seen.add(node)  # Add node to seen set so that we can skip it if we see it again

            if set(graph.neighbors(node)):
                for neighbour_node in graph.neighbors(node):  # Loop through all neighbours of the node
                    choice_payload_display = edge_choice_payload_display[(node, neighbour_node, 0)]
                    choice_payload_display = f'|{choice_payload_display}|' if choice_payload_display else ''

                    node_label = f'{graph.nodes[node].get("label", "")}{" *" if graph.nodes[node].get("multiple_answers_allowed", False) else ""}'  # noqa
                    neighbour_node_label = f'["{graph.nodes[neighbour_node].get("label")}"]' if graph.nodes[neighbour_node].get('label') else ''  # noqa

                    _write(f'{graph.nodes[node].get("ref")}["{node_label}"] -->{choice_payload_display} {graph.nodes[neighbour_node].get("ref")}{neighbour_node_label}')  # noqa

                    stack.append(neighbour_node)  # push neighbour on stack
            else:
                label = f'{graph.nodes[node].get("label", "")}{" *" if graph.nodes[node].get("multiple_answers_allowed", False) else ""}'  # noqa
                _write(f'{graph.nodes[node].get("ref")}["{label}"]')

    return '\n'.join(print_buffer)
