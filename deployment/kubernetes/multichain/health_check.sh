# check health
echo check multichain health
echo {0..3} | tr " " "\n" | xargs -I{} kubectl exec multichain-{} -- bin/ash -c 'multichain-cli chain --rpcuser=user --rpcpassword=password getinfo'
echo {0..3} | tr " " "\n" | xargs -I{} kubectl exec multichain-{} -- bin/ash -c 'multichain-cli chain --rpcuser=user --rpcpassword=password getlastblockinfo'
echo {0..3} | tr " " "\n" | xargs -I{} kubectl exec multichain-{} -- bin/ash -c 'multichain-cli chain --rpcuser=user --rpcpassword=password getpeerinfo'
echo {0..3} | tr " " "\n" | xargs -I{} kubectl exec multichain-{} -- bin/ash -c 'multichain-cli chain --rpcuser=user --rpcpassword=password getblockchaininfo'
