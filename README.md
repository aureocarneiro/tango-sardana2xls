# tango-sardana2xls

Tool to generate a xls representation of an existing [Tango](https://github.com/tango-controls/pytango.git) [Sardana](https://github.com/sardana-org/sardana) environment

## Usage

With the current tango host
```bash
python sardana2xls/main.py {Pool instance name}
```

With a different tango host
```bash
TANGO_HOST=your_tango_db_host:your_tango_db_port python sardana2xls/main.py {Pool instance name}
```

## Todo
 - Requierment
 - CLI
 - Test
 - Parameters
 
 
