/** 
  @title Contract on Ethereum for Stride transactions. The "forward" 
  transaction, for SBTC->EBTC is implemented using a cross-chain atomic swap 
  where a Custodian is involved. The "reverse" tansaction, EBTC->SBTC, however,
  is automatic and is based on user providing proof of transaction that burns 
  EBTC on Ethereum contract. 
*/ 
pragma solidity ^0.4.24;

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";

contract StrideEthContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, DEPOSITED, ISSUED, CHALLENGED}
    enum RevTxnStates {UNINITIALIZED, DEPOSITED, HASH_ADDED, 
                      SECURITY_RECOVERED, CHALLENGED}

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

    address public m_custodian_eth;
    address public m_ebtc_token_addr; /* Set by method below */ 
    uint public m_eth_ebtc_ratio_numerator = 15;  /* For collateral */
    uint public m_eth_ebtc_ratio_denominator = 1;
    uint public m_ether_lock_interval = 100; /* In blocks */
    uint public m_locked_eth = 0;

    event FwdCustodianDeposited(uint txn_id);
    event FwdEBTCIssued(uint txn_id);
    event FwdCustodianChallengeAccepted(uint txn_id);

    event RevCollateralDeposited(uint txn_id);
    event RevRedemptionInitiated(uint txn_id, address dest_rsk_addr);
    event RevHashAdded(uint txn_id, bytes32 ack_hash);
    event RevCustodianSecurityRecovered(uint txn_id, string ack_str);
    event RevUserChallengeAccepted(uint txn_id);
    event RevCustodianChallengeAccepted(uint txn_id);
   
    /* Contract initialization functions called by Owner */
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

    function set_lock_interval(uint nblocks) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_ether_lock_interval = nblocks;
    }

    /**  Send collateral Eth to contract.  Called by Custodian */
    function fwd_deposit(uint txn_id, address user_eth, 
                         bytes32 custodian_pwd_hash, uint timeout_interval, 
                         uint ebtc_amount) public payable {
        require(txn_id > 0);
        require(m_fwd_txns[txn_id].txn_id != txn_id, 
                "Transaction already exists");
        require(msg.sender == m_custodian_eth);
        uint collateral_eth = (ebtc_amount.mul(m_eth_ebtc_ratio_numerator)).
                               div(m_eth_ebtc_ratio_denominator); 
        require(msg.value == collateral_eth); 

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, user_eth, custodian_pwd_hash, 
                                        timeout_interval, block.number, 
                                        ebtc_amount, collateral_eth, 
                                        FwdTxnStates.DEPOSITED);
        
        emit FwdCustodianDeposited(txn_id); 
    }

    /** Issue EBTCs to user. Called by user */
    function fwd_issue(uint txn_id, bytes pwd_str) public { 
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_eth, "Only user can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, 
                "Transaction not in DEPOSITED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), 
                "Hash does not match");

        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(txn.user_eth, 
                                                              txn.ebtc_amount));
        txn.state = FwdTxnStates.ISSUED;

        emit FwdEBTCIssued(txn_id);
    }

    /* Called by custodian when no user action */
    function fwd_no_user_action_challenge(uint txn_id) public {
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_eth, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, 
                "Transaction not in DEPOSITED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        m_custodian_eth.transfer(txn.collateral_eth);
        txn.state = FwdTxnStates.CHALLENGED;

        emit FwdCustodianChallengeAccepted(txn_id);
    }
}

