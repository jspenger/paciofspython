SCRIPTPATH=$(dirname "$0")

# delete current benchmark deployment
kubectl delete --all -f $SCRIPTPATH/benchmark-deployment.yaml
