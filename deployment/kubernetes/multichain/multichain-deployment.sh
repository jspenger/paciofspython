SCRIPTPATH=$(dirname "$0")

# deploy multichain seed to kubernetes
kubectl apply -f $SCRIPTPATH/multichainseed-deployment.yaml

# deploy multichain to kubernetes
kubectl apply -f $SCRIPTPATH/multichain-deployment.yaml

sleep 30

# delete running multichainseed deployment
kubectl delete --all -f $SCRIPTPATH/multichainseed-deployment.yaml
