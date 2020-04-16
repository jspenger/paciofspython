SCRIPTPATH=$(dirname "$0")

# delete paciofs deployment
sh $SCRIPTPATH/paciofs/delete-paciofs-deployment.sh

# delete multichain deployment
sh $SCRIPTPATH/multichain/delete-multichain-deployment.sh
