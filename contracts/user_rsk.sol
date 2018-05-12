pragma solidity ^0.4.23;

/* User side contract on RSK for Atomic Swap */

import "erc20.sol";

contract mortal {
    address m_owner = msg.sender;  /* Whoever deploys this contract */ 
    function kill() public { if (msg.sender == m_owner) selfdestruct(m_owner); }
}

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
    address constant m_sbtc_token_addr = 0xc778417E063141139Fce010982780140Aa0cD5Ab; /* WETH for testing */ 

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

    function transfer_to_contract(uint txn_id) public { /* To be called by user */
        /* Assumed user has approved movement of sbtc tokens from his account to this contract */
        require(msg.sender == m_txns[txn_id].user_rsk);
        require(m_txns[txn_id].txn_id == txn_id, "Transaction does not exist"); 
     
        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        require(token_contract.transferFrom(m_txns[txn_id].user_rsk, this, m_txns[txn_id].sbtc_amount)); 

        emit UserTransferred(txn_id);
    }

    function refund(uint txn_id) public { /* Called by user */
        ForwardTxn memory txn = m_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */
        require(msg.sender == txn.user_rsk, "Only user can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        require(token_contract.transferFrom(this, txn.user_rsk, txn.sbtc_amount)); 
        txn.state = TxnStates.REFUNDED;

        emit RefundedToUser(txn_id);
    }

    function execute(uint txn_id, string pwd_str) public { /* Called by custodian */
        ForwardTxn memory txn = m_txns[txn_id]; 
        require(msg.sender == txn.custodian_rsk, "Only custodian can call this"); 
        require(txn.state == TxnStates.CREATED, "Transaction not in CREATED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");

        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        require(token_contract.transferFrom(this, txn.custodian_rsk, txn.sbtc_amount));
        txn.state = TxnStates.EXECUTED;

        emit CustodianExecutionSuccess(txn_id, pwd_str);
    }
}


