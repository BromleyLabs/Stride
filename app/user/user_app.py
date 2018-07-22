# This daemon will run by customer at his premises or in his control. 
import sys
import uuid
import json
import datetime
from common import config
from common.utils import *
import requests
import merkle_proof as merkel
import rlp
import trie.utils.nibbles as nibbles

class App:
    def __init__(self, log_file):
        self.logger = init_logger('USER',  log_file)
        self.w3_rsk = W3Utils(config.rsk, self.logger)
        self.w3_eth = W3Utils(config.eth, self.logger)
        self.eth_contract, self.eth_concise = self.w3_eth.init_contract(
                                 'StrideEthContract', config.eth.contract_addr) 
        self.rsk_contract, self.rsk_concise = self.w3_rsk.init_contract(
                                 'StrideRSKContract', config.rsk.contract_addr) 
        self.ebtc_contract, self.ebtc_concise = self.w3_eth.init_contract(
                                 'EBTCToken', config.eth.token_addr) 
        self.proof_contract, self.proof_concise = self.w3_rsk.init_contract(
                                 'EthProof', config.eth_proof_contract_addr)
        
        self.eth_tx = {'from' : config.eth.user, 'gas' : config.eth.gas, 
                       'gasPrice' : config.eth.gas_price, 'value' : 0}
        self.rsk_tx = {'from' : config.rsk.user, 'gas' : config.rsk.gas, 
                       'gasPrice' : config.rsk.gas_price, 'value' : 0} 
    
    def create_txn_id(self):
        u =  uuid.uuid4()  # Random 128 bits 
        return u.int
 
    def offchain_handshake(self, method, params):
        # With custodian
        txn_id = self.create_txn_id() 
        self.logger.info('Initiate %s, txn_id: %d' % (method, txn_id)) 
        js = {'jsonrpc' : '2.0', 'id' : txn_id, 
                  'method' : method, 'params' :  params}
        r = requests.post(config.custodian_portal, json = js)
        self.logger.info(r.text)
        if r.status_code != requests.codes.ok:
            self.logger.error('Incorrect response code from custodian = %d' % 
                               r.status_code)
            return None, None
        return txn_id, json.loads(r.text)
 
    def run_fwd_txn(self, sbtc_amount): # sbtc->ebtc
        params = {'sbtc_amount' : sbtc_amount, 'user' : config.eth.user}
        txn_id, js = self.offchain_handshake('init_sbtc2ebtc', params)
        if txn_id is None: 
            return 1
 
        pwd_hash = js['result'] # of form '0x45667...'
        timeout_interval = 100 # Right timeout TBD
        self.logger.info('password hash from custodian = %s' % pwd_hash)

        # Wait for Custodian to transfer Ether To Ether contract
        # TODO: User can spam custodian here by sending many requests for which
        # customer will end up depositing Ether
        self.logger.info('Waiting for custodian to transfer Ether')
        event_filter = self.eth_contract.events.FwdCustodianDeposited.createFilter(fromBlock = 'latest')
        event = self.w3_eth.wait_for_event(event_filter, 
                                           args = {'txn_id' : txn_id})
        if event is None:  # Timeout 
            self.logger.info('Custodian did not respond. Quiting.')
            return 0 

        # Transfer SBTC to RSK contract
        self.logger.info('Depositing SBTC to RSK contract ..')
        self.rsk_tx['value'] = sbtc_amount
        txn_hash = self.rsk_concise.fwd_deposit(txn_id, 
                            self.w3_eth.w3.toBytes(hexstr = pwd_hash), 
                            timeout_interval, transact = self.rsk_tx) 
        self.rsk_tx['value'] = 0

        status = self.w3_rsk.wait_to_be_mined(txn_hash) # TODO: Check for timeout
        if status == 'error':
            return 1 
        # Wait for custodian to send password string on RSK 
        self.logger.info('Waiting for custodian to send password string')
        event_filter = self.rsk_contract.events.FwdAckByCustodian.createFilter(fromBlock = 'latest')
        event = self.w3_rsk.wait_for_event(event_filter, 
                                           args = {'txn_id' : txn_id})
        if event is None:  # Timeout
            self.logger.info('Customer did not send password string. Challenging..')
            txn_hash = self.rsk_concise.fwd_no_custodian_action_challenge(
                                                 txn_id, transact = self.rsk_tx)
            self.w3_rsk.wait_to_be_mined(txn_hash) # TODO: Check for timeout
            self.logger.info('Fwd transaction complete')
            return 0

        pwd_str = event['args']['pwd_str'] 

        # Issuing EBTC on Eth contract   
        self.logger.info('Issuing EBTC on Eth contract ..')
        txn_hash = self.eth_concise.fwd_issue_ebtc(txn_id, pwd_str, 
                                             transact = self.eth_tx) 
        self.w3_eth.wait_to_be_mined(txn_hash)

        self.logger.info('Fwd transaction completed')
        return 0

    def rev_approve_ebtc(self):
        self.logger.info('Approve Eth contract to move EBTC')
        txn_hash = self.ebtc_concise.approve(config.eth.contract_addr, 
                                            10 * 10**18, 
                                            transact = self.eth_tx)
        self.logger.info('Tx hash: %s' % HexBytes(txn_hash).hex())
        self.w3_eth.wait_to_be_mined(txn_hash)

    def rev_submit_bock_header(self, block_hash):
        self.logger.info('Submitting block header to EthProof contract') 
        rlp_header =  merkel.get_rlp_block_header(self.w3_eth.w3, block_hash)
        txn_hash = self.proof_concise.submit_block(
            block_hash, 
            rlp_header,
            transact = self.rsk_tx
        )
        self.w3_rsk.wait_to_be_mined(txn_hash)
        
    def run_rev_txn(self, ebtc_wei):
        self.logger.info('Initiating EBTC->SBTC transfer')

        self.logger.info('Authorize Eth contract to move EBTC')
        self.rev_approve_ebtc()

        self.logger.info('Surrender EBTC on Eth')
        txn_hash = self.eth_concise.rev_redeem(config.rsk.dest_addr, ebtc_wei,
                                               transact = self.eth_tx)
        self.w3_eth.wait_to_be_mined(txn_hash)
   
        n = 2 # Only for testing, otherwise it is 30
        self.logger.info('Waiting for %d confirmations')
        bn = self.w3_eth.w3.eth.blockNumber
        while (self.w3_eth.w3.eth.blockNumber - bn) <=2:
            time.sleep(2)

        self.logger.info('Initiating EBTC->SBTC transfer')
        eth_txn_hex = HexBytes(txn_hash).hex()
        self.logger.info('Submit Eth txn proof to RSK and redeem SBTC')
        receipt, block_hash, path, parent_nodes = \
            merkel.build_receipt_proof(self.w3_eth.w3, eth_txn_hex) 

        self.rev_submit_bock_header(block_hash)
        latest_block =  self.w3_eth.w3.eth.getBlock('latest')
        self.rev_submit_bock_header(latest_block.hash)

        # Our last node will always be a leaf node and the path length will
        # be even because of rlp encoding of transaction index.  Hence, add 
        # prefix 0x20 to the path (as per hex encoding specs)
        self.logger.info('Redeeming on RSK') 
        path = b'\x20' + path
        txn_hash = self.rsk_concise.rev_redeem(receipt, block_hash, path,
                                               parent_nodes, 
                                               transact = self.rsk_tx) 
        self.w3_rsk.wait_to_be_mined(txn_hash)

def main():
    if len(sys.argv) != 3:
        print('Usage: python user_app.py <fwd | rev>  <sbtc | ebtc amount in float>')
        exit(0)
    
    wei = int(float(sys.argv[2]) * 1e18) # In Wei
    app = App('/tmp/stride.log')
    if sys.argv[1] == 'fwd':
        app.run_fwd_txn(wei)
    elif sys.argv[1] == 'rev':
        app.run_rev_txn(wei)
    else:
        print('Invalid argument')
        exit(0)

if __name__== '__main__':
    main()
