# PacioFS Python
PacioFS is a tamper-proof file system under development at the Zuse Institute Berlin (https://www.zib.de/projects/pacio) (PacioFS java / C++, https://github.com/paciofs/paciofs).

We aim to design a distributed file system for the digital archival of financial documents, compliant to German regulations.

## Current Status and Roadmap:
- [x] tamper-proof: any participant can detect unauthorized changes to the file system
- [ ] multi-user: multiple users can concurrently use the system
- [ ] multi-volume: supports multiple volumes
- [ ] complete version history: the entire file-history is accessible
- [ ] fault-tolerant: data is protected against loss
- [ ] distributed, scalable, low latency

## Installation
- Multichain:
   - Install multichain (https://www.multichain.com/)
   - Add multichain to path: `export PATH=$PATH:/usr/local/multichain-2.0-release`
- Python:
   - Install the required python packages: `pip install -r requirements.txt`

## Usage
Run PacioFS on local machine, mounting directory `mnt` to `vol`:
```
python paciofs/paciofslocal.py --mountpoint mnt --volume vol
```

Run PacioFS as a client and server, mounting `mnt` on client to `vol` on server, connecting to server host `localhost` and port `8765`:
```
python paciofs/paciofsserver.py --volume vol --host localhost --port 8765
python paciofs/paciofsclient.py --mountpoint mnt --host localhost --port 8765
```

Run PacioFS connecting to existing blockchain at address `chainname@host:port`, for example `chain@127.0.0.1:8765`:
```
python paciofs/paciofslocal.py --chainname chain@127.0.0.1:8765
```

To show the help message, and for more information on settings, set `-h` as an argument.
```
python paciofs/paciofslocal.py -h
python paciofs/paciofsserver.py -h
python paciofs/paciofsclient.py -h
```

## Tests and Benchmarks
Run all unit tests:
```
python -m unittest discover tests/unittests -v
```

Run all integration tests:
```
python -m unittest discover tests/integrationtests -v
```

Run specific test:
```
python -m unittest tests.integrationtests.test_tamperproofbroadcast -v
python -m unittest tests.integrationtests.test_tamperproofbroadcast.TestTamperProofBroadcast.test_validity -v
```

Run all benchmarks:
```
sh tests/benchmarks/test_bonnie.sh
sh tests/benchmarks/test_fio.sh
sh tests/benchmarks/test_iozone.sh
sh tests/benchmarks/test_posix.sh
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

upon event < fs, Init > do
  servers = { } // map: pid -> host:port
  tmp_log = { }  // map: obfuscated_msg -> msg
  log = [ ]  // list: pid, epoch, txid, obfuscated_msg, msg

upon event < fs, FSAPI-* | arg1, arg2, ... > do
  returnvalue = disk.*( arg1, arg2, ... )
  if * changes state do
    msg = ( *, arg1, arg2, ... )
    obfuscated_msg = obfuscate( msg )
    tmp_log.append( obfuscated_msg, msg )
    trigger < bc, Broadcast | obfuscated_msg >
  trigger < fs, FSAPI-*-Return | returnvalue >

upon event < bc, Deliver | pid, epoch, txid, msg > and msg = "join", pid, host:port do
  servers.add( pid -> host:port )

upon event < bc, Deliver | pid, epoch, txid, msg > do
  if pid is my pid do  // if I broadcast message
    unobfuscated_msg = tmp_log[ msg ]
    log.append( pid, txid, msg, unobfuscated_msg )
    tmp_log.remove( msg )
  if pid is in servers do
    repeat do
      pid, host:port = random_choice( servers )
      pid.

// auditing API-1: verify integrity of file system
upon event < fs, AuAPI-1 > do
  verify( disk, log )

Footnotes:
- obfuscate: pseudo-anonymize data (salt hash data)
- verify: check if disk is consistent with the tamper-proof
  records found in log
- pid: signature public key; epoch: block number; txid: transaction id
```

## Development
- Format source code: `black *`
- Generate requirements: `pipreqs . --force`
