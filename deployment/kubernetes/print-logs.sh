SCRIPTPATH=$(dirname "$0")

for POD in $(kubectl get pods | cut -d" " -f1 | tail -n +2)
do
  echo $POD
  kubectl logs $POD
done
