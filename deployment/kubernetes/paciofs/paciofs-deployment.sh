SCRIPTPATH=$(dirname "$0")

# deploy paciofs to kubernetes
kubectl apply -f $SCRIPTPATH/paciofs-deployment.yaml
