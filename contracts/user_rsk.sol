pragma solidity ^0.4.23;

/* User side contract on RSK for Atomic Swap */

import "erc20.sol";

contract mortal {
    address m_owner = msg.sender;  /* Whoever deploys this contract */ 
    function kill() public { if (msg.sender == m_owner) selfdestruct(m_owner); }
}

contract UserRSKContract is mortal {

    enum TxnStates {CREATED, EXECUTED}

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

    /* TODO: Separate the two parts below into separate function calls */
    function execute(uint txn_id, string pwd_str) public { /* Called by custodian */
        require(msg.sender == m_txns[txn_id].custodian_rsk, "Only custodian can call this"); 
        require(m_txns[txn_id].state == TxnStates.CREATED, "Transaction already executed");

        ForwardTxn memory txn = m_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */

        /* Atomic swap logic.  Assumption here is that user has already deposited SBTC to this contract */
        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        if(block.number > (txn.creation_block + txn.timeout_interval)) {
            require(token_contract.transferFrom(this, txn.user_rsk, txn.sbtc_amount)); 
        }
        else {
            require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");
            require(token_contract.transferFrom(this, txn.custodian_rsk, txn.sbtc_amount));
            txn.state = TxnStates.EXECUTED;
            emit CustodianExecutionSuccess(txn_id, pwd_str);
        }
    }
}


