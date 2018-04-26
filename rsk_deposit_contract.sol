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

contract RSKDepositContract is mortal {

    enum TxnStates {DEPOSITED, ACKNOWLEDGED}

    struct ForwardTxn { /* from SBTC -> EBTC */
        uint txn_id;
        address user;
        uint amount;  /* SBTC */ 
        address eth_addr;  
        TxnStates state; 
        string ack_msg; /* from custodian */
        bytes32 ack_msg_sign; /* by custodian */
        uint8 v;
        bytes32 r;
        bytes32 s;
    }

    uint private m_txn_count = 0;
    address public m_custodian; 
    address constant m_sbtc_token_addr = 0xc778417E063141139Fce010982780140Aa0cD5Ab; /* WETH for testing */ 
    mapping (uint => ForwardTxn) public m_txns; 

    event Deposited(address from, address to, uint amount, uint txn_id);
    event Ack(string json_msg, bytes32 signature, uint8 v, bytes32 r, bytes32 s);

    function add_custodian(address addr) public {
        require(msg.sender == m_owner, "Only owner can call this");  
        require(m_custodian == address(0), "Custodian already set");   

        m_custodian = addr;
    }

    function deposit_sbtc(uint sbtc_amount, address eth_addr) public { /* By user */
        require(m_custodian != address(0), "Custodian not set");   
        require(msg.sender != m_custodian, "A custodian should not call this"); 

        /* For now, it is assumed that SBTC is ERC20 compliant and user has approved
           this contract address to transfer tokens from user's account to custodian's
           account */
        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        require(token_contract.transferFrom(msg.sender, m_custodian, sbtc_amount)); 

        m_txns[m_txn_count] = ForwardTxn(m_txn_count, msg.sender, sbtc_amount, 
                                        eth_addr, TxnStates.DEPOSITED, "", 0, 0, 0, 0); 

        emit Deposited(msg.sender, eth_addr, sbtc_amount, m_txn_count); /* Custodian watches this event */ 

        m_txn_count += 1;
    }

    /* json_msg: "{fromSbtc: <>, toEthr: <>, amount : <>, blocNumber: <>}" 
       json_msg is signed as signature */
 
    function submit_ack(uint txn_id, string json_msg, bytes32 signature, 
                        uint8 v, bytes32 r, bytes32 s) public { /* Sent by custodian */
        require(msg.sender == m_custodian, "Only custodian can call this");
        bytes memory prefix = "\x19Ethereum Signed Message:\n32";
        bytes32 prefixedHash = keccak256(prefix, signature); 
        require(ecrecover(prefixedHash, v, r, s) == m_custodian, "Not a custodian signed msg"); 
         
        m_txns[txn_id].ack_msg = json_msg;
        m_txns[txn_id].ack_msg_sign = signature;
        m_txns[txn_id].v = v;
        m_txns[txn_id].r = r;
        m_txns[txn_id].s = s;
        m_txns[txn_id].state = TxnStates.ACKNOWLEDGED; 

        emit Ack(json_msg, signature, v, r, s); /* User watches this event */

    }
}
