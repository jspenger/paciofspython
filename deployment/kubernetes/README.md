# PacioFS Kubernetes Deployment
The deployment deploys 3 MultiChain servers and 3 PacioFS servers.
The benchmark deployment launches a job that starts a PacioFS client connecting to one of the PacioFS servers, and runs the fio benchmark.

To deploy (PacioFSServer + MultiChain) run:
```
sh deploy.sh
```

To delete deployment (PacioFSServer + MultiChain) run:
```
sh delete-deployment.sh
```

To run a short benchmark on the deployment, run `run_benchmark.sh` or:
```
# deploy multichain and paciofs
sh deploy.sh

# deploy benchmark
sh benchmark/benchmark-deployment.sh

# wait 10 minutes
sleep 600

# print logs
sh print-logs.sh | tee benchmark.log

# delete deployments
sh benchmark/delete-benchmark-deployment.sh
sh delete-deployment.sh
```
