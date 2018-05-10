pragma solidity ^0.4.23;

/* Custodian side contract on Ethereum for Atomic Swap */

import "erc20.sol";

contract mortal {
    address m_owner = msg.sender;  /* Whoever deploys this contract */ 
    function kill() public { if (msg.sender == m_owner) selfdestruct(m_owner); }
}

contract CustodianEthContract is mortal {

    enum TxnStates {CREATED, EXECUTED}

    struct ForwardTxn {
        address custodian; 
        uint txn_id; 
        address user;
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint ebtc_amount;
        TxnStates state;
    } 

    mapping (uint => ForwardTxn) public m_txns; 
    address constant m_ebtc_token_addr = 0xc778417E063141139Fce010982780140Aa0cD5Ab; /* WETH for testing */ 

    event CustodianTransactionCreated(uint txn_id, address custodian, address user);
    event CustodianTransferred(uint txn_id);
    event UserExecutionSuccess(uint txn_id);

    function create_transaction(uint txn_id, address user, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint ebtc_amount) public {
        require(m_txns[txn_id].txn_id != txn_id, "Transaction already exists");
       
        m_txns[txn_id] = ForwardTxn(msg.sender, txn_id, user, custodian_pwd_hash, timeout_interval,
                                    block.number, ebtc_amount, TxnStates.CREATED);
        
        emit CustodianTransactionCreated(txn_id, msg.sender, user);
    }

    function transfer_to_contract(uint txn_id) public { /* To be called by custodian */
        /* Assumed customer has approved movement of erc20 tokens from his account to this contract */
        require(msg.sender == m_txns[txn_id].custodian);
        require(m_txns[txn_id].txn_id == txn_id, "Transaction does not exist"); 
     
        ERC20Interface token_contract = ERC20Interface(m_ebtc_token_addr);
        require(token_contract.transferFrom(m_txns[txn_id].custodian, this, m_txns[txn_id].ebtc_amount)); 

        emit CustodianTransferred(txn_id);
    }

    function execute(uint txn_id, string pwd_str) public { /* Called by user */ 
        require(msg.sender == m_txns[txn_id].user, "Only user can call this"); 
        require(m_txns[txn_id].state == TxnStates.CREATED, "Transaction already executed");

        ForwardTxn memory txn = m_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */

        /* Atomic swap logic.  Assumption here is that custodian has already deposited EBTC to this contract */
        ERC20Interface token_contract = ERC20Interface(m_ebtc_token_addr);
        if(block.number > (txn.creation_block + txn.timeout_interval)) {
            require(token_contract.transferFrom(this, txn.custodian, txn.ebtc_amount));
        }
        else {
            require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");
            require(token_contract.transferFrom(this, txn.user, txn.ebtc_amount));
            txn.state = TxnStates.EXECUTED;
            emit UserExecutionSuccess(txn_id);
        }
    }
}


