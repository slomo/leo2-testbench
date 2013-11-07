Testbench for the LEO-II prover
===============================


All configurations for testruns can be found in the configs direcotry.
They were used to create the runs on the testsystem, for which the
results reside in the subfolder remoteruns.

A config can be started via the test.sh command, it will install all
needed provers in this directory. The versions needed are preinstalled
in this folder, to make it easier to reproduce the work.

Plots are created via the plots/extract.py script (except for the sankey
diagramm, which was done by using the d3.js framewokr). Before plotting
the tptp overview file needs to be created. This is done by the following
command:

    find TPTP-v5.5.0/Problems -iname "*\^?.p" -exec sh -c 'echo -n "$(basename {}), ";  sed -n "s/^% Status   : \(\w\+\)$/\1/p" {}'   \; > TPTP-v5.5.0/higherOrderStatus.csv

Everthing is provided as free software under the 2-clause BSD License,
except for the LEO-II prover itself and all other provers (SPASS, VAMPIRE, E)
