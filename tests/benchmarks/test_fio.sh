#!/bin/bash
################################################################################
# info
################################################################################
# uses: https://fio.readthedocs.io/en/latest/fio_doc.html

################################################################################
# setup environment
################################################################################
trap "kill 0" EXIT
cd `dirname $0`

################################################################################
# run test
################################################################################
# reset test directory
rm -rf .testfio
mkdir .testfio
cd .testfio

echo paciofslocal
mkdir vol1
python ../../../paciofs/paciofslocal.py --mountpoint mnt1 --volume vol1 --logginglevel ERROR &
sleep 15
pushd mnt1
fio --name=test --bs=1K --size=10M --readwrite=randrw > ../test.paciofslocal.log
popd

echo passthroughfs
mkdir vol2
python ../../../paciofs/passthrough.py vol2 mnt2 &
sleep 15
pushd mnt2
fio --name=test --bs=1K --size=10M --readwrite=randrw > ../test.passthrough.log
popd

echo localfs
mkdir vol3
pushd vol3
fio --name=test --bs=1K --size=10M --readwrite=randrw > ../test.localfs.log
popd

exit
