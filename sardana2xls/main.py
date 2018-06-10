from utils import get_elements, generate_aliases_mapping
from utils import generate_id_mapping, generate_prop_mapping
from utils import generate_class_mapping
import tango
import xlrd
from xlutils.copy import copy
from functools import partial

pool = "FlexPes"
db = tango.Database()
elements = get_elements(pool, db)
print(elements)
aliases = generate_aliases_mapping(elements, db)
ids = generate_id_mapping(elements, db)
ctrl_ids = generate_prop_mapping(elements, db, 'ctrl_id')
motor_ids = generate_prop_mapping(elements, db, 'motor_role_ids')
pseudo_ids = generate_prop_mapping(elements, db, 'pseudo_motor_role_ids')
classes = generate_class_mapping(elements, db)


r_workbook = xlrd.open_workbook("template.xls")
w_workbook = copy(r_workbook)
controllers = [k for k, v in classes.iteritems() if v == "Controller"]
motors = [k for k, v in classes.iteritems() if v == "Motor"]
pseudos = [k for k, v in classes.iteritems() if v == "PseudoMotor"]
pool_name = "flexpes/pool/01"
pool_server = "Pool/FlexPes"
controller_sheet = w_workbook.get_sheet(3)
motor_sheet = w_workbook.get_sheet(4)
pseudo_sheet = w_workbook.get_sheet(5)
pool_sheet = w_workbook.get_sheet(1)
global_sheet = w_workbook.get_sheet(0)


default_properties = [
    "id",
    "ctrl_id",
    "motor_role_ids",
    "pseudo_motor_role_ids",
    "type",
    "library",
    "klass"]


def get_property(ds, name):
    return db.get_device_property(ds, name)[name][0]


def get_property_list(name):
    return [p for p in db.get_device_property_list(name, "*")
            if p not in default_properties]


def get_properties(name):
    props = get_property_list(name)
    return ["{}:{}".format(p, get_property(name, p)) for p in props]


def get_controller_elements(name, ctrl_type):
    elems = []
    if ctrl_type == "PseudoMotor":
        for pseudo in pseudo_ids[name]:
            try:
                elems.append(aliases[ids[pseudo]])
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
    return [ctrl_type,
            pool_name,
            aliases[name],
            ctrl_lib, ctrl_class,
            ctrl_props,
            ctrl_elements]


def write_line(sheet, line, data):
    for index, d in enumerate(data):
        sheet.write(line, index, d)


def proceed_controllers(names, sheet):
    for line, controller in enumerate(names):
        data = controller_data(controller)
        write_line(sheet, line+1, data)


def proceed_motors(names, sheet):
    for line, motor in enumerate(names):
        data = motor_data(motor, "Motor")
        write_line(sheet, line+1, data)


def proceed_pseudos(names, sheet):
    for line, motor in enumerate(names):
        data = motor_data(motor, "PseudoMotor")
        write_line(sheet, line+1, data)


mot_attributes = [
    "EncoderSource",
    "EncoderSourceFormula",
    "Sign",
    "Offset",
    "Step_per_unit",
    "UserEncoderSource"]


def get_motor_attributes(name):
    tango_db = tango.DeviceProxy("sys/database/2")
    query = "Select attribute, value from property_attribute_device "
    query += "where device='{}' and name='__value'"
    query = query.format(name)
    reply = tango_db.DbMySqlSelect(query)
    reply = reply[1]
    answer = ["{}:{}".format(att, value)
              for att, value in zip(reply[::2], reply[1::2])]
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
    mot_instrument = ""
    mot_desc = ""
    mot_attributes = ";".join(get_motor_attributes(name))
    return (mot_type,
            mot_pool,
            mot_ctrl,
            mot_alias,
            mot_device,
            mot_axis,
            mot_instrument,
            mot_desc,
            mot_attributes)


def proceed_pool(name, sheet):
    # get_properties
    host = ":".join((db.get_db_host(), str(db.get_db_port())))
    pool_alias = db.get_alias_from_device(pool_name)
    prop = str(db.get_device_property(pool_name, "PoolPath")["PoolPath"])
    line = ("Pool",
            host,
            pool_server,
            '',      # Description
            pool_alias,   # Alias
            pool_name,
            prop)
    write_line(sheet, 1, line)


def proceed_global(name, sheet):
    write_line(sheet, 0, ("code", pool))
    write_line(sheet, 1, ("name", pool))
    write_line(sheet, 2, ("description",))
    write_line(sheet, 3, ("",))
    write_line(sheet, 4, ("prefix", "p1"))

proceed_motors(motors, motor_sheet)
proceed_pseudos(pseudos, pseudo_sheet)
proceed_controllers(controllers, controller_sheet)
proceed_pool(pool_name, pool_sheet)
proceed_global(pool, global_sheet)

w_workbook.save("template2.xls")
