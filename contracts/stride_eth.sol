pragma solidity ^0.4.23;

/* Contract on Ethereum for SBTC->EBTC transaction */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";

contract StrideEthContract is mortal {
    using SafeMath for uint;

    enum TxnStates {UNINITIALIZED, CREATED, EXECUTED, REFUNDED}

    struct ForwardTxn {
        address custodian_eth;  /* Eth address */
        uint txn_id; 
        address user_eth; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint ebtc_amount; 
        uint collateral_eth; /* Calculated */
        TxnStates state;
    }  /* TODO: What is the cost of this storage? */

    mapping (uint => ForwardTxn) public m_txns; 
    address constant m_ebtc_token_addr = 0x0; /* TODO */ 
    uint m_eth_ebtc_ratio_numerator = 15; 
    uint m_eth_ebtc_ratio_denominator = 1;

    event CustodianTransactionCreated(uint txn_id, address custodian_eth, address user_eth);
    event CustodianTransferred(uint txn_id);
    event UserExecutionSuccess(uint txn_id);
    event RefundedToCustodian(uint txn_id);
   
    function set_eth_ebtc_ratio(uint numerator, uint denominator) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_eth_ebtc_ratio_numerator = numerator;
        m_eth_ebtc_ratio_denominator = denominator;
    }

    function create_transaction(uint txn_id, address user_eth, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint ebtc_amount) public {
        require(m_txns[txn_id].txn_id != txn_id, "Transaction already exists");
       
        uint collateral_eth = (ebtc_amount.mul(m_eth_ebtc_ratio_numerator)).div(m_eth_ebtc_ratio_denominator); 
        m_txns[txn_id] = ForwardTxn(msg.sender, txn_id, user_eth, custodian_pwd_hash, timeout_interval,
                                    block.number, ebtc_amount, collateral_eth, TxnStates.CREATED);
        
        emit CustodianTransactionCreated(txn_id, msg.sender, user_eth);
    }

    function transfer_to_contract(uint txn_id) public payable { /* To be called by custodian to deposit Eth */
        ForwardTxn memory txn = m_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */
        require(msg.sender == txn.custodian_eth);
        require(txn.txn_id == txn_id, "Transaction does not exist"); 
        require(msg.value == txn.collateral_eth); 
     
        emit CustodianTransferred(txn_id);
    }

    function request_refund(uint txn_id) public { /* Called by custodian */
        ForwardTxn memory txn = m_txns[txn_id]; 
        require(msg.sender == txn.custodian_eth, "Only custodian can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));
        txn.custodian_eth.transfer(txn.collateral_eth);
        txn.state = TxnStates.REFUNDED;

        emit RefundedToCustodian(txn_id);
    }

    function execute(uint txn_id, string pwd_str) public { /* Called by user */
        ForwardTxn memory txn = m_txns[txn_id]; 
        require(msg.sender == txn.user_eth, "Only user can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");

        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(txn.user_eth, txn.ebtc_amount));
        txn.state = TxnStates.EXECUTED;

        emit UserExecutionSuccess(txn_id);
    }
}


