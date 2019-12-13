#!/bin/bash
################################################################################
# info
################################################################################
# uses: https://en.wikipedia.org/wiki/Bonnie%2B%2B

################################################################################
# setup environment
################################################################################
trap "kill 0" EXIT
cd `dirname $0`

################################################################################
# run test
################################################################################
# reset test directory
rm -rf .testbonnie
mkdir .testbonnie
cd .testbonnie

echo paciofslocal
mkdir vol1
python ../../../paciofs/paciofslocal.py --mountpoint mnt1 --volume vol1 --logginglevel ERROR &
sleep 15
pushd mnt1
bonnie++ | tee ../test.paciofslocal.log
popd

echo passthroughfs
mkdir vol2
python ../../../paciofs/passthrough.py vol2 mnt2 &
sleep 15
pushd mnt2
bonnie++ | tee ../test.passthrough.log
popd

echo localfs
mkdir vol3
pushd vol3
bonnie++ | tee ../test.localfs.log
popd

exit
