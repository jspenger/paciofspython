SCRIPTPATH=$(dirname "$0")

# delete multichain deployment
sh $SCRIPTPATH/multichain/delete-multichain-deployment.sh

# delete paciofs deployment
sh $SCRIPTPATH/paciofs/delete-paciofs-deployment.sh
