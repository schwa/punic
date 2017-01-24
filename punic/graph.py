
import click
import networkx as nx
import os
import logging
import sys

from punic.errors import *
from punic.utilities import *
from punic.config import *
from punic.runner import *

def make_graph(punic, open):
    try:
        with error_handling():

            graph = punic.graph()

            logging.info('Writing graph file to "{}".'.format(os.getcwd()))
            nx.drawing.nx_pydot.write_dot(graph, 'graph.dot')

            command = 'dot graph.dot -ograph.png -Tpng'
            if runner.can_run(command):
                logging.info('Rendering dot file to png file.')
                runner.check_run(command)
                if open:
                    click.launch('graph.png')
            else:
                logging.warning('graphviz not installed. Cannot convert graph to a png.')
    except ImportError:
        pip = 'pip' if sys.version_info.major < 3 else 'pip3'
        steps = ['brew install graphviz', '{} install pydotplus'.format(pip)]
        lines = ['To enable graph generation please do the following:'] + ['\t' + step for step in steps]
        logging.error('\n'.join(lines))
