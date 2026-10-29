===============
Labgrid for SGL
===============

Overview
========

We want to run the CI built images on real hardware automatically. 
For this purpose we want to use labgrid.


Architecture
============

labgrid-client -> labgrid-coordinator -> labgrid-exporter -> "Device under test"


The beagleV-Fire gets power via USB-C, the same interface is used to flash the
internal eMMC. To power cycle the board from remote a controllable USB-Hub is
used, here the Yepkit Yepkit USB Switchable Hub (in short YKUSH).

To get acces to the serial console a USB-UART cable is used.



Hardware setup
==============

Install necessary software
--------------------------

On a basic Debian Trixie installation add the trixie-backports repository for labgrid packages.

Add a new file /etc/apt/sources.list.d/debian-backports.sources:

::

  Types: deb deb-src
  URIs: http://deb.debian.org/debian
  Suites: trixie-backports
  Components: main
  Enabled: yes
  Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Run "apt update" 

For now we install all labgrid parts on one machine.
Install the labgrid packages and, for debugging purposes, picocom and the control application for YKUSH

::

  sudo apt install labgrid-coordinator labgrid-client labgrid-exporter labgrid-utils python3-labgrid picocom ykush-control


After installation the labgrid-coordinator is started automatically. We can use
the labgrid-client to communicate with the coordinator. As we didn't defined
places or resoources yet, the output is empty.

::

  labgrid-client resources
  labgrid-client places

TODO: Configure SSH


Configure labgrid-exporter
--------------------------

The labgrid-exporter is the software that controls all the hardware resources.
To configure the exporter, resource groups need to be defined containing one or more resources.

https://labgrid.readthedocs.io/en/latest/configuration.html#exporter-configuration
Labgrid Tutorial #1 - Setup & CLI : https://www.youtube.com/watch?v=In_mOO35V7c

Disconnect all usb devices (ykush, usb serial cables). We will run the tool
labgrid-suggest to help us to find the right usb-path for the exporter
configuration. 

::

  labgrid-suggest

Now use one usb device (eg. USB thumb drive) to discover the usb id path for
each USB port in the system (or on the usb hub). 

The output of labgrid-suggest per attached device looks something like this:

::

  === added device ===
  USBSerialPort for /devices/pci0000:00/0000:00:14.0/usb1/1-3/1-3:1.0/ttyUSB0/tty/ttyUSB0
  === device properties ===
  device node: /dev/ttyUSB0
  udev tags: systemd
  vendor: Prolific_Technology_Inc.
  vendor (DB): Prolific Technology, Inc.
  model: USB-Serial_Controller
  model (DB): PL2303 Serial Port / Mobile Phone Data Cable
  revision: 0300
  === suggested matches ===
  USBSerialPort:
    match:
      ID_PATH: pci-0000:00:14.0-usb-0:3:1.0
  ---


The ID_PATH for all USB ports on this HP Prodesk device here it looks like this:

USB port location

================= ============================
back side port 1: pci-0000:00:14.0-usb-0:1:1.0
back side port 2: pci-0000:00:14.0-usb-0:2:1.0
back side port 3: pci-0000:00:14.0-usb-0:4:1.0
back side port 4: pci-0000:00:14.0-usb-0:5:1.0
front left port : pci-0000:00:14.0-usb-0:13:1.0
front right port: pci-0000:00:14.0-usb-0:3:1.0
================= ============================



When all ID_PATH values for the USB ports are collected, 
create the configuration file /etc/labgrid/labgrid-exporter.yaml


::
  
  {% for index, id_path in [
    ('1', 'pci-0000:00:14.0-usb-0:1:1.0'),
    ('2', 'pci-0000:00:14.0-usb-0:2:1.0'),
    ('3', 'pci-0000:00:14.0-usb-0:4:1.0'),
    ('4', 'pci-0000:00:14.0-usb-0:5:1.0'),
    ('left', 'pci-0000:00:14.0-usb-0:13:1.0'),
    ('right', 'pci-0000:00:14.0-usb-0:3:1.0')] %}


    usb-port{{index}}:
      USBSerialPort:
        match:
          '@ID_PATH': '{{id_path}}'

  {% endfor %}

Attach a usb serial cable to the system and start the labgrid-exporter

::

  sudo systemctl start labgrid-exporter


Now the labgrid-client should list the attached resource::

  labgrid-client resources



Connect the YKUSH to a USB port. Use "ykushcmd -l" to obtain the YKUSH board
serial number. The YKUSH has three controllable USB ports.

Add this config snippet to the exporter.yaml:

::

  {% for num in range(1,4) %}
    YKUSHPowerPort-{{num}}:
      YKUSHPowerPort:
        serial: 'Y3N12345'
        index: {{num}}
  {% endfor %}

After a "systemctl restart labgrid-exporter" the labgrid-client will show more resources:

::

  ~# labgrid-client resources
  prodesk/YKUSHPowerPort-1/NetworkYKUSHPowerPort
  prodesk/YKUSHPowerPort-2/NetworkYKUSHPowerPort
  prodesk/YKUSHPowerPort-3/NetworkYKUSHPowerPort
  prodesk/usb-port1/NetworkSerialPort
  prodesk/usb-portright/NetworkSerialPort
  ~# 


Add a place / a.k.a. device under test
--------------------------------------

Create a place that uses resources to control a device under test. 

Using labgrid-client:  

::

  labgrid-client --place beaglev-fire-1 create


Now we add resources. Knowing that the board named "beaglev-fire-1" is attached to the YKUSH port 1 and connected with the usb-serial adapter in the USB port 1 we add these resources to the place:

::

  labgrid-client --place beaglev-fire-1 add-match prodesk/YKUSHPowerPort-1/NetworkYKUSHPowerPort
  labgrid-client --place beaglev-fire-1 add-match prodesk/usb-port1/NetworkSerialPort

Now labgrid-client shows the fresh created place::

  labgrid-client places
  labgrid-client --place beaglev-fire-1 show
  
  # power on / off / cycle
  labgrid-client --place beaglev-fire-1 power cycle

  # serial console (to exit ctrl + \ then enter "quit"
  labgrid-client --place beaglev-fire-1 console

