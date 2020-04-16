SCRIPTPATH=$(dirname "$0")

# deploy benchmark to kubernetes
kubectl apply -f $SCRIPTPATH/benchmark-deployment.yaml
