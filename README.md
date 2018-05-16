# Stride

## Installation notes

- Setup python 3.5 virtual environment
- Setup web3.py
- Install python hexbytes module
- Install rabbit-mq
```
> sudo apt-get install rabbitmq-server
> sudo rabbitmq-plugins enable rabbitmq_management
>  sudo service rabbitmq-server restart
```
- Install python Pika in virtual environment
- Run RSK Testnet and Parity Ropsten node
- Create user, custodian accounts on on both 
- Unlock all the accounts - in Parity it has to be done while starting the node, while unlocking in RSK is done in the script itself.
- Get Ether for all accounts from Ropsten Testnet faucet. On Parity, convert some ether to WETH for testing.  This can be done using 0x Protocol page https://0xproject.com/portal/weth. You will need to install Metamask plugin.  And then add users into Metamask. Then useOx page to convert to WETH. Use chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/popup.html to add user in Metamask as importing accounts from Chrome icon does did not work for me. 
- For RSK, get SBTC using RSK Testnet faucet.   

## Running scripts
- All python scripts should be run in the Python virtual environment using:
```
>source ~/.venv-py3/bin/activate  
```
- The scripts here simulate one transaction
- Compile the contracts using ```solc```. Check the version of ```solc``` in contract code.
- Deploy them using deploy.py
- Update contract address in config.py
- First run custodian_app.py in a terminal, followed by user_app.py in another terminal.
- Common log file log.txt is created.


