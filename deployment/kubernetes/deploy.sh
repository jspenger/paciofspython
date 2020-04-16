SCRIPTPATH=$(dirname "$0")

# deploy multichain
sh $SCRIPTPATH/multichain/multichain-deployment.sh

# wait 3 minutes for multichain blockchain to bootstrap
sleep 120

# deploy paciofs
sh $SCRIPTPATH/paciofs/paciofs-deployment.sh
