#!/bin/bash
################################################################################
# info
################################################################################
# uses: iozone http://www.iozone.org/, install: brew install iozone (macOS)

################################################################################
# setup environment
################################################################################
trap "kill 0" EXIT
cd `dirname $0`

################################################################################
# run test
################################################################################
# reset test directory
rm -rf .testiozone
mkdir .testiozone
cd .testiozone

echo paciofslocal
mkdir vol1
python ../../../paciofs/paciofslocal.py --mountpoint mnt1 --volume vol1 --logginglevel ERROR &
sleep 15
pushd mnt1
iozone -a | tee ../test.paciofslocal.log
popd

echo passthroughfs
mkdir vol2
python ../../../paciofs/passthrough.py vol2 mnt2 &
sleep 15
pushd mnt2
iozone -a | tee ../test.passthrough.log
popd

echo localfs
mkdir vol3
pushd vol3
iozone -a | tee ../test.localfs.log
popd

exit
