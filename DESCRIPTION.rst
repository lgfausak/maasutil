maasutil
========

|Package| |Build Status| |Coverage Status|

maas utility for a 1.8 maas region installation

Summary
-------

Provide misc command line stuff for maas. The first one I need is the
ability to determine the system\_id given the machine name.

Usage
-----

::

    usage: maasutil.py [-h] [-u URL] [-k KEY] [-f FILENAME] [-t TEMPLATE]
                       [-c COMMAND] [-v] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                       [-s]

    MaaS utility cli

    optional arguments:
      -h, --help            show this help message and exit
      -u URL, --url URL     This is the maas url to connect to, default :
                            http://localhost/MAAS/api/1.0
      -k KEY, --key KEY     This is the maas admin api key, default :null
      -f FILENAME, --file FILENAME
                            This is the jinja2 template file :
      -t TEMPLATE, --template TEMPLATE
                            This is the jinja2 template text :
      -c COMMAND, --command COMMAND
                            This is the maas uri, e.g. /nodes/?op=list :
      -v, --version         this switch will just return the version and exit,
                            current version is : 0.0.19
      -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            Log level (DEBUG,INFO,WARNING,ERROR,CRITICAL) default
                            is: INFO
      -s, --save            save select command line arguments (default is never)
                            in "/home/gfausak/.maasutil.conf" file

    -t or -f MUST be specified, not both.

Arguments
---------

-  --url, the url to connect to the MaaS server. If this is running on
   the same machine as the MaaS server, then the default
   'http://localhost/MAAS/api/1.0' will be sufficient.
-  --key, this can be found on the MaaS gui console, pulldown the right
   hand side, user account, that page contains keys. You can create new
   keys as well.
-  --command, The actual `MaaS
   api <https://maas.ubuntu.com/docs/api.html>`__ to execute. The
   command will return json, which is used by the template (so they must
   be paired).
-  --file, the file with the
   `jinja2 <http://jinja.pocoo.org/docs/dev/>`__ template in it. or..
-  --template, the actual `jinja2 <http://jinja.pocoo.org/docs/dev/>`__
   template text
-  --help, the usage message is printed.
-  --version, print the version and exit
-  --loglevel, for debugging, default INFO.
-  --save, save current arguments to persistent file in home directory,
   this file will be read as if it came from the command line in
   subsequent invocations of this program. To remove it you have to
   remove the ~/.maasutil.conf file manually. The default is no save is
   done. By the way, SAVE IS INSECURE! It can right the command line
   'KEY' to the file. You've been warned!

Rationale
---------

I needed a generic interface between the data that is returned by the
MaaS api, and Ansible. For example, there are a couple of things I want
to be able to do with Ansible. \* Dynamic inventory (from maas) \*
Deploy machines (from maas)

To implement these types of plays in Ansible, I need a simple way of
reaching into the MaaS api, prefereably on the command line, to access
from Ansible playbooks. Rather than writing one script for each piece of
data I needed, I decided to write a general REST api to template
program. The REST api must return json. The template is a jinja2
template which can take arbitrarily json and convert it to any format.
It can do filtering as well. So while this is written specifically for
MaaS, it will work with any REST interface that returns json.

Notes
-----

This uses the `jinja2 <http://jinja.pocoo.org/docs/dev/>`__ templating
system. The url/command that is run is expected to return json. Your
jinja2 template is expected to take that json as input, and format the
output accordingly. The template can be passed on the command line with
a -t argument, or, the template can be stored in a file, which is
referenced with a -f.

Installation
------------

The easiest way is to use pypi.

::

    pip install maasutil

Examples
--------

In most of the examples I leave off the --key argument. That argument
makes the command messy! To set arguments once, do something like this:

::

    maasutil --save --key 'FbVzEwU4sKaD68cadK:W7L9xm9LgycyfrmdYD:DbSW7fhnYMj4qtMxE5tzHUnw7AtAg5NM' --url 'http://www.myspecial.com/MAAS/api/1.0'

This will set the default --key and --url, so subsequent commands will
use those as if they were entered on the command line. This is pretty
handy when doing adhoc stuff, you don't have to keep retyping it.
However, it is insecure. The key is written to a file in the home
directory of the executor, in a file called .maasutil.conf. It is a good
idea to erase this file when you are done messing around.

Show the hostname, systemid and status

::

    maasutil --command '/nodes/?op=list' --template '{% for h in src %}{{ h.hostname }}, {{ h.system_id }}, {{ h.status }}^M{% endfor %}'

and an example result:

::

    hp-bottom.maas, node-01077d56-4cb9-11e5-ab4d-0800274e4167, 4
    hp-top.maas, node-9d269970-4ff6-11e5-8444-0800274e4167, 4
    hp-right.maas, node-3b57d712-4ff7-11e5-8444-0800274e4167, 6
    hp-left.maas, node-3eb98f90-4ff7-11e5-8c49-0800274e4167, 4

You will need to know the json that is returned by the command. The
`MaaS api <https://maas.ubuntu.com/docs/api.html>`__ documentation will
help with that. Just for completeness I will show what the command above
returns, so the template will make a little more sense. This is a very
basic example, the templates can gete arbitrarily complex.

::

    [
        {
            "ip_addresses": [
                "10.20.30.54"
            ],
            "cpu_count": 8,
            "power_type": "amt",
            "tag_names": [
                "juju2"
            ],
            "swap_size": null,
            "owner": null,
            "macaddress_set": [
                {
                    "resource_uri": "/MAAS/api/1.0/nodes/node-01077d56-4cb9-11e5-ab4d-0800274e4167/macs/cc%3A3d%3A82%3A67%3Afe%3A3f/",
                    "mac_address": "cc:3d:82:67:fe:3f"
                },
                {
                    "resource_uri": "/MAAS/api/1.0/nodes/node-01077d56-4cb9-11e5-ab4d-0800274e4167/macs/ec%3Ab1%3Ad7%3A46%3Ad7%3Afb/",
                    "mac_address": "ec:b1:d7:46:d7:fb"
                }
            ],
            "zone": {
                "resource_uri": "/MAAS/api/1.0/zones/default/",
                "name": "default",
                "description": ""
            },
            "hostname": "hp-bottom.maas",
            "storage": 500107,
            "system_id": "node-01077d56-4cb9-11e5-ab4d-0800274e4167",
            "boot_type": "fastpath",
            "memory": 16384,
            "disable_ipv4": false,
            "status": 4,
            "power_state": "off",
            "routers": [],
            "physicalblockdevice_set": [
                {
                    "name": "sda",
                    "tags": [
                        "rotary",
                        "sata",
                        "7200rpm"
                    ],
                    "id": 20,
                    "id_path": "/dev/disk/by-id/wwn-0x5000cca85ec51c83",
                    "path": "/dev/sda",
                    "model": "HGST HTS725050A7",
                    "block_size": 4096,
                    "serial": "RC250ACE0B7KTM",
                    "size": 500107862016
                }
            ],
            "pxe_mac": {
                "resource_uri": "/MAAS/api/1.0/nodes/node-01077d56-4cb9-11e5-ab4d-0800274e4167/macs/ec%3Ab1%3Ad7%3A46%3Ad7%3Afb/",
                "mac_address": "ec:b1:d7:46:d7:fb"
            },
            "netboot": true,
            "osystem": "",
            "substatus": 4,
            "architecture": "amd64/generic",
            "distro_series": "",
            "resource_uri": "/MAAS/api/1.0/nodes/node-01077d56-4cb9-11e5-ab4d-0800274e4167/"
        },
        ...and this repeats for each one...
    ]

.. |Package| image:: https://badge.fury.io/py/maasutil.svg
   :target: https://pypi.python.org/pypi/maasutil
.. |Build Status| image:: https://travis-ci.org/lgfausak/maasutil.svg?branch=master
   :target: https://travis-ci.org/lgfausak/maasutil
.. |Coverage Status| image:: https://coveralls.io/repos/lgfausak/maasutil/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/lgfausak/maasutil?branch=master
