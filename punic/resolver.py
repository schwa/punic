from __future__ import division, absolute_import, print_function

__all__ = ['Resolver', 'Node']

from collections import (defaultdict, namedtuple)
from networkx import (DiGraph, dfs_preorder_nodes, topological_sort, number_of_nodes, number_of_edges)
import logging
from networkx.readwrite import json_graph
import json
import punic
from .utilities import reveal
from .repository import *

class Node:
    def __init__(self, identifier, version):
        self.identifier = identifier
        self.version = version
    def __repr__(self):
        return "{}@{}".format(self.identifier, self.version)
    def items(self):
        return self.identifier, self.version

    def __hash__(self):
        return hash(self.identifier) ^ hash(self.version)

    def __eq__(self, other):
        return self.identifier == other.identifier and self.version == other.version


#Node = namedtuple("Node", "identifier version")


class Resolver(object):
    def __init__(self, root, dependencies_for_node, export_diagnostics = False):
        self.root = root
        self.dependencies_for_node = dependencies_for_node
        self.export_diagnostics = export_diagnostics

    def build_graph(self, dependency_filter=None):
        def populate_graph(graph, parent, depth=0):
            graph.add_node(parent)
            for child_identifier, child_versions in self._dependencies_for_node(parent):
                for child_version in child_versions:
                    child = Node(child_identifier, child_version)
                    if dependency_filter and dependency_filter(child.identifier, child.version) == False:
                        continue
                    graph.add_edge(parent, child)
                    populate_graph(graph, child, depth=depth + 1)
        graph = DiGraph()
        populate_graph(graph=graph, parent=self.root)
        return graph

    def resolve(self):
        # type: () -> DiGraph

        for dependency, revisions in self._dependencies_for_node(self.root):
            logging.debug('<ref>{}</ref> <rev>{}</rev>'.format(dependency, revisions))

        logging.debug('Building universal graph')

        # Build a graph up of _all_ version of _all_ dependencies
        graph = self.build_graph()
        logging.debug('Input universal graph has {} nodes, {} edges.'.format(number_of_nodes(graph), number_of_edges(graph)))

        ################################################################################################################

        if self.export_diagnostics:
            def default(obj):
                if isinstance(obj, (Node)):
                    return str(obj)
                else:
                    raise Exception("Unknown type: {}".format(type(obj)))
            # https://networkx.github.io/documentation/networkx-1.10/reference/readwrite.json_graph.html
            j = json_graph.node_link_data(graph, dict(id='id', source='source.id', target='target.id', key='key'))


            path = (punic.current_session.config.library_directory / "test.json")
            json.dump(j, path.open("wb"), indent=4, default=default)

            reveal(path)

        ################################################################################################################

        # Build a dictionary of all versions of all dependencies
        all_dependencies = defaultdict(set)
        for node in dfs_preorder_nodes(graph):
            all_dependencies[node.identifier].add(node.version)

        ################################################################################################################

        def prune_1():
            for dependency, versions in all_dependencies.items():
                if len(versions) <= 1:
                    continue
                for version in sorted(versions):
                    if len(graph.predecessors(Node(dependency, version))) <= 1:
                        graph.remove_node(Node(dependency, version))
                        all_dependencies[dependency].remove(version)
                    if len(versions) <= 1:
                        break

        def prune_2():
            def prune(node):
                mini = defaultdict(set)
                if not node in graph:
                    return

                for node in graph.successors(node):
                    mini[node.identifier].add(node.version)
                for dependency, versions in mini.items():
                    some = all_dependencies[dependency]
                    difference = some.difference(versions)
                    for version in difference:
                        graph.remove_node(Node(dependency, version))
                        all_dependencies[dependency].remove(version)
                for successor in graph.successors(node):
                    prune(successor)

            prune(self.root)

        ################################################################################################################

        logging.debug('<sub>Pruning graph</sub>')

        prune_1()
        prune_2()

        logging.debug('Pruned graph has {} nodes, {} edges.'.format(number_of_nodes(graph), number_of_edges(graph)))

        ################################################################################################################

        logging.debug('<sub>Uniquing graph</sub>')

        # Calculate a unique set of dependencies. If multiple dependnecies have the same child dependency this "uniques" them
        dependencies = set([(dependency, sorted(versions)[-1]) for dependency, versions in sorted(all_dependencies.items())])

        # Build a graph _again_ but only with actual dependencies. This is the "correct" dependency graph
        graph = self.build_graph(dependency_filter=lambda child, child_version: (child, child_version) in dependencies)

        logging.debug('Uniqued graph has {} nodes, {} edges.'.format(number_of_nodes(graph), number_of_edges(graph)))

        ################################################################################################################

        return graph

    def resolve_build_order(self):
        # type: () -> [(ProjectIdentifier, Revision)]
        graph = self.resolve()
        logging.debug('<sub>Topologically sorting graph</sub>')
        build_order = topological_sort(graph, reverse=True)
        return build_order

    def resolve_versions(self, dependencies):
        # type: (ProjectIdentifier, Revision) -> [ProjectIdentifier, Tag]
        """Given an array of project identifier/version pairs work out the build order"""

        graph = DiGraph()
        versions_for_identifier = dict(dependencies)
        for identifier, version in dependencies:
            parent = Node(identifier, version)
            graph.add_node(parent)

            assert isinstance(version, Revision)

            dependencies_for_node = self._dependencies_for_node(Node(identifier, version))

            for dependency, _ in dependencies_for_node:
                version = versions_for_identifier[dependency]
                child = Node(dependency, version)
                graph.add_edge(parent, child)
        build_order = topological_sort(graph, reverse=True)

        return build_order

    def _dependencies_for_node(self, node):
        # type: (Edge, bool) -> [Any, [Any]]
        return self.dependencies_for_node(node)


def dump(stream, graph, node, depth=0):
    count = len(graph.predecessors(node))

    stream.write("{}{} {}\n".format('\t' * depth, node, count))
    for child in sorted(graph[node].keys()):
        dump(stream, graph, child, depth + 1)
