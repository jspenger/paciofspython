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
# exit when any command fails
set -e

################################################################################
# run test
################################################################################
# reset test directory
rm -rf .testfio
mkdir .testfio
cd .testfio

echo paciofslocal
mkdir vol1
timeout 1m python3 ../../../paciofs/paciofslocal.py --mountpoint mnt1 --volume vol1 --logginglevel ERROR &
sleep 15
pushd mnt1
fio --name=test --bs=1K --size=10M --readwrite=randrw > ../test.paciofslocal.log
popd
umount mnt1

echo passthroughfs
mkdir vol2
timeout 1m python3 ../../../paciofs/passthrough.py vol2 mnt2 &
sleep 15
pushd mnt2
fio --name=test --bs=1K --size=10M --readwrite=randrw > ../test.passthrough.log
popd
umount mnt2

echo localfs
mkdir vol3
pushd vol3
fio --name=test --bs=1K --size=10M --readwrite=randrw > ../test.localfs.log
popd

exit
