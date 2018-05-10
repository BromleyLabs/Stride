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
        address user;
        uint txn_id; 
        address custodian; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint sbtc_amount;
        TxnStates state;
    } 

    mapping (uint => ForwardTxn) public m_txns; 
    address constant m_sbtc_token_addr = 0xc778417E063141139Fce010982780140Aa0cD5Ab; /* WETH for testing */ 

    event UserTransactionCreated(uint txn_id, address user, address custodian);
    event CustodianExecutionSuccess(uint txn_id, string pwd_str); 

    function create_transaction(uint txn_id, address custodian, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint sbtc_amount) public {
        require(m_txns[txn_id].txn_id != txn_id, "Transaction already exists");
       
        m_txns[txn_id] = ForwardTxn(msg.sender, txn_id, custodian, custodian_pwd_hash, timeout_interval,
                                    block.number, sbtc_amount, TxnStates.CREATED);
        
        emit UserTransactionCreated(txn_id, msg.sender, custodian);
    }


    function execute(uint txn_id, string pwd_str) public { /* Called by custodian */
        require(msg.sender == m_txns[txn_id].custodian, "Only custodian can call this"); 
        require(m_txns[txn_id].state == TxnStates.CREATED, "Transaction already executed");

        ForwardTxn memory txn = m_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */

        /* Atomic swap logic.  Assumption here is that user has already deposited SBTC to this contract */
        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        if(block.number > (txn.creation_block + txn.timeout_interval)) {
            require(token_contract.transferFrom(this, txn.user, txn.sbtc_amount));
        }
        else {
            require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");
            require(token_contract.transferFrom(this, txn.custodian, txn.sbtc_amount));
            txn.state = TxnStates.EXECUTED;
            emit CustodianExecutionSuccess(txn_id, pwd_str);
        }
    }
}


