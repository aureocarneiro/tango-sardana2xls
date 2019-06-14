from utils import get_elements, get_ms_elements, generate_aliases_mapping
from utils import generate_id_mapping, generate_prop_mapping
from utils import generate_class_mapping
from utils import generate_instrument_list, generate_instrument_mapping
import tango
import xlrd
from xlutils.copy import copy
import pprint
from functools import partial
import sys
import os
import argparse
import logging

# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

usage = "%prog [options] <pool_instance> "
parser = argparse(usage)
options, args = parser.parse_args()

if len(args) == 0:
    logging.fatal("You need to provide at least a pool instance")
    sys.exit()

db = tango.Database()

# Setup
pool = args[0]
pool_server = "Pool/{}".format(pool)
pool_name = db.get_device_name(pool_server, "Pool")[0]
logging.info("Pool: {}".format(pool))
logging.info("Server: {}".format(pool_server))
logging.info("Pool device: {}".format(pool_name))
ms_server = "MacroServer/{}".format(pool)
ms_name = db.get_device_name(ms_server, "MacroServer")[0]
logging.info("MacroServer: {}".format(ms_server))
logging.info("MacroServer device: {}".format(ms_name))

# Prepare environment
elements = get_elements(pool, db)
ms_elements = get_ms_elements(pool, db)
print("controller/endstationmanipulator/a_ea01_mpb_01_ctrl" in elements)
# Generate mapping
aliases = generate_aliases_mapping(elements, db)
ids = generate_id_mapping(elements, db)
ctrl_ids = generate_prop_mapping(elements, db, "ctrl_id")
motor_ids = generate_prop_mapping(elements, db, "motor_role_ids")
pseudo_ids = generate_prop_mapping(elements, db, "pseudo_motor_role_ids")
channel_ids = generate_prop_mapping(elements, db, "elements")
instrument_list = generate_instrument_list(pool_name, db)
instrument_ids = generate_instrument_mapping(instrument_list)


# Class mapping
classes = generate_class_mapping(elements, db)
classes_ms = generate_class_mapping(ms_elements, db)
print("controller/endstationmanipulator/a_ea01_mpb_01_ctrl" in classes)
controllers = [k for k, v in classes.items() if v.lower() == "controller"]
print("controller/endstationmanipulator/a_ea01_mpb_01_ctrl" in controllers)
motors = [k for k, v in classes.items() if v == "Motor"]
pseudos = [k for k, v in classes.items() if v == "PseudoMotor"]
iors = [k for k, v in classes.items() if v == "IORegister"]
measgrps = [k for k, v in classes.items() if v == "MeasurementGroup"]
macroservers = [k for k, v in classes_ms.items() if v == "MacroServer"]
doors = [k for k, v in classes_ms.items() if v == "Door"]
channels = [
    (k, v)
    for k, v in classes.items()
    if "counter" in v.lower() or "channel" in v.lower()
]


# Open xls file
module_path = os.path.dirname(os.path.realpath(__file__))
template_path = "{}/template/template.xls".format(module_path)
r_workbook = xlrd.open_workbook(template_path)
w_workbook = copy(r_workbook)
door_sheet = w_workbook.get_sheet(2)
controller_sheet = w_workbook.get_sheet(3)
motor_sheet = w_workbook.get_sheet(4)
pseudo_sheet = w_workbook.get_sheet(5)
servers_sheet = w_workbook.get_sheet(1)
global_sheet = w_workbook.get_sheet(0)
ior_sheet = w_workbook.get_sheet(6)
channel_sheet = w_workbook.get_sheet(7)
measurment_sheet = w_workbook.get_sheet(8)
acq_sheet = w_workbook.get_sheet(9)
instr_sheet = w_workbook.get_sheet(11)


default_properties = [
    "id",
    "ctrl_id",
    "motor_role_ids",
    "pseudo_motor_role_ids",
    "type",
    "library",
    "klass",
    "__SubDevices",
]

mot_attributes = [
    "EncoderSource",
    "EncoderSourceFormula",
    "Sign",
    "Offset",
    "Step_per_unit",
    "UserEncoderSource",
]

def get_property(ds, name):
    proplist = db.get_device_property(ds, name)[name]
    if len(proplist)>1:
        prop = '\\n'.join(proplist)
    else:
        prop = proplist[0]
    return prop


def get_property_list(name):
    return [
        p
        for p in db.get_device_property_list(name, "*")
        if p not in default_properties
    ]


def get_properties(name):
    props = get_property_list(name)
    return ["{}:{}".format(p, get_property(name, p)) for p in props]


def get_controller_elements(name, ctrl_type):
    elems = []
    if ctrl_type == "PseudoMotor":
        for motor in motor_ids[name]:
            try:
                elems.append(aliases[ids[motor]])
            except KeyError as e:
                print(e)
    return ";".join(elems)


def controller_data(name):
    ctrl_prop = partial(get_property, name)
    ctrl_type = ctrl_prop("type")
    ctrl_lib = ctrl_prop("library")
    ctrl_class = ctrl_prop("klass")
    ctrl_props = ";".join(get_properties(name))
    ctrl_elements = get_controller_elements(name, ctrl_type)
    #ctrl_device = name
    return [
        ctrl_type,
        pool_name,
        aliases[name],
        #ctrl_device,
        ctrl_lib,
        ctrl_class,
        ctrl_props,
        ctrl_elements,
    ]


def write_line(sheet, line, data):
    for index, d in enumerate(data):
        sheet.write(line, index, d)


def proceed_controllers(names, sheet):
    logging.info("Create controllers")
    ctrls = []
    for ctrl in names:
        logging.info("{}".format(ctrl))
        data = controller_data(ctrl)
        ctrls.append(data)
    ctrls = sorted(ctrls, key=lambda x: (x[0], x[2]))
    for line, data in enumerate(ctrls):
        write_line(sheet, line + 1, data)


def proceed_motors(names, sheet):
    logging.info("Create motors")
    motors = []
    for motor in names:
        data = motor_data(motor, "Motor")
        motors.append(data)
    motors = sorted(motors, key=lambda x: (x[2], int(x[5])))
    for line, data in enumerate(motors):
        write_line(sheet, line + 1, data)


def proceed_pseudos(names, sheet):
    logging.info("Create pseudo motors")
    pseudos = []
    for motor in names:
        data = motor_data(motor, "PseudoMotor")
        pseudos.append(data)
    pseudos = sorted(pseudos, key=lambda x: (x[2], int(x[5])))
    for line, data in enumerate(pseudos):
        write_line(sheet, line + 1, data)


def get_motor_attributes(name):
    tango_db = tango.DeviceProxy("sys/database/2")
    query = "Select attribute, value from property_attribute_device "
    query += "where device='{}' and name='__value'"
    query = query.format(name)
    reply = tango_db.DbMySqlSelect(query)
    reply = reply[1]
    if "DialPosition" in reply:
        idx = reply.index("DialPosition")
        del reply[idx:idx+2]
    if "PowerOn" in reply:
        idx = reply.index("PowerOn")
        del reply[idx:idx+2]
    answer = [
        "{}:{}".format(att, value)
        for att, value in zip(reply[::2], reply[1::2])
    ]
    return answer


def motor_data(name, mot_type):
    mot_type = mot_type
    mot_pool = pool_name

    mot_ctrl = aliases[ids[ctrl_ids[name][0]]]
    try:
        mot_alias = aliases[name]
    except KeyError:
        mot_alias = ""
    mot_device = name
    mot_axis = get_property(name, "Axis")
    try:
        mot_instr = get_property(name, "instrument_id")
        mot_instrument = instrument_ids[mot_instr]
    except:
        mot_instrument = ""
    mot_desc = ""
    mot_attributes = ";".join(get_motor_attributes(name))
    return (
        mot_type,
        mot_pool,
        mot_ctrl,
        mot_alias,
        mot_device,
        mot_axis,
        mot_instrument,
        mot_desc,
        mot_attributes,
    )


def ior_data(name):
    ior_ctrl = aliases[ids[ctrl_ids[name][0]]]
    ior_type = "IORegister"
    ior_pool = pool_name
    ior_alias = aliases[name]
    ior_name = name
    ior_axis = get_property(name, "Axis")
    try:
        ior_instr = get_property(name, "instrument_id")
        ior_instrument = instrument_ids[ior_instr]
    except:
        ior_instrument = ""
    ior_desc = ""
    ior_attributes = ";".join(get_motor_attributes(name))
    return (
        ior_type,
        ior_pool,
        ior_ctrl,
        ior_alias,
        ior_name,
        ior_axis,
        ior_instrument,
        ior_desc,
        ior_attributes,
    )


def proceed_iors(names, sheet):
    logging.info("Create ioregister")
    _iors = []
    for ior in names:
        data = ior_data(ior)
        _iors.append(data)
    _iors = sorted(_iors, key=lambda x: (x[2], x[5]))
    for line, data in enumerate(_iors):
        write_line(sheet, line + 1, data)


def channel_data(name, _type):
    channel_ctrl = aliases[ids[ctrl_ids[name][0]]]
    channel_type = _type
    channel_pool = pool_name
    channel_alias = aliases[name]
    channel_name = name
    channel_axis = get_property(name, "Axis")
    try:
        channel_instr = get_property(name, "instrument_id")
        channel_instrument = instrument_ids[channel_instr]
    except:
        channel_instrument = ""
    channel_desc = ""
    channel_attributes = ";".join(get_motor_attributes(name))
    return (
        channel_type,
        channel_pool,
        channel_ctrl,
        channel_alias,
        channel_name,
        channel_axis,
        channel_instrument,
        channel_desc,
        channel_attributes,
    )


def proceed_channel(names, sheet):
    logging.info("Create channels")
    _channels = []
    for channel, _type in names:
        data = channel_data(channel, _type)
        _channels.append(data)
    _channels = sorted(_channels, key=lambda x: (x[2], x[5]))
    for line, data in enumerate(_channels):
        write_line(sheet, line + 1, data)


def proceed_pool(name, sheet):
    # get_properties
    host = ":".join((db.get_db_host(), str(db.get_db_port())))
    pool_alias = db.get_alias_from_device(pool_name)
    prop = '\n'.join(db.get_device_property(pool_name, "PoolPath")["PoolPath"])
    line = (
        "Pool",
        host,
        pool_server,
        "",  # Description
        pool_alias,  # Alias
        pool_name,
        prop,
    )
    write_line(sheet, 1, line)


def proceed_macroserver(name, sheet):
    # get_properties
    host = ":".join((db.get_db_host(), str(db.get_db_port())))
    ms_alias = db.get_alias_from_device(ms_name)
    prop = '\n'.join(db.get_device_property(ms_name, "MacroPath")["MacroPath"])
    pools = '\n'.join(db.get_device_property(ms_name, "PoolNames")["PoolNames"])
    line = (
        "MacroServer",
        host,
        ms_server,
        "",  # Description
        ms_alias,  # Alias
        ms_name,
        prop,
        pools
    )
    write_line(sheet, 2, line)


def proceed_doors(names ,sheet):
    #Server	MacroServer	Description	name	tango name
    for line, name in enumerate(names):
        data = (
            ms_server,
            ms_name,
            "enter description",  # Sardana dsconfig doesnt like empty description
            db.get_alias_from_device(name),
            name
        )
        write_line(sheet, line+1, data)


def proceed_global(name, sheet):
    write_line(sheet, 0, ("code", pool))
    write_line(sheet, 1, ("name", pool))
    write_line(sheet, 2, ("description",))
    write_line(sheet, 3, ("",))
    write_line(sheet, 4, ("prefix", "p1"))

def proceed_measgrps(names, sheet):
    logging.info("Create measurement groups")
    _mgs = []
    for mg in names:
        data = mg_data(mg)
        _mgs.append(data)
    _mgs = sorted(_mgs, key=lambda x: (x[2], x[5]))
    for line, data in enumerate(_mgs):
        write_line(sheet, line + 1, data)

def mg_data(name):
    mg_type = "MeasurementGroup"
    mg_pool = pool_name
    mg_device = name
    mg_alias = aliases[name]
    mg_desc = ""
    mg_channels = get_mg_channels(name)

    return (
        mg_type,
        mg_pool,
        mg_alias,
        mg_device,
        mg_channels,
        mg_desc,
    )

def get_mg_channels(name):
    elems = []
    for chan in channel_ids[name]:
        try:
            elems.append(aliases[ids[chan]])
        except KeyError as e:
            print(e)
    return ";".join(elems)


def proceed_instruments(instr_list, sheet):
    logging.info("Create instruments")
    for line, data in enumerate(instr_list):
        instr_type = "Instrument"
        instr_pool = pool_name
        instr_name = data[1]
        instr_class = data[0]
        line_data = (instr_type, instr_pool, instr_name, instr_class)
        write_line(sheet, line + 1, line_data)


def main():

    proceed_motors(motors, motor_sheet)
    proceed_pseudos(pseudos, pseudo_sheet)
    proceed_controllers(controllers, controller_sheet)
    proceed_pool(pool_name, servers_sheet)
    proceed_macroserver(ms_name, servers_sheet)
    proceed_global(pool, global_sheet)
    proceed_iors(iors, ior_sheet)
    proceed_channel(channels, channel_sheet)
    proceed_measgrps(measgrps, acq_sheet)
    proceed_instruments(instrument_list, instr_sheet)
    proceed_doors(doors,door_sheet)

    w_workbook.save("{}/{}.xls".format(os.getcwd(), pool))

if __name__ == '__main__':
    main()
