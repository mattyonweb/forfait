from typing import *

class DependencyGraphException(Exception):
    pass

class Graph:
    """
    Needed to check for put an order on rewritings of types.
    """
    def __init__(self):
        self.outer_edges = dict()  # i vicini in uscita
        self.inner_edges = dict()  # i vicini entranti
        self.nodes = set()

    def __update(self, d, key, val):
        if key in d:
            d[key].append(val)
        else:
            d[key] = [val]

    def add_node(self, x):
        self.nodes.add(x)

    def add_edge(self, x, y):
        self.nodes.add(x)
        self.nodes.add(y)

        self.__update(self.outer_edges, x, y)
        self.__update(self.inner_edges, y, x)

    def is_terminal_generic(self, gen) -> List[Any]:
        return gen in self.nodes and (gen not in self.outer_edges)

    def ciclicity_check(self):
        for node in self.nodes:
            self.ciclicity_check_single_node(node, [])

    def ciclicity_check_single_node(self, node, path):
        if node not in self.outer_edges:
            return

        for neigh in self.outer_edges[node]:
            if neigh in path:
                raise DependencyGraphException(f"Found ciclicity: {path}")
            self.ciclicity_check_single_node(neigh, path + [neigh])


    def ordered_visit(self) -> List[Any]:
        """
        :return: Ordered list of nodes to visit.
        """

        # Se non ho nodi non ho niente da visitare
        if len(self.nodes) == 0:
            return []

        # Controllo se ci sono cicli, prima di iniziare qualsiasi visita
        self.ciclicity_check()

        # ordered list of nodes
        order = list()

        # initial elements are all nodes with no entering edges;
        # stack = list(self.nodes - set(self.inner_edges.keys()))
        stack = set()
        for node in self.nodes - set(self.inner_edges.keys()):
            # se un nodo è un singleton, escludilo
            # if node not in self.outer_edges:
            #     continue
            stack.add(node)
        stack = list(stack)


        while len(stack) > 0:
            node = stack.pop()

            # add extracted node to ordered list
            if node not in order:
                order.append(node)

            for neigh in self.outer_edges.get(node, []):
                # you can visit a node only if all its predecessors have already been visited
                if all(x in order for x in self.inner_edges[neigh]):
                    # don't output terminal nodes, you don't need them
                    # if not self.is_terminal_generic(neigh):
                    stack.append(neigh)

        return order

    def __str__(self):
        return f"Nodes:\n{[str(s) for s in self.nodes]}\n\nInner edges:\n{self.inner_edges}\n\nOuter edges:\n{self.outer_edges}"


if __name__ == '__main__':
    g = Graph()

    g.add_edge(5, 2)
    g.add_edge(2, 1)
    g.add_edge(5, 1)
    g.add_edge(1, 9)

    print(g.ordered_visit())