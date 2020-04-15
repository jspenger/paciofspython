SCRIPTPATH=$(dirname "$0")

# deploy multichain seed to kubernetes
kubectl apply -f $SCRIPTPATH/multichainseed-deployment.yaml

# deploy multichain to kubernetes
kubectl apply -f $SCRIPTPATH/multichain-deployment.yaml
