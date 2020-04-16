SCRIPTPATH=$(dirname "$0")

# deploy multichain and paciofs
sh $SCRIPTPATH/deploy.sh

# deploy benchmark
sh $SCRIPTPATH/benchmark/benchmark-deployment.sh

# wait 10 minutes
sleep 600

# print logs
sh $SCRIPTPATH/print-logs.sh | tee $SCRIPTPATH/benchmark.log

# delete deployments
sh $SCRIPTPATH/benchmark/delete-benchmark-deployment.sh
sh $SCRIPTPATH/delete-deployment.sh
