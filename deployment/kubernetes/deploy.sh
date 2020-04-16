SCRIPTPATH=$(dirname "$0")

# deploy multichain
sh $SCRIPTPATH/multichain/multichain-deployment.sh

# deploy paciofs
sh $SCRIPTPATH/paciofs/paciofs-deployment.sh
