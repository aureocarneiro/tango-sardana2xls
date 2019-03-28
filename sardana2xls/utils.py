import tango
import collections


class unique_dict(collections.MutableMapping):

    def __init__(self, *args, **kwargs):
        self._store = dict()
        self._inverted = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        """ issue allowed:
            store     {1: 2, 3: 4, 5: 3}
            inverted  {2: 1, 3: 5, 4: 3}
        """
        if value in self._inverted:
            self._store.pop(self._inverted.pop(value))
        if key in self._store and self._store[key] in self._inverted:
            self._inverted.pop(self._store.pop(key))
        self._inverted[value] = key
        self._store[key] = value

    def __delitem__(self, key):
        del self._inverted[self._store[key]]
        del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return self._store.__repr__()


class unique_bidict(unique_dict):
    def __getitem__(self, key):
        if key in self._store:
            return self._store[key]
        elif key in self._inverted:
            return self._inverted[key]
        else:
            raise KeyError(key)


# get sardana element
# create between id and devices
# create a map between device and alias


def get_elements(instance, db):
    names = db.get_device_name("Pool/{}".format(instance), "*")
    return [name for name in names if 'dserver' not in name]


def get_ms_elements(instance, db):
    names = db.get_device_name("MacroServer/{}".format(instance), "*")
    return [name for name in names if 'dserver' not in name]

def generate_id_mapping(devices, db):
    id_map = unique_bidict()
    for name in devices:
        prop = db.get_device_property(name, 'id')['id']
        if not prop:
            continue
        id_map[prop[0]] = name
    return id_map


def generate_aliases_mapping(devices, db):
    alias_map = unique_bidict()
    for name in devices:
        try:
            alias = db.get_alias(name)
        except tango.DevFailed:
            continue
        alias_map[alias] = name
    return alias_map


def generate_instrument_list(pool, db):
    instr_list = []
    instr_prop = db.get_device_property(pool, "instrumentlist")["instrumentlist"]
    for n in range(0,len(instr_prop),3):
        instr_class = instr_prop[n]
        instr_name = instr_prop[n+1]
        instr_id = instr_prop[n+2]
        instr_list.append((instr_class, instr_name, instr_id))
    instr_list.sort(key=lambda a: a[2])
    return instr_list


def generate_instrument_mapping(instr_list):
    id_map = unique_bidict()
    for instr in instr_list:
        id_map[instr[2]] = instr[1]
    return id_map


def generate_prop_mapping(devices, db, prop_name):
    id_map = dict()
    for name in devices:
        prop = db.get_device_property(name, prop_name)[prop_name]
        if not prop:
            continue
        id_map[name] = prop
    return id_map



def generate_class_mapping(devices, db):
    return {d: db.get_class_for_device(d) for d in devices}


if __name__ == "__main__":
    db = tango.Database()
    elements = get_elements("Femtomax", db)
    aliases = generate_aliases_mapping(elements, db)
    ids = generate_id_mapping(elements, db)
    ctrl_ids = generate_prop_mapping(elements, db, 'ctrl_id')
    motor_ids = generate_prop_mapping(elements, db, 'motor_role_ids')
    pseudo_ids = generate_prop_mapping(elements, db, 'pseudo_motor_role_ids')
    import networkx as nx
    import matplotlib.pyplot as plt
    # import pydot
    G = nx.Graph()
    G.add_nodes_from(ids.values()
                     )

    def add_edge(iterable):
        for name, elems in iterable.items():
            for e in elems:
                G.add_edge(name, ids[e])
    add_edge(motor_ids)
    add_edge(pseudo_ids)
    add_edge(ctrl_ids)

    nx.draw(G, node_size=100, cmap=plt.cm.Blues,
            node_color=range(len(G)),
            prog='dot',
            with_labels=True)
