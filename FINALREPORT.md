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
This is the original version of PacioFS.
It is implemented in languages Java, C++, using extensions: grpc, FUSE, MultiChain, Akka.
It provides a deployment to Kubernetes and Docker, and automatic build integration using Travis-CI.
The open source code can be found at https://github.com/paciofs/paciofs.

This code base is no longer being maintained.
The program in this current state is not usable for a replicated file system, as the data is not replicated to other servers.
Furthermore, the current implementation does not order guarantee any order on the transactions appended to the blockchain.
The program does, however, serve as a base for building a RPC file system service in Java and C++.

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

**Installing PacioFS:**
- Download paciofs: `git clone https://github.com/paciofs/paciofs.git`
- Navige into directory: `cd paciofs`
- Install all libraries (Linux / MacOs):
  - Kubernetes (local Kubernetes cluster with minikube or docker-desktop)
  - Java SE Development Kit 11
  - Docker
  - Linux (apt get):
    - clang-format
    - cppcheck
    - gettext
    - libboost-all-dev
    - libfuse-dev
  - MacOS (brew install):
    - osxfuse
    - java11
    - boost
    - clang-format
    - cppcheck
    - gettext
- Install with Maven
  ```
  mvn --non-recursive install
  mvn --file ./paciofs-client/third_party/pom.xml install
  export DESTDIR=pfs
  mvn --define destdir=${DESTDIR} clean install
  ```
- Start a Kubernetes deployment:Start Kubernetes (locally: `minikube start`)
- Build Docker image: `./paciofs-docker/docker-compose-minikube.sh`
- Deploy to Kubernetes: `kubectl apply -f ./paciofs-kubernetes/paciofs-minikube.yaml`
- Run test script: `bash -x .travis/test.sh`, or start

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

**Pitfalls:**
- Make sure to install all required packages and libraries before running Maven installation.
- Root is necessary for FUSE. PacioFS Client can only run with root access.

## Implementation - PacioFSPython
Implementation overview
- Short description of how it is implemented (core implementation philosophy)
    - PacioFSPython is Python implementation of PacioFS.
    - The implementation consists of four parts, we will briefly discuss each:
        - PacioFS
            - PacioFS(Python) is a prototype under development. and is currently not suitable for deployment.
            - “The architecture consists of three layers.
        - Deployment
            - The deployment consists of a docker container of the PacioFS software, and a Kubernetes deployment.
            - Docker
                -
            - Kubernetes
                -
        - Tests
            -
            - travis-CI
- Directory structure
How to get it running
- Running PacioFSPython
    - Steps
        - Go to https://github.com/jonasspenger/paciofspython/
        - The easiest way to get started is to run PacioFSPython in a docker container. This requires root privileges. A safer alternative is to run it in a virtual machine. The safest alternative is to read the logs from https://travis-ci.com/github/jonasspenger/paciofspython, which executes the help commands, runs the unit tests and integration tests, and runs a benchmark.
    - Pitfalls
        - Root privileges are necessary for FUSE. This poses potential security issues.
- Deploying PacioFSPython
    - Steps
        -
    - Pitfalls
        -
Current status and roadmap
- Current issues
    - Implementation can cause orphan process running FUSE and multichaind (MultiChain daemon).
- Outstanding tasks:
    - Complete merger with https://github.com/jonasspenger/tamperproofbroadcast
    *  complete version history: the entire file-history is accessible
    *  fault-tolerant: data is protected against loss
    *  distributed, scalable, low latency, high throughput, etc.
    *  test and clean



  - Architecture
      - PacioFS
  - How to use
  - Pitfalls
      - Root privilege. Root privileges are necessary for FUSE. This is a potential security issue for the client.
      - MultiChain. Bootstrapping a MultiChain cluster requires two steps. First, a seed node has to create a new MultiChain blockchain together with a new genesis block. After that, other MultiChain nodes can connect to this new Blockchain either via the seed node, or via other nodes that have connected. (An instance of the Bitcoin blockchain would not require this two-step process, as the genesis block can be decided before launching the blockchain.)
      - Implementation can cause orphan processes if not shut down gracefully. We currently do not know the cause of this.
  - Deployment and Testing
  - Deployment Pitfalls


# Discussion
- Bad choices:
  - MultiChain. In hindsight, we would maybe consider MultiChain to have been the wrong choice of technology, and perhaps preferred working with the Bitcoin blockchain. This is for two reasons: The MultiCHain codebase is not as frequently used as the Bitcoin codebase, thus more likely contains bugs and is less documented.
  - FUSE. FUSE requires root privileges, which requires that root privileges are necessary for deployment and testing. Furthermore, the overhead of mounting FUSE, and the involvement of significantly more processes. This is especially noticeable whilst testing, and if one of the tests does not shut down gracefully. Furthermore, we are uncertain if the Posix File system is a sutable abstraction for our purposes. As saving a large file is in fact not one, but potentially a large number of operations, this increases the burden, or the question, should every operation be stored tamper-proof? or can operations be grouped together in more logical blocks? Perhaps, it would have been easier, less complex, to define a object blob-storage (like google cloud storage), that stores larger files in a single operation. Thus, each store would only generate one entry in the ledger.

# Conclusions
