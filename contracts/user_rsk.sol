pragma solidity ^0.4.23;

contract ERC20Interface {
    function totalSupply() public constant returns (uint);
    function balanceOf(address tokenOwner) public constant returns (uint balance);
    function allowance(address tokenOwner, address spender) public constant returns (uint remaining);
    function transfer(address to, uint tokens) public returns (bool success);
    function approve(address spender, uint tokens) public returns (bool success);
    function transferFrom(address from, address to, uint tokens) public returns (bool success);

    event Transfer(address indexed from, address indexed to, uint tokens);
    event Approval(address indexed tokenOwner, address indexed spender, uint tokens);
}

contract mortal {
    address m_owner = msg.sender;  /* Whoever deploys this contract */ 
    function kill() public { if (msg.sender == m_owner) selfdestruct(m_owner); }
}


contract UserRSKContract is mortal {

    enum TxnStates {CREATED, EXECUTED}

    struct ForwardTxn {
        address user;
        bytes32 txn_id; 
        address custodian; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint sbtc_amount;
        TxnStates state;
    } 

    mapping (bytes32 => ForwardTxn) public m_txns; 
    event UserTransactionCreated(bytes32 txn_id, address user, address custodian);
    event CustodianExecutionSuccess(bytes32 txn_id, bytes pwd_str); 

    address constant m_sbtc_token_addr = 0xc778417E063141139Fce010982780140Aa0cD5Ab; /* WETH for testing */ 

    function create_transaction(bytes32 txn_id, address custodian, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint sbtc_amount) public {
        /* Assumed user has generated a unique txn_id.  May not matter, but just to avoid unnecessary
           handling and potential problems */
       
        m_txns[txn_id] = ForwardTxn(msg.sender, txn_id, custodian, custodian_pwd_hash, timeout_interval,
                                    block.number, sbtc_amount, TxnStates.CREATED);
        
        emit UserTransactionCreated(txn_id, msg.sender, custodian);
    }


    function execute(bytes32 txn_id, bytes pwd_str) public { /* Called by custodian */
         
        require(msg.sender == m_txns[txn_id].custodian, "Only custodian can call this"); 
        require(m_txns[txn_id].state == TxnStates.CREATED, "Transaction already executed");

        /* Atomic swap logic.  Assumption here is that user has already deposited SBTC to this contract */
        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        if(block.number > (m_txns[txn_id].creation_block + m_txns[txn_id].timeout_interval)) {
            require(token_contract.transferFrom(this, m_owner, m_txns[txn_id].sbtc_amount));
        }
        else {
            require(m_txns[txn_id].custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");
            require(token_contract.transferFrom(this, m_txns[txn_id].custodian, m_txns[txn_id].sbtc_amount));
            m_txns[txn_id].state = TxnStates.EXECUTED;
            emit CustodianExecutionSuccess(txn_id, pwd_str);
        }
    }
}


