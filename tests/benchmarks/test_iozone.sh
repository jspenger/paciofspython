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
set -e  # exit when any command fails

################################################################################
# run test
################################################################################
# reset test directory
rm -rf .testiozone
mkdir .testiozone
cd .testiozone

echo paciofslocal
mkdir vol1
mkdir mnt1
timeout 5m python3 ../../../paciofs/paciofslocal.py --logginglevel=ERROR --paciofslocal-mountpoint=mnt1 --paciofs-fileservervolume=vol1 --paciofs-volume=vol1 fotb --multichain-create=True &
sleep 15
cd mnt1
iozone -a | tee ../test.paciofslocal.log
cd ..
umount mnt1

echo passthroughfs
mkdir vol2
mkdir mnt2
timeout 5m python3 ../../../paciofs/passthrough.py vol2 mnt2 &
sleep 15
cd mnt2
iozone -a | tee ../test.passthrough.log
cd ..
umount mnt2

echo localfs
mkdir vol3
cd vol3
iozone -a | tee ../test.localfs.log
cd ..

exit
