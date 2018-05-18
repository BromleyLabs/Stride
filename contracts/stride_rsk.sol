pragma solidity ^0.4.23;

/* User side contract on RSK for Atomic Swap */

import "erc20.sol";
import "mortal.sol";

contract UserRSKContract is mortal {

    enum TxnStates {UNINITIALIZED, CREATED, EXECUTED, REFUNDED}

    struct ForwardTxn {
        address user_rsk; /* RSK address */
        uint txn_id; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint sbtc_amount;
        TxnStates state;
    } 

    mapping (uint => ForwardTxn) public m_txns; 
    address m_custodian_rsk;   

    event UserTransactionCreated(uint txn_id, address user_rsk, address custodian_rsk);
    event UserTransferred(uint txn_id);
    event CustodianExecutionSuccess(uint txn_id, string pwd_str); 
    event RefundedToUser(uint txn_id);

    function set_custodian(address addr) public {
        require(msg.sender == m_owner);
        m_custodian_rsk = addr;
    }

    function fwd_create_transaction(uint txn_id, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint sbtc_amount) public { /* By user */
        require(m_txns[txn_id].txn_id != txn_id, "Transaction already exists");
       
        m_txns[txn_id] = ForwardTxn(msg.sender, txn_id, custodian_pwd_hash, timeout_interval,
                                    block.number, sbtc_amount, TxnStates.CREATED);
        
        emit UserTransactionCreated(txn_id, msg.sender, m_custodian_rsk);
    }

    function fwd_transfer_to_contract(uint txn_id) public payable { /* To be called by user */
        ForwardTxn memory txn = m_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */
        require(msg.sender == txn.user_rsk);
        require(txn.txn_id == txn_id, "Transaction does not exist"); 
        require(msg.value == txn.sbtc_amount, "Sent SBTC amount does not match"); 

        emit UserTransferred(txn_id);
    }

    function fwd_request_refund(uint txn_id) public { /* Called by user */
        ForwardTxn memory txn = m_txns[txn_id]; 
        require(msg.sender == txn.user_rsk, "Only user can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        txn.user_rsk.transfer(txn.sbtc_amount);
        txn.state = TxnStates.REFUNDED;

        emit RefundedToUser(txn_id);
    }

    /* This function main job is to send password string to user */ 
    function fwd_send_pwd(uint txn_id, string pwd_str) public { /* Called by custodian */
        ForwardTxn memory txn = m_txns[txn_id]; 
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");

        txn.state = TxnStates.EXECUTED;

        emit CustodianExecutionSuccess(txn_id, pwd_str);
    }

    function rev_execute(address to, uint sbtc_amount) public { /* By custodian */
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        /* TODO: We need to check if the amount is going to correct user */
        to.transfer(sbtc_amount);
    }

    function rev_force_execute() public { /* By user if custodian does not call rev_excecute()  */
        if txn 

    }

}


