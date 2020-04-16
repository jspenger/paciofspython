# PacioFS Python

[![Build Status](https://travis-ci.com/jonasspenger/paciofspython.svg?branch=master)](https://travis-ci.com/jonasspenger/paciofspython)

PacioFS is a tamper-proof file system under development at the Zuse Institute Berlin (https://www.zib.de/projects/pacio) (PacioFS java / C++, https://github.com/paciofs/paciofs).

We aim to design a distributed file system for the digital archival of financial documents compliant to German regulations.

## Current Status and Roadmap:
This repository is a prototype under development and should not be used in deployment.
- [x] tamper-proof: any participant can detect unauthorized changes to the file system
- [x] multi-user: multiple users can concurrently use the system
- [x] multi-volume: supports multiple volumes
- [x] permissioned access / group membership: dynamic groups (join, leave) and permissioned (voteaccept, votekick)
- [ ] complete version history: the entire file-history is accessible
- [ ] fault-tolerant: data is protected against loss
- [ ] distributed, scalable, low latency, high throughput, etc.
- [ ] test and clean

## Docker Installation
The recommended way to install PacioFS Python is via Docker.
To build the docker image, see [deployment/docker/README.md](deployment/docker/README.md).

Alternatively, use the pre-built image from docker hub at jonasspenger/paciofspython.

## Example
Run the image locally, using privileged (at your own risk) to enable mounting FUSE locally. This allows the container to have root capabilities on the host machine.
```
docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  /bin/ash;
```
It is convenient to run the image locally and execute a benchmark:
```
docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  sh paciofspython/tests/benchmarks/test_fio.sh;
```
Or, to run the unit tests and integration tests.
```
docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  python3 -m unittest discover paciofspython/tests/unittests -v;
```
```
docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  python3 -m unittest discover paciofspython/tests/integrationtests -v;
```
For an example of the outputs please refer to the latest build at [https://travis-ci.com/jonasspenger/paciofspython](https://travis-ci.com/jonasspenger/paciofspython).


## Local Installation
- Multichain:
   - (Linux) Install multichain (https://www.multichain.com/, https://www.multichain.com/download-community/):
   ```
   cd /tmp
   wget https://www.multichain.com/download/multichain-2.0.6.tar.gz
   tar -xvzf multichain-2.0.6.tar.gz
   ```

   Move to bin folder: `cd multichain-2.0-release && mv multichaind multichain-cli multichain-util multichaind-cold /usr/local/bin;`

   - (macOS) Install multichain (https://github.com/paciofs/multichain/releases/tag/2.0-dev-20190915T142420)

   Move to bin folder: `mv multichaind multichain-cli multichain-util multichaind-cold /usr/local/bin`
   Or, add to path: `export PATH=$PATH:XXX/multichain-2.0-dev/`
   If you get message: `dyld: Library not loaded`, try reinstalling openssl: `brew reinstall https://github.com/tebelorg/Tump/releases/download/v1.0.0/openssl.rb` or `brew reinstall openssl`
- Python:
   - Install the required python3 packages: `pip3 install -r requirements.txt`

## Usage
Run PacioFS on local machine, mounting directory `mnt` to `vol`, using FIFO-order tamper-proof broadcast protocol (and creating a local multichain instance):
```
python3 paciofs/paciofslocal.py --logginglevel=DEBUG --paciofslocal-mountpoint mnt --paciofs-volume vol --paciofs-fileservervolume vol fotb --multichain-create=True
```

Example usage:
```
timeout 1m python3 paciofs/paciofslocal.py --logginglevel=DEBUG --paciofslocal-mountpoint mnt --paciofs-volume vol --paciofs-fileservervolume vol fotb --multichain-create=True &
sleep 15
cd mnt
echo hello > world.txt
ls
cat world.txt
cd ..
umount mnt
```

Run PacioFS as a client and server, mounting `mnt` on client to `vol` on server, connecting to server host `localhost` and port `8765`:
```
python3 paciofs/paciofsserver.py --logginglevel=DEBUG --paciofs-volume vol --paciofs-fileservervolume vol --paciofsserver-host localhost --paciofsserver-port 8765 fotb --multichain-create=True
python3 paciofs/paciofsclient.py --logginglevel=DEBUG --paciofsclient-mountpoint mnt --paciofsclient-host localhost --paciofsclient-port 8765
```

Run PacioFS connecting to existing blockchain at address `chainname@host:port`, for example `chain@127.0.0.1:8765`:
```
python3 paciofs/paciofslocal.py --logginglevel=DEBUG fotb --multichain-chainname chain@127.0.0.1:8765;
```

To show the help message, and for more information on settings, set `-h` as an argument.
```
python3 paciofs/paciofslocal.py -h
python3 paciofs/paciofslocal.py fotb -h
python3 paciofs/paciofslocal.py totb -h
python3 paciofs/paciofslocal.py htlltb -h
python3 paciofs/paciofslocal.py htlltbtest -h
python3 paciofs/paciofsserver.py -h
python3 paciofs/paciofsclient.py -h
```

## Tests and Benchmarks
Run all unit tests:
```
python3 -m unittest discover tests/unittests -v
```

Run all integration tests:
```
python3 -m unittest discover tests/integrationtests -v
```

Run specific test:
```
python3 -m unittest tests.integrationtests.test_blockchain -v
python3 -m unittest tests.integrationtests.test_paciofs -v
python3 -m unittest tests.integrationtests.test_paciofslocal -v
python3 -m unittest tests.integrationtests.test_tamperproofbroadcast -v
python3 -m unittest tests.unittests.test_blockchain -v
python3 -m unittest tests.unittests.test_kvstore -v
python3 -m unittest tests.unittests.test_paciofs -v

```

Run all benchmarks:
```
sh tests/benchmarks/test_fio.sh
```

Benchmarks currently not supported by PacioFS:
```
sh tests/benchmarks/test_posix.sh
sh tests/benchmarks/test_bonnie.sh
sh tests/benchmarks/test_iozone.sh
```

## PacioFS Design
The architecture consists of three layers.
```
               PacioFS
                  ^
Reliable FIFO-Order Tamper-Proof Broadcast
                  ^
              Blockchain
```
The file system (PacioFS) communicates state-changes via the broadcast module.
The broadcast module ensures both the reliable and FIFO-order delivery, and uses the blockchain to achieve tamper-proof communication and communication history.

Currently, PacioFS uses the local file system for management of the file system, and the broadcast for tamper-proof communication of the state changes.

```
============================================================
PacioFS
============================================================
Implements: Tamper-Proof File System, instance fs

Uses:
- Reliable FIFO-Order Tamper-Proof Broadcast, instance bc
- Disk (local file system), instance disk

upon event < fs, Init | volume > do
  this.volume = volume
  servers = { }  // set of permissioned servers: pid
  map = { }  // map: obfuscated_msg -> msg
  log = [ ]  // list: pid, epoch, txid, obfuscated_msg, msg
  trigger < bc, Broadcast | "JOIN", this.volume >

upon event < fs, FSAPI-* | arg1, arg2, ... > do
  returnvalue = disk.*( arg1, arg2, ... )
  if * changes state do
    msg = ( *, arg1, arg2, ... )
    obfuscated_msg = obfuscate( msg )
    map[ obfuscated_msg ] = msg
    trigger < bc, Broadcast | obfuscated_msg >
  trigger < fs, FSAPI-*-Return | returnvalue >

upon event < bc, Deliver | pid, epoch, txid, msg > and msg = "JOIN", volume do
  if volume is this.volume do
    if accept( join_pid ) do
      trigger < bc, Broadcast | "VOTEACCEPT", pid, volume >

upon event < bc, Deliver | pid, epoch, txid, msg > and msg = "LEAVE", volume do
  if volume is this.volume do
    trigger < bc, Broadcast | "VOTEKICK", pid, volume >

upon event < bc, Deliver | pid, epoch, txid, msg > and msg = "VOTEACCEPT", vote_pid, volume do
  if volume is this.volume do
    if pid in servers or servers is empty do
      servers = servers \/ { vote_pid }  // add pid to accepted servers

upon event < bc, Deliver | pid, epoch, txid, msg > and msg = "VOTEKICK", vote_pid, volume do
  if volume is this.volume do
    if pid in servers do
      servers = servers \ { vote_pid }  // remove pid from accepted servers

upon event < bc, Deliver | pid, epoch, txid, msg > do
  if pid in servers and pid is this.pid do  // if I broadcast message
    unobfuscated_msg = map[ msg ]
    log.append( pid, txid, msg, unobfuscated_msg )

  else if pid is in servers  // if message from other known server
    repeat until success  // success if get unobfuscated_msg from remote server
      random_pid = random_choice( servers )  // randomly choose a server
      unobfuscated_msg = remote_get(pid, msg)  // get unobfuscated msg from remote server
      if random_pid not responsive or unobfuscated_msg is not obfuscate(msg) do
        trigger < bc, Broadcast | "VOTEKICK", random_pid, this.volume >
    log.append( pid, txid, msg, unobfuscatedmsg )

upon event < fs, AuAPI-1 > do  // auditing API-1: verify integrity of file system
  verify( disk, log )

Footnotes:
- obfuscate: pseudo-anonymize data (salt hash data)
- verify: check if disk is consistent with the tamper-proof records found in log
- pid: signature public key
- epoch: block number
- txid: transaction id
- 'this' syntax similar to C++, e.g. this.x retrieves the object instance variable x
- accept: function that accepts (returning true) or rejects (returning false) a new pid
- voteaccept, votekick: 1 vote from permissioned node is enough to accept or kick
```

## Development
- Format source code: `black *`
- Generate requirements: `pipreqs . --force`
