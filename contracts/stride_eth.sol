/** 
 * @title Stride Ethereum Contract 
 * @dev Contract on Ethereum for Stride transactions. The "forward" 
 * transaction, for SBTC->EBTC is implemented using a cross-chain atomic swap 
 * where a custodian is involved. The "reverse" tansaction, EBTC->SBTC, however,
 * is automatic and is based on user providing proof of transaction that burns 
 * EBTC on Ethereum contract. 
 * 
 * @author Bon Filey (bonfiley@gmail.com)
 * Copyright 2018 Bromley Labs Inc. 
 */

pragma solidity ^0.4.24;

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";

contract StrideEthContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, DEPOSITED, ISSUED, CHALLENGED}

    struct ForwardTxn { /* SBTC -> EBTC Transaction */
        uint txn_id; 
        address user_eth; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks */
        uint creation_block; /* When this transaction was created */ 
        uint ebtc_amount; 
        uint collateral_eth; /* Calculated */
        FwdTxnStates state;
    }  

    mapping (uint => ForwardTxn) public m_fwd_txns; 

    address public m_custodian_eth;
    address public m_ebtc_token_addr; /* Set by method below */ 
    uint public m_eth_ebtc_ratio_numerator = 15;  /* For collateral */
    uint public m_eth_ebtc_ratio_denominator = 1;
    uint public m_locked_eth = 0;
    uint m_event_nonce = 0; /* To establish uniqueness of transaction receipt */

    event FwdCustodianDeposited(uint txn_id);
    event FwdEBTCIssued(uint txn_id);
    event FwdCustodianChallengeAccepted(uint txn_id);
    event EBTCSurrendered(address sender, uint ebtc_amount, uint block_number,
                          uint event_nonce);
   
    /**
     * @dev Contract initialization functions called by Owner 
     */
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

    /**
     * @dev Send collateral Ether to contract.  Called by custodian.
     */
    function fwd_deposit(uint txn_id, address user_eth, 
                         bytes32 custodian_pwd_hash, uint timeout_interval, 
                         uint ebtc_amount) public payable {
        require(txn_id > 0);
        require(m_fwd_txns[txn_id].txn_id != txn_id, 
                "Transaction already exists");
        require(msg.sender == m_custodian_eth);
        uint collateral_eth = (ebtc_amount.mul(m_eth_ebtc_ratio_numerator)).div(m_eth_ebtc_ratio_denominator); 
        require(msg.value == collateral_eth); 

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, user_eth, custodian_pwd_hash, 
                                        timeout_interval, block.number, 
                                        ebtc_amount, collateral_eth, 
                                        FwdTxnStates.DEPOSITED);
        
        emit FwdCustodianDeposited(txn_id); 
    }

    /** 
     * @dev Issue EBTCs to user. Called by user. 
     */
    function fwd_issue_ebtc(uint txn_id, bytes pwd_str) public { 
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_eth, "Only user can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, 
                "Transaction not in DEPOSITED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), 
                "Hash does not match");

        txn.state = FwdTxnStates.ISSUED; 

        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(txn.user_eth, 
                                                              txn.ebtc_amount));

        emit FwdEBTCIssued(txn_id);
    }

    /** 
     * @dev Challenge by custodian for no user action. 
     */
    function fwd_no_user_action_challenge(uint txn_id) public {
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_eth, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, 
                "Transaction not in DEPOSITED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        txn.state = FwdTxnStates.CHALLENGED;

        m_custodian_eth.transfer(txn.collateral_eth);

        emit FwdCustodianChallengeAccepted(txn_id);
    }

    /** 
     * @dev Function called by user to redeem EBTC. It is assumed that user has
     * approved EBTC transfer by this contract. The function burns the EBTCs
     * by sending to a NULL address. The corresponding collateral Ether is 
     * transferred back to custodian.  The event generated here will be part
     * of logs in the transaction receipt. RSK contract will verify transaction
     * receipt of this transaction, read rsk_dest_addr and ebtc_amount values
     * from logs and transfer equivalent SBTC.
     * @param ebtc_amount uint in Wei
     * @param rsk_dest_addr address on RSK to which equivalent SBTCs need to be
     *  transferred.  
     */
    function rev_redeem(address rsk_dest_addr, uint ebtc_amount) public {
       require(EBTCToken(m_ebtc_token_addr).transferFrom(msg.sender, 0x0, 
                                                         ebtc_amount));
       uint collateral_eth = (ebtc_amount.mul(m_eth_ebtc_ratio_numerator)).
                               div(m_eth_ebtc_ratio_denominator); 
       m_custodian_eth.transfer(collateral_eth);

       emit EBTCSurrendered(rsk_dest_addr, ebtc_amount, block.number, 
                            m_event_nonce);
       m_event_nonce += 1;
   }
}


