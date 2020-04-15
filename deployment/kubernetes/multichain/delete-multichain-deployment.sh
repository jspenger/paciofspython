SCRIPTPATH=$(dirname "$0")

# delete running multichainseed deployment
kubectl delete --all -f $SCRIPTPATH/multichainseed-deployment.yaml

# delete current multichain deployment
kubectl delete --all -f $SCRIPTPATH/multichain-deployment.yaml
