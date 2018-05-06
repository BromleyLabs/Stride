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
        uint sbtc_amount;  /* SBTC */ 
        address eth_addr;  
        TxnStates state; 
        bytes ack_msg; /* TODO: has to be longer. from custodian */
        bytes32 ack_msg_hash; 
        uint8 v; /* Signed by custodian */
        bytes32 r;
        bytes32 s;
    }

    address public m_custodian; 
    address constant m_sbtc_token_addr = 0xc778417E063141139Fce010982780140Aa0cD5Ab; /* WETH for testing */ 
    mapping (uint => ForwardTxn) public m_txns; 

    uint private m_txn_count = 1; /* We will use 0 to check existence of key in above mapping */
                                  /* TODO: Is there a need to use a hash as an id? */

    event Deposited(address from, address to, uint amount, uint txn_id);
    event Ack(bytes ack_msg, bytes32 ack_msg_hash, uint8 v, bytes32 r, bytes32 s);

    function add_custodian(address addr) public {
        require(msg.sender == m_owner, "Only owner can call this");  
        require(m_custodian == address(0), "Custodian already set");   

        m_custodian = addr;
    }

    /* This method is called by user. For now, it is assumed that SBTC is ERC20 
       compliant and user has approved this contract address to transfer SBTC from 
       user's account to contract address's account */ 
    function deposit_sbtc(uint sbtc_amount, address eth_addr) public { /* By user */
        require(m_custodian != address(0), "Custodian not set");   
        require(msg.sender != m_custodian, "A custodian should not call this"); 

        ERC20Interface token_contract = ERC20Interface(m_sbtc_token_addr);
        require(token_contract.transferFrom(msg.sender, this, sbtc_amount)); 

        uint txn_id = m_txn_count; /* Unique id */
        m_txn_count += 1;

        m_txns[txn_id] = ForwardTxn(m_txn_count, msg.sender, sbtc_amount, 
                                        eth_addr, TxnStates.DEPOSITED, "", 0, 0, 0, 0); 

        emit Deposited(msg.sender, eth_addr, sbtc_amount, txn_id); /* Custodian watches this event */ 

    }

    /* Extract bytes32 from a byte array given an offset */
    function get_bytes(bytes b, uint nbytes, uint offset) private pure returns (bytes32) {
        bytes32 out;

        for (uint i = 0; i < nbytes; i++) 
            out |= bytes32(b[offset + i] & 0xFF) >> (i * 8);

        return out;
    }

    /* ack_msg byte array: tx_id(32), fromSbtc(20), toEthr(20), amount(32), blocNumber(32)
       txn_id is what custodian reads from Deposited event */
    /* TODO: ack_msg can be packed better to save memory, if it really matters */ 
    function submit_ack(bytes ack_msg, bytes32 ack_msg_hash, 
                        uint8 v, bytes32 r, bytes32 s) public { /* Sent by custodian */
        require(msg.sender == m_custodian, "Only custodian can call this");
        bytes memory prefix = "\x19Ethereum Signed Message:\n32";
        bytes32 prefixedHash = keccak256(prefix, ack_msg_hash) ; 
        require(ecrecover(prefixedHash, v, r, s) == m_custodian, "Not a custodian signed msg"); 
        require(ack_msg_hash == keccak256(ack_msg), "Ack msg hash does not match"); 
       
        /* TODO: Verify if custodian has sent correct information for this transaction id */
        uint offset = 0;
        uint txn_id = uint(get_bytes(ack_msg, 32, offset));
        require(m_txns[txn_id].txn_id != 0, "Txn id does not exist");
        
        offset += 32;
        address user = address(get_bytes(ack_msg, 20, offset));
        require(user == m_txns[txn_id].user);

        offset += 20;
        address eth_addr = address(get_bytes(ack_msg, 20, offset));
        require(eth_addr == m_txns[txn_id].eth_addr);

        offset += 20;
        uint sbtc_amount = uint(get_bytes(ack_msg, 32, offset));
        require(sbtc_amount == m_txns[txn_id].sbtc_amount);

        m_txns[txn_id].ack_msg = ack_msg;  /* TODO: Check copy/reference during assignment */
        m_txns[txn_id].ack_msg_hash = ack_msg_hash; 
        m_txns[txn_id].v = v;
        m_txns[txn_id].r = r;
        m_txns[txn_id].s = s;
        m_txns[txn_id].state = TxnStates.ACKNOWLEDGED; 

        emit Ack(ack_msg, ack_msg_hash, v, r, s); /* User watches this event and verifies info is correct */
        /* TODO: What does user do if the info here is not correct? */
    }
}
