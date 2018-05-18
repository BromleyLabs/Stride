pragma solidity ^0.4.23;

/* Contract on Ethereum for SBTC->EBTC transaction */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";

contract ForwardEthContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, CREATED, EXECUTED, REFUNDED}
    enum RevTxnStates {UNINITIALIZED, DEPOSITED, ACKNOWLEDGED, REVERTED}

    struct ForwardTxn { /* from SBTC -> EBTC */
        uint txn_id; 
        address user_eth; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint ebtc_amount; 
        uint collateral_eth; /* Calculated */
        FwdTxnStates state;
    }  /* TODO: What is the cost of this storage? */

    struct ReverseTxn { /* from EBTC -> SBTC */
        uint txn_id;
        address user_eth;
        address user_rsk;
        uint ebtc_amount;  
        RevTxnStates state; 
        uint block_number; /* When created */
        bytes ack_msg; /* From custodian */ 
        bytes32 ack_msg_hash; 
        uint8 v; /* Signed by custodian */
        bytes32 r;
        bytes32 s;
    }

    mapping (uint => ForwardTxn) public m_fwd_txns; 
    mapping (uint => ReverseTxn) public m_rev_txns; 

    address m_custodian_eth;
    address m_ebtc_token_addr; /* Set by method below */ 
    uint m_eth_ebtc_ratio_numerator = 15; 
    uint m_eth_ebtc_ratio_denominator = 1;
    uint public m_penalty; /* Custodian penalty in Eth for reverse txn for not sending ack to user */ 
    uint m_max_ack_delay = 200; /* In blocks. Ack has to be sent by custodian within so many block numbers */

    event FwdCustodianTransactionCreated(uint txn_id, address m_custodian_eth, address user_eth);
    event FwdCustodianTransferred(uint txn_id);
    event FwdUserExecutionSuccess(uint txn_id);
    event FwdRefundedToCustodian(uint txn_id);
   
    event RevUserDeposited(address from, uint amount, uint txn_id);
    event RevCustodianAck(bytes ack_msg, bytes32 ack_msg_hash, uint8 v, bytes32 r, bytes32 s);
    event RevChallengeAccepted(uint txn_id);
 
    function set_custodian(address addr) public {
        require(msg.sender == m_owner);
        m_custodian_eth = addr;
    }

    function set_ebtc_token_address(address addr) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_ebtc_token_addr = addr; 
    } 

    function set_eth_ebtc_ratio(uint numerator, uint denominator) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_eth_ebtc_ratio_numerator = numerator;
        m_eth_ebtc_ratio_denominator = denominator;
    }

    function set_ebtc_token_addr(address addr) public {
        require(msg.sender == m_owner);
        m_ebtc_token_addr = addr;
    }

    function set_penalty(uint amount) public {
        require(msg.sender == m_owner, "Only owner can set penalty");  
        m_penalty = amount;
    }

    function set_max_ack_delay(uint nblocks) public {
        require(msg.sender == m_owner, "Only owner can set max_ack_delay");  
        m_max_ack_delay = nblocks; 
    }

    /* Utility function to extract bytes from a byte array given an offset and returns as bytes32, bytes20 */
    function get_bytes32(bytes b, uint offset) private pure returns (bytes32) {
        bytes32 out;
        for (uint i = 0; i < 32; i++) 
            out |= bytes32(b[offset + i] & 0xFF) >> (i * 8); /* CAUTION: Beware of left/right padding from bytes->bytes32  */
        return out;
    }

    function get_bytes20(bytes b, uint offset) private pure returns (bytes20) {
        bytes20 out;
        for (uint i = 0; i < 20; i++) 
            out |= bytes20(b[offset + i] & 0xFF) >> (i * 8); 
        return out;
    }
    /* With this method custodian is initializing the transaction along with sending Eth to 
       contract */
    function fwd_create_transaction(uint txn_id, address user_eth, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint ebtc_amount) public payable { /* Called by custodian */
        require(m_fwd_txns[txn_id].txn_id != txn_id, "Transaction already exists");
        require(msg.sender == m_custodian_eth);
        uint collateral_eth = (ebtc_amount.mul(m_eth_ebtc_ratio_numerator)).div(m_eth_ebtc_ratio_denominator); 
        require(msg.value == collateral_eth); 

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, user_eth, custodian_pwd_hash, timeout_interval,
                                    block.number, ebtc_amount, collateral_eth, FwdTxnStates.CREATED);
        
        emit FwdCustodianTransactionCreated(txn_id, msg.sender, user_eth);
        emit FwdCustodianTransferred(txn_id); /* TODO: this event may not be needed */
    }

    function fwd_request_refund(uint txn_id) public { /* Called by custodian */
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_eth, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.CREATED, "Transaction not in CREATED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));
        m_custodian_eth.transfer(txn.collateral_eth);
        txn.state = FwdTxnStates.REFUNDED;

        emit FwdRefundedToCustodian(txn_id);
    }

    function fwd_execute(uint txn_id, string pwd_str) public { /* Called by user */
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_eth, "Only user can call this"); 
        require(txn.state == FwdTxnStates.CREATED, "Transaction not in CREATED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");

        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(txn.user_eth, txn.ebtc_amount));
        txn.state = FwdTxnStates.EXECUTED;

        emit FwdUserExecutionSuccess(txn_id);
    }

    function rev_redeem_ebtc(uint txn_id, uint ebtc_amount, address user_rsk_addr) public { /* By user */
        /* Fresh txn_id generated by user */
        require(m_rev_txns[txn_id].txn_id != txn_id, "Transaction already exists");

        /* TODO: Do we need to ensure that custodian has deposited enough Eth for any penality when challenge is made by user */
        require(EBTCToken(m_ebtc_token_addr).transferFrom(msg.sender, this, ebtc_amount));
        require(EBTCToken(m_ebtc_token_addr).burnTokens(ebtc_amount));

        m_rev_txns[txn_id] = ReverseTxn(txn_id, msg.sender, user_rsk_addr, ebtc_amount, 
                                    RevTxnStates.DEPOSITED, block.number, "", 0, 0, 0, 0); 

        emit RevUserDeposited(msg.sender, ebtc_amount, txn_id); /* Custodian watches this event */ 
    }

    /* This function is called by custodian after receiving Deposited event.
       ack_msg byte array: txn_id(32), user_eth(20), user_rsk(20), ebtc_amount(32), block_number(32) */

    function rev_submit_ack(bytes ack_msg, bytes32 ack_msg_hash, uint8 v, bytes32 r, bytes32 s) public {
        require(msg.sender == m_custodian_eth, "Only custodian can call this");
        bytes memory prefix = "\x19Ethereum Signed Message:\n32";
        bytes32 prefixedHash = keccak256(prefix, ack_msg_hash) ; 
        require(ecrecover(prefixedHash, v, r, s) == m_custodian_eth, "Not a custodian signed msg"); 
        require(ack_msg_hash == keccak256(ack_msg), "Ack msg hash does not match"); 
       
        /* Verify if custodian has sent correct information for this transaction id */
        uint offset = 0;
        uint txn_id = uint(get_bytes32(ack_msg, offset));
        require(m_rev_txns[txn_id].txn_id != 0, "Txn id does not exist");

        ReverseTxn memory txn = m_rev_txns[txn_id];  

        /* Avoid repeated ack message for the same txn_id */
        require(txn.state == RevTxnStates.DEPOSITED, "Txn not in DEPOSITED state");
        
        offset += 32;
        address user = address(get_bytes20(ack_msg, offset));
        require(user == txn.user_eth, "User does not match");

        offset += 20;
        address user_rsk = address(get_bytes20(ack_msg, offset));
        require(user_rsk == txn.user_rsk, "User RSK address does not match");

        offset += 20;
        uint ebtc_amount = uint(get_bytes32(ack_msg, offset));
        require(ebtc_amount == txn.ebtc_amount, "EBTC amount does not match");
  
        /* TODO: Check if ack has come too late, i.e. block number limit has been exceeded */

        /* Save the ack info for further use by this contract */
        txn.ack_msg = ack_msg;  /* TODO: Check copy/reference during assignment */
        txn.ack_msg_hash = ack_msg_hash; 
        txn.v = v;
        txn.r = r;
        txn.s = s;
        txn.state = RevTxnStates.ACKNOWLEDGED; 

        emit RevCustodianAck(ack_msg, ack_msg_hash, v, r, s); /* User watches this event and verifies info is correct */
        /* TODO: What does user do if the info here is not correct? */
    }

    /* This function is called by user if user does not receive Ack event after m_max_ack_delay blocks. */
    function no_ack_challenge(uint txn_id) public {
        require(m_rev_txns[txn_id].txn_id != 0, "Txn id does not exist");
        ReverseTxn memory txn = m_rev_txns[txn_id];
        require(txn.user_eth == msg.sender, "User does not match");
        require(txn.state == RevTxnStates.DEPOSITED, "Txn has not in DEPOSITED state"); 
        require((block.number - txn.block_number) > m_max_ack_delay, "Not reached block limit"); 

        /* Give back the user all the EBTC that were deposited */
        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(txn.user_eth, txn.ebtc_amount)); /* Since they have been burnt already */
        txn.state = RevTxnStates.REVERTED;
        emit RevChallengeAccepted(txn_id);
    }
}


