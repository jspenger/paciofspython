#!/bin/bash
################################################################################
# info
################################################################################
# uses: https://github.com/pjd/pjdfstest

################################################################################
# setup environment
################################################################################
trap "kill 0" EXIT
cd `dirname $0`

################################################################################
# run test
################################################################################
# reset test directory
rm -rf .testposix
mkdir .testposix
cd .testposix

# get and install posix testing suite: pjdfstest
git clone https://github.com/pjd/pjdfstest.git
pushd pjdfstest/
autoreconf -ifs
./configure
make pjdfstest
popd

echo paciofslocal
mkdir vol1
python ../../../paciofs/paciofslocal.py --mountpoint mnt1 --volume vol1 --logginglevel ERROR &
sleep 15
pushd mnt1
prove -rv ../pjdfstest/tests/ | tee ../test.paciofslocal.log
popd

echo passthroughfs
mkdir vol2
python ../../../paciofs/passthrough.py vol2 mnt2 &
sleep 15
pushd mnt2
prove -rv ../pjdfstest/tests/ | tee ../test.passthrough.log
popd

echo localfs
mkdir vol3
pushd vol3
prove -rv ../pjdfstest/tests/ | tee ../test.localfs.log
popd

exit
