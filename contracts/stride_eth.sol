pragma solidity ^0.4.23;

/* Contract on Ethereum for SBTC->EBTC transaction */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";

contract StrideEthContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, DEPOSITED, EXECUTED, REFUNDED}
    enum RevTxnStates {UNINITIALIZED, DEPOSITED, HASH_ADDED, SECURITY_RECOVERED, CHALLENGED}

    struct ForwardTxn { /* SBTC -> EBTC Transaction */
        uint txn_id; 
        address user_eth; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks */
        uint creation_block; /* When this transaction was created */ 
        uint ebtc_amount; 
        uint collateral_eth; /* Calculated */
        FwdTxnStates state;
    }  /* TODO: What is the cost of this storage? */

    struct ReverseTxn { /* EBTC -> SBTC transaction */
        uint txn_id;
        address user_eth;
        address dst_rsk; /* Destination address on RSK */ 
        uint ebtc_amount;  
        uint creation_block;
        bytes32 ack_hash;
        uint security_eth; 
        RevTxnStates state; 
    }

    mapping (uint => ForwardTxn) public m_fwd_txns; 
    mapping (uint => ReverseTxn) public m_rev_txns; 

    address m_custodian_eth;
    address m_ebtc_token_addr; /* Set by method below */ 
    uint m_eth_ebtc_ratio_numerator = 15; 
    uint m_eth_ebtc_ratio_denominator = 1;
    uint public m_penalty; /* Custodian penalty in Eth for reverse txn for not sending ack to user */ 
    uint m_max_ack_delay = 200; /* In blocks. Ack has to be sent by custodian within so many block numbers */
    uint m_ether_lock_interval = 100; /* In blocks */
    uint m_locked_eth = 0;

    event FwdCustodianDeposited(uint txn_id);
    event FwdUserExecutionSuccess(uint txn_id);
    event FwdRefundedToCustodian(uint txn_id);

    event RevRedemptionInitiated(uint txn_id, address dest_rsk_addr);
    event RevHashAdded(uint txn_id);
    event RevCustodianSecurityRecovered(uint txn_id, bytes ack_str);
    event RevUserChallengeAccepted(uint txn_id);
   
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

    /* Called by custodian. Send collateral Eth to contract */
    function fwd_deposit(uint txn_id, address user_eth, bytes32 custodian_pwd_hash, 
                                    uint timeout_interval, uint ebtc_amount) public payable {
        require(m_fwd_txns[txn_id].txn_id != txn_id, "Transaction already exists");
        require(msg.sender == m_custodian_eth);
        uint collateral_eth = (ebtc_amount.mul(m_eth_ebtc_ratio_numerator)).div(m_eth_ebtc_ratio_denominator); 
        require(msg.value == collateral_eth); 

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, user_eth, custodian_pwd_hash, timeout_interval,
                                    block.number, ebtc_amount, collateral_eth, FwdTxnStates.DEPOSITED);
        
        emit FwdCustodianDeposited(txn_id); 
    }

    /* Called by user */
    function fwd_execute(uint txn_id, string pwd_str) public { 
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_eth, "Only user can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, "Transaction not in DEPOSITED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");

        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(txn.user_eth, txn.ebtc_amount));
        txn.state = FwdTxnStates.EXECUTED;

        emit FwdUserExecutionSuccess(txn_id);
    }

    function fwd_request_refund(uint txn_id) public { /* Called by custodian */
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_eth, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, "Transaction not in DEPOSITED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));
        m_custodian_eth.transfer(txn.collateral_eth);
        txn.state = FwdTxnStates.REFUNDED;

        emit FwdRefundedToCustodian(txn_id);
    }

    /* Called by user */
    function rev_request_redemption(uint txn_id, address dest_rsk_addr, uint ebtc_amount) public { 
        /* User creates a unique redemption id */
        /* Assuming this contract has been given approval to move funds */ 
        require(m_rev_txns[txn_id].txn_id != txn_id, "Transaction already exists");
        uint security_eth =  (ebtc_amount.mul(m_eth_ebtc_ratio_numerator)).div(m_eth_ebtc_ratio_denominator); 
        require(address(this).balance.sub(m_locked_eth) >= security_eth); 

        EBTCToken(m_ebtc_token_addr).transferFrom(msg.sender, this, ebtc_amount);
        EBTCToken(m_ebtc_token_addr).burnTokens(ebtc_amount);
        
        m_locked_eth += security_eth;  /* Lock Ether */
        m_rev_txns[txn_id] = ReverseTxn(txn_id, msg.sender, dest_rsk_addr, ebtc_amount, 
                                        block.number, 0, security_eth, RevTxnStates.DEPOSITED); 

        emit RevRedemptionInitiated(txn_id, dest_rsk_addr);
    } 

   /* Called by user */
   function rev_add_hash(uint txn_id, bytes32 ack_hash) public { 
       ReverseTxn memory txn = m_rev_txns[txn_id];
       require(msg.sender == txn.user_eth);
       require(txn.state == RevTxnStates.DEPOSITED);
       txn.ack_hash = ack_hash;
       txn.state = RevTxnStates.HASH_ADDED;
       
       emit RevHashAdded(txn_id);
   } 
    
   /* Called by custodian */ 
   function rev_recover_security_deposit(uint txn_id, bytes ack_str) public {
       ReverseTxn memory txn = m_rev_txns[txn_id];
       require(msg.sender == m_custodian_eth);
       require(txn.state == RevTxnStates.HASH_ADDED);
       require(txn.ack_hash == keccak256(ack_str)); 

       m_custodian_eth.transfer(txn.security_eth); 
       m_locked_eth -= txn.security_eth; /* Unlock Ether */
       txn.state = RevTxnStates.SECURITY_RECOVERED; 

       emit RevCustodianSecurityRecovered(txn_id, ack_str);
   } 

   
   /* Called by user */
   function rev_no_action_challenge(uint txn_id) public { 
       ReverseTxn memory txn = m_rev_txns[txn_id];
       require(msg.sender == txn.user_eth);
       require(txn.state == RevTxnStates.DEPOSITED || txn.state == RevTxnStates.HASH_ADDED);
       require(block.number > txn.creation_block + m_ether_lock_interval); 
       
       txn.user_eth.transfer(txn.security_eth);
       txn.state = RevTxnStates.CHALLENGED;

       emit RevUserChallengeAccepted(txn_id);
   }
   
}


