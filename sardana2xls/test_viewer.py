import utils
import tango

import networkx as nx
from networkx_viewer import Viewer
if __name__ == "__main__":
    db = tango.Database()
    elements = utils.get_elements("B110A-TMP", db)
    aliases = utils.generate_aliases_mapping(elements, db)
    ids = utils.generate_id_mapping(elements, db)
    ctrl_ids = utils.generate_prop_mapping(elements, db, 'ctrl_id')
    motor_ids = utils.generate_prop_mapping(elements, db, 'motor_role_ids')
    pseudo_ids = utils.generate_prop_mapping(elements, db, 'pseudo_motor_role_ids')
    # import pydot
    G = nx.MultiGraph()
    G.add_nodes_from(ids.values()
                     )

    def add_edge(iterable):
        for name, elems in iterable.items():
            for e in elems:
                G.add_edge(name, ids[e])
    add_edge(motor_ids)
    add_edge(pseudo_ids)
    add_edge(ctrl_ids)

    app = Viewer(G)
    app.mainloop()
