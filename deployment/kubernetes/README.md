# PacioFS Kubernetes Deployment

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
