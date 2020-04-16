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
set -e  # exit when any command fails

################################################################################
# run test
################################################################################
# reset test directory
rm -rf .testposix
mkdir .testposix
cd .testposix

# get and install posix testing suite: pjdfstest
git clone https://github.com/pjd/pjdfstest.git
cd pjdfstest/
autoreconf -ifs
./configure
make pjdfstest
cd ..

echo paciofslocal
mkdir vol1
mkdir mnt1
timeout 1h python3 ../../../paciofs/paciofslocal.py --logginglevel=ERROR --paciofslocal-mountpoint=mnt1 --paciofs-fileservervolume=vol1 --paciofs-volume=vol1 fotb --multichain-create=True &
sleep 15
cd mnt1
prove -rv ../pjdfstest/tests/ | tee ../test.paciofslocal.log
cd ..
umount mnt1

echo passthroughfs
mkdir vol2
mkdir mnt2
timeout 1h python3 ../../../paciofs/passthrough.py vol2 mnt2 &
sleep 15
cd mnt2
prove -rv ../pjdfstest/tests/ | tee ../test.passthrough.log
cd ..
umount mnt2

echo localfs
mkdir vol3
cd vol3
prove -rv ../pjdfstest/tests/ | tee ../test.localfs.log
cd ..

exit
