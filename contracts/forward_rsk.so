pragma solidity ^0.4.23;

/* User side contract on RSK for Atomic Swap */

import "erc20.sol";
import "mortal.sol";

contract UserRSKContract is mortal {

    enum TxnStates {UNINITIALIZED, CREATED, EXECUTED, REFUNDED}

    struct ForwardTxn {
        address user_rsk; /* RSK address */
        uint txn_id; 
        address custodian_rsk;  
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint sbtc_amount;
        TxnStates state;
    } 

    mapping (uint => ForwardTxn) public m_txns; 

    event UserTransactionCreated(uint txn_id, address user_rsk, address custodian_rsk);
    event UserTransferred(uint txn_id);
    event CustodianExecutionSuccess(uint txn_id, string pwd_str); 
    event RefundedToUser(uint txn_id);

    function create_transaction(uint txn_id, address custodian_rsk, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint sbtc_amount) public {
        require(m_txns[txn_id].txn_id != txn_id, "Transaction already exists");
       
        m_txns[txn_id] = ForwardTxn(msg.sender, txn_id, custodian_rsk, custodian_pwd_hash, timeout_interval,
                                    block.number, sbtc_amount, TxnStates.CREATED);
        
        emit UserTransactionCreated(txn_id, msg.sender, custodian_rsk);
    }

    function transfer_to_contract(uint txn_id) public payable { /* To be called by user */
        ForwardTxn memory txn = m_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */
        require(msg.sender == txn.user_rsk);
        require(txn.txn_id == txn_id, "Transaction does not exist"); 
        require(msg.value == txn.sbtc_amount, "Sent SBTC amount does not match"); 

        emit UserTransferred(txn_id);
    }

    function request_refund(uint txn_id) public { /* Called by user */
        ForwardTxn memory txn = m_txns[txn_id]; 
        require(msg.sender == txn.user_rsk, "Only user can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        txn.user_rsk.transfer(txn.sbtc_amount);
        txn.state = TxnStates.REFUNDED;

        emit RefundedToUser(txn_id);
    }

    function execute(uint txn_id, string pwd_str) public { /* Called by custodian */
        ForwardTxn memory txn = m_txns[txn_id]; 
        require(msg.sender == txn.custodian_rsk, "Only custodian can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");

        txn.custodian_rsk.transfer(txn.sbtc_amount); 

        txn.state = TxnStates.EXECUTED;

        emit CustodianExecutionSuccess(txn_id, pwd_str);
    }
}


