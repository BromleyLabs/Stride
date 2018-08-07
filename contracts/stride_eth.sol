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

//import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";

contract StrideEthContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, DEPOSITED, ISSUED, CHALLENGED}

    struct ForwardTxn { /* SBTC -> EBTC Transaction */
        uint txn_id; 
        address user_eth; 
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint creation_block; /* When this transaction was created */ 
        uint ebtc_amount; 
        FwdTxnStates state;
    }  

    mapping (uint => ForwardTxn) public m_fwd_txns; 

    address public m_custodian_addr = address(0);
    address public m_ebtc_token_addr = address(0); /* Set by method below */ 
    uint m_event_nonce = 0; /* To establish uniqueness of transaction receipt */
    uint public m_lock_interval; /* In blocks */

    event FwdCustodianDeposited(uint txn_id, address user_eth, 
                                uint ebtc_amount);
    event FwdEBTCIssued(uint txn_id);
    event EBTCSurrendered(address sender, uint ebtc_amount, uint block_number,
                          uint event_nonce);
   
    constructor(address ebtc_token_addr, address custodian_addr, 
                uint lock_interval) public {
        m_ebtc_token_addr = ebtc_token_addr;
        m_custodian_addr = custodian_addr; 
        m_lock_interval = lock_interval;
    }

    /**
     * @dev Deposit EBTC to contract.  Called by custodian. It is assumed that
     * custodian has given approval for this contract to transfer EBTCs.
     */
    function fwd_deposit(uint txn_id, address user_eth, 
                         bytes32 custodian_pwd_hash, uint ebtc_amount) 
                         public {
        require(txn_id > 0);
        require(m_fwd_txns[txn_id].txn_id != txn_id, 
                "Transaction already exists");
        require(msg.sender == m_custodian_addr);

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, user_eth, custodian_pwd_hash, 
                                        block.number, ebtc_amount, 
                                        FwdTxnStates.DEPOSITED);

        require(EBTCToken(m_ebtc_token_addr).transferFrom(msg.sender, 
                                                          address(this), 
                                                          ebtc_amount));
           
        
        emit FwdCustodianDeposited(txn_id, user_eth, ebtc_amount); 
    }

    /** 
     * @dev Issue EBTCs to user. Called by user. 
     */
    function fwd_issue_ebtc(uint txn_id, bytes pwd_str) public { 
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_eth, "Only user can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, 
                "Transaction not in DEPOSITED state");
        require(block.number <= (txn.creation_block + m_lock_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), 
                "Hash does not match");

        txn.state = FwdTxnStates.ISSUED; 

        require(EBTCToken(m_ebtc_token_addr).transfer(txn.user_eth, 
                                                      txn.ebtc_amount));

        emit FwdEBTCIssued(txn_id);
    }

    /** 
     * @dev Challenge by custodian for no user action. 
     */
    function fwd_no_user_action_challenge(uint txn_id) public {
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_addr, "Only custodian can call"); 
        require(txn.state == FwdTxnStates.DEPOSITED, 
                "Transaction not in DEPOSITED state"); 
        require(block.number > (txn.creation_block + m_lock_interval));

        txn.state = FwdTxnStates.CHALLENGED;

        require(EBTCToken(m_ebtc_token_addr).transfer(m_custodian_addr,
                                                      txn.ebtc_amount));
    }

    /** 
     * @dev Function called by user to redeem EBTC. It is assumed that user has
     * approved EBTC transfer by this contract. The function burns the EBTCs
     * by sending to a NULL address. The event generated here will be part
     * of logs in the transaction receipt. RSK contract will verify transaction
     * receipt of this transaction, read rsk_dest_addr and ebtc_amount values
     * from logs and transfer equivalent SBTC.
     * @param ebtc_amount uint in Wei
     * @param rsk_dest_addr address on RSK to which equivalent SBTCs need to be
     *  transferred.  
     */
    function rev_redeem(address rsk_dest_addr, uint ebtc_amount) public {
       require(EBTCToken(m_ebtc_token_addr).burn(msg.sender, ebtc_amount), 
               "Could not burn EBTCs");

       emit EBTCSurrendered(rsk_dest_addr, ebtc_amount, block.number, 
                            m_event_nonce);
       m_event_nonce += 1;
   }
}


