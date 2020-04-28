# Final Report
Jonas Spenger \
Zuse Institute Berlin \
Research Group: Distributed Data Management

April, 2020


## Contents
- Introduction
- Implementation: PacioFS
- Implementation: PacioFSPython
- Discussion
- Conclusions


## Introduction
PacioFS is a tamper-proof, distributed file system.
The project scope involves the research and development of algorithms and protocols for manipulation proof, scalable and fault tolerant storage of data on the basis of blockchain technology.

**Project information:**
- Name: Pacio
- Funding: Bundesministerium für Wirtschaft und Energie
- https://www.zib.de/projects/pacio
- Employment: Research Assistant Oct 2019 - Apr 2020


## Implementation - PacioFS
PacioFS is the original version of PacioFS.
It is implemented in languages Java, C++, using extensions: grpc, FUSE, MultiChain, Akka.
It provides a deployment to Kubernetes and Docker, and automatic build integration using Travis-CI.
The open source code can be found at https://github.com/paciofs/paciofs.

This code base is no longer being maintained.
The program in this current state is not usable for a replicated file system, as the data is not replicated to other servers.
Furthermore, the current implementation does not order guarantee any order on the transactions appended to the blockchain.
The program does, however, serve as a base for building a RPC file system service in Java and C++.

### Design - PacioFS
The PacioFS Server implementation consists of:
- a MultiChain abstraction
- a file system abstraction
- and the main module, which we refer to as PacioFS Server

PacioFS Server starts a process that runs the MultiChain abstraction.
The MultiChain abstraction continually synchronizes with the MultiChain.
It also manages the set of UTXOs (unspent transaction outputs), such that it never is empty, by splitting transactions into smaller pieces, if the set of UTXOs are too few.
The PacioFS Server accepts any incoming requests via RPC from the PacioFS Client.
These requests are executed on the file system abstraction, the returnvalue is returned to the PacioFS Client.
The requests are also appended to the blockchain using the MultiChain abstraction.

### Installation - PacioFS
- Download paciofs: `git clone https://github.com/paciofs/paciofs.git`
- Navige into directory: `cd paciofs`
- Install all libraries (Linux / MacOs):
  - Kubernetes (local Kubernetes cluster with minikube or docker-desktop)
  - Java SE Development Kit 11
  - Docker
  - Linux (apt get):
    - clang-format, cppcheck, gettext, libboost-all-dev, libfuse-dev.
  - MacOS (brew install):
    - osxfuse, java11, boost, clang-format, cppcheck, gettext.
- Install with Maven
  ```
  mvn --non-recursive install
  mvn --file ./paciofs-client/third_party/pom.xml install
  export DESTDIR=pfs
  mvn --define destdir=${DESTDIR} clean install
  ```

### Running, Testing, and Deployment - PacioFS
**Run PacioFS:**
See https://github.com/paciofs/paciofs.

**Run PacioFS test script:**
```
bash -x .travis/test.sh
```

**Or deploy to Kubernetes (local cluster in this example):**
```
# deploy to kubernetes
minikube start
./paciofs-docker/docker-compose-minikube.sh
kubectl apply -f ./paciofs-kubernetes/paciofs-minikube.yaml
# create and mount file system
timeout 5m kubectl port-forward --namespace=pacio service/paciofs 8080:8080 &
${DESTDIR}/usr/local/bin/mkfs.paciofs localhost:8080 volume1
mkdir /tmp/volume1
${DESTDIR}/usr/local/bin/mount.paciofs localhost:8080 /tmp/volume1 volume1 -d TRACE
```

### Pitfalls - PacioFS
- Make sure to install all required packages and libraries before running Maven installation.
- Root is necessary for FUSE. PacioFS Client can only run with root access.
- Software should not be used in real-world systems.

## Implementation - PacioFSPython
PacioFSPython is an implementation of PacioFS in Python with FUSE.
It encompasses: PacioFS, the source code of the prototype under development; a Kubernetes and Docker deployment; integration tests, unit tests, benchmarks; and continuous integration with Travis-CI.
The source code can be found at: https://github.com/jonasspenger/paciofspython/.

This code base is no longer being maintained.
It is not currently suitable for deployment, as there are some issues (which we will discuss).
The current status of the project is:
- [x] tamper-proof: any participant can detect unauthorized changes to the file system (see verify function)
- [x] multi-user: multiple users can concurrently use the system
- [x] multi-volume: supports multiple volumes
- [x] permissioned access / group membership: dynamic groups (join, leave) and permissioned (voteaccept, votekick)

The project supports continuous integration with Travis-CI, any pushed code to the repository is tested.
The tests include a benchmark run of running a PacioFS Server cluster and MultiChain cluster on Kubernetes, executing the fio benchmark (https://fio.readthedocs.io/).
A number of unit tests and integration tests are also run.
The integration tests include testing a multi-user setup, a multi-volume setup, a single-volume setup, and testing the verify functionality.
The latest commit is built into a docker container and published at https://hub.docker.com/r/jonasspenger/paciofspython.

### Design - PacioFSPython
The PacioFSPython Server implementation consists of:
- a MultiChain abstraction
- a Tamper-Proof Broadcast abstraction (abstraction of the MultiChain abstraction)
- and the main module, which we refer to as PacioFSPython Server.

Upon first starting the server, it connects (or creates) a MultiChain instance, and instantiates the tamper-proof broadcast abstraction thereof.
When a user first connects to the server and creates a new volume, the volume name and the servers PID are broadcast.
The server keeps a map of all servers and the volumes they manage.
When the user issues a file system request to the server, the server executes the request locally, and if the request changes the state of the file system, broadcasts the hash value of the requested command via the broadcast abstraction.
When the broadcast abstraction delivers a command on one of the managed volumes, this command is re-executed on the local file system.
Pseudocode of the implementation is available at https://github.com/jonasspenger/paciofspython/.

### Installation - PacioFSPython
The recommended way to install PacioFS Python is via Docker.
To build the docker image, see deployment/docker/README.md.
Alternatively, use the pre-built image from docker hub at jonasspenger/paciofspython.
For local installation, see https://github.com/jonasspenger/paciofspython/.

### Running, Testing, and Deployment - PacioFSPython
**Running PacioFSPython:**
```
docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  sh paciofspython/tests/benchmarks/paciofspython/paciofs/paciofslocal.py -h;

docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  sh paciofspython/tests/benchmarks/paciofspython/paciofs/paciofslocal.py fotb -h;
```

**Run benchmark:**
```
docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  sh paciofspython/tests/benchmarks/test_fio.sh;
```
The fio benchmark results can be inspected at https://travis-ci.com/github/jonasspenger/paciofspython.

**Run unit tests and integration tests:**
```
docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  python3 -m unittest discover paciofspython/tests/unittests -v;

docker run \
  --rm \
  -it \
  --privileged \
  jonasspenger/paciofspython \
  python3 -m unittest discover paciofspython/tests/integrationtests -v;
```
For an example of the outputs please refer to the latest build at https://travis-ci.com/jonasspenger/paciofspython.

**Deploy to Kubernetes:**
To run a Kubernetes deployment of PacioFS, see https://github.com/jonasspenger/paciofspython/tree/master/deployment/kubernetes.
It is as simple as running the `sh deploy.sh` command.
This starts a MultiChain cluster and a PacioFSPython server cluster.
The deployment includes a benchmark deployment.

### Pitfalls:
- Root access is necessary for FUSE. That is why the `--privileged` flag is necessary for running Docker containers. This is a potential security issue for the client.
- MultiChain. Bootstrapping a MultiChain cluster requires two steps. First, a seed node has to create a new MultiChain blockchain together with a new genesis block. After that, other MultiChain nodes can connect to this new Blockchain either via the seed node, or via other nodes that have connected. (An instance of the Bitcoin blockchain would not require this two-step process, as the genesis block can be decided before launching the blockchain.)
- Implementation can cause orphan process running FUSE and multichaind (MultiChain daemon). The implementation does not shut down gracefully.
- Software is not stable under large workloads, and should not be used in real-world systems.
- Integration tests do not fully cover the requirements specification as required by GoBD (Grund­sät­ze zur ord­nungs­mä­ßi­gen Füh­rung und Auf­be­wah­rung von Bü­chern, Auf­zeich­nun­gen und Un­ter­la­gen in elek­tro­ni­scher Form so­wie zum Da­ten­zu­griff).

### Outstanding Tasks
- Complete merger with https://github.com/jonasspenger/tamperproofbroadcast.
- Implement support for version history (the entire file-history is accessible).
- Make software fault-tolerant, scalable, and high-performance.
- Test and clean the software.
- Future work includes proof-of-storage and proof-of-integrity.
