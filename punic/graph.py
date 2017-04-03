
import click
import networkx as nx
import os
import logging
import sys

from .errors import *
from .utilities import *
from .config import *
from .runner import *

def make_graph(session, launch):
    try:
        with error_handling():

            graph = session.graph()

            logging.info('Writing graph file to "{}".'.format(os.getcwd()))
            nx.drawing.nx_pydot.write_dot(graph, 'graph.dot')

            command = 'dot graph.dot -ograph.png -Tpng'
            if runner.can_run(command):
                logging.info('Rendering dot file to png file.')
                runner.check_run(command)
                if launch:
                    click.launch('graph.png')
            else:
                logging.warning('graphviz not installed. Cannot convert graph to a png.')
    except ImportError:
        pip = 'pip' if sys.version_info.major < 3 else 'pip3'
        steps = ['brew install graphviz', '{} install pydotplus'.format(pip)]
        lines = ['To enable graph generation please do the following:'] + ['\t' + step for step in steps]
        logging.error('\n'.join(lines))
