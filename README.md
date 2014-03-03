rfinyl
======

Work in progress...

## Prerequisites:

* Install nfcy from its launchpad repo (instructions
[here](http://nfcpy.readthedocs.org/en/latest/topics/get-started.html)).

```
$ sudo apt-get install bzr
$ cd <somedir>
$ bzr branch lp:nfcpy
```

## Usage

* Optional: Add a udev rule so that you need not be root to run the script.
   I'm using a pn53x device connected via an FTDI USB-SERIAL board, so this is what my udev rule looks like (I am not going to go into how and where udev rules work - Google if you need):
```
 "UBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE=="0660", GROUP="plugdev"
```


