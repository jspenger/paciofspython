SCRIPTPATH=$(dirname "$0")

# delete current paciofs deployment
kubectl delete --all -f $SCRIPTPATH/paciofs-deployment.yaml
