# Network Simulator
This repository contains our team's network simulator code for CS 143 (a Caltech class).

Team members: Laksh Bhasin, David Luo, Yubo Su, Sharon Yang.

IDE (PyCharm 4.5)
===
The code is written using Python 2.7.10. Our developers use PyCharm 4.5 as
their IDE.

Download the "Community" version here:
```
https://www.jetbrains.com/pycharm/download/
```

Dependencies
===
To use the package network_simulator, the following dependencies need to
be installed (via pip for Python 2).

- jsonpickle
- numpy

Usage
===
Run initializer.py (or read the file) to see example usage. One method of
example usage is included below:
```
python2 initializer.py -v INFO -f stdout data/test_case_0_fast.json
```

This will run the simulator with verbosity level "INFO", and output any logs
directly to stdout (alternatively, a file can be specified as part of the
"-f" optional parameter). The JSON file "data/test_case_0_fast.json" wraps a
NetworkTopology that describes Test Case 0 with TCP FAST used for Flows. See
the other JSON files in the data/ folder for more options.
