pragma solidity ^0.4.23;

/* Contract on RSK for Stride transactions */ 

import "erc20.sol";
import "mortal.sol";
import "safe_math.sol";

contract StrideRSKContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, DEPOSITED, TRANSFERRED, CHALLENGED}
    enum RevTxnStates {UNINITIALIZED, DEPOSITED, TRANSFERRED, CHALLENGED}  

    struct ForwardTxn {  /* SBTC -> EBTC Transaction */
        uint txn_id; 
        address user_rsk; /* RSK address */
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint sbtc_amount;
        FwdTxnStates state;
    } 

    struct ReverseTxn {  /* EBTC -> SBTC Transaction */
        uint txn_id; 
        address user_rsk;
        address dest_rsk_addr;
        bytes32 ack_hash; 
        uint sbtc_amount;
        uint creation_block;
        RevTxnStates state;
    }

    mapping (uint => ForwardTxn) public m_fwd_txns;  /* TODO: Efficient and cheaper storage and purge strategy of transactions */ 
    mapping (uint => ReverseTxn) public m_rev_txns; 

    address public m_custodian_rsk;   
    uint public m_locked_sbtc = 0;
    uint public m_sbtc_lock_interval = 100;  /* In blocks. */

    event FwdUserDeposited(uint txn_id);
    event FwdTransferredToCustodian(uint txn_id, string pwd_str); 
    event FwdUserChallengeAccepted(uint txn_id);

    event RevCustodianDeposited(uint txn_id, bytes32 ack_hash); 
    event RevTransferredToUser(uint txn_id);
    event RevCustodianChallengeAccepted(uint txn_id);

    /* Contract initialization functions called by Owner */
    function set_custodian(address addr) public {
        require(msg.sender == m_owner);
        m_custodian_rsk = addr;
    }

    function set_lock_interval(uint nblocks) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_sbtc_lock_interval = nblocks;
    }

    /* Called by user. Transfer SBTC to contract */
    function fwd_deposit(uint txn_id, bytes32 custodian_pwd_hash, 
                                uint timeout_interval) public payable {
        require(txn_id > 0);
        require(m_fwd_txns[txn_id].txn_id != txn_id, "Transaction already exists");
        require(msg.value > 0, "SBTC cannot be 0"); /* NOTE: custodian may want to check if this amount is as per agreed while hash off-chain transaction */

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, msg.sender, custodian_pwd_hash, timeout_interval,
                                    block.number, msg.value, FwdTxnStates.DEPOSITED);
        emit FwdUserDeposited(txn_id);
    }

    /* Called by custodian. Send password string to user and transfer SBTC to custodian */
    function fwd_transfer(uint txn_id, string pwd_str) public { 
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, "Transaction not in DEPOSITED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");
  
        m_custodian_rsk.transfer(txn.sbtc_amount);
        txn.state = FwdTxnStates.TRANSFERRED;

        emit FwdTransferredToCustodian(txn_id, pwd_str);
    }

    /* Called by user. Refund in case no action by Custodian */ 
    function fwd_no_custodian_action_challenge(uint txn_id) public {
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_rsk, "Only user can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, "Transaction not in DEPOSITED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        txn.user_rsk.transfer(txn.sbtc_amount);
        txn.state = FwdTxnStates.CHALLENGED;

        emit FwdUserChallengeAccepted(txn_id);
    }

    /* Called by custodian. Send enough SBTCs to contract to pay to user. */
    function rev_deposit(uint txn_id, address user_rsk, address dest_rsk_addr, uint sbtc_amount,
                         bytes32 ack_hash) payable public {  
        require(txn_id > 0);
        require(m_rev_txns[txn_id].txn_id != txn_id, "Transaction already exists");
        /* The custodian should pay enough so that lock amount is covered */
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        /* TODO: Ensure that custodian has transferred enough to satify condition below */
        m_locked_sbtc += sbtc_amount;

        m_rev_txns[txn_id] = ReverseTxn(txn_id, user_rsk, dest_rsk_addr, ack_hash, sbtc_amount, 
                                        block.number, RevTxnStates.DEPOSITED); 
         
        emit RevCustodianDeposited(txn_id, ack_hash); 
    }

    /* Called by user.  Transfer SBTCs to destination address */
    function rev_transfer(uint txn_id, string ack_str) public { 
        ReverseTxn storage txn = m_rev_txns[txn_id];
        require(msg.sender == txn.user_rsk, "Only RSK user can call this"); 
        require(txn.ack_hash == keccak256(ack_str), "Hash does not match"); 
        require(block.number <= txn.creation_block + m_sbtc_lock_interval, "Timed out");  /* Within certain time period */
       
        txn.dest_rsk_addr.transfer(txn.sbtc_amount);
        txn.state = RevTxnStates.TRANSFERRED; 
        
        emit RevTransferredToUser(txn_id);
    } 

    /* Called by custodian. Recover custodian's SBTCs if user hasn't acted for a while. */
    function rev_challenge(uint txn_id) public { 
        ReverseTxn storage txn = m_rev_txns[txn_id];
        require(msg.sender == m_custodian_rsk); 
        require(block.number > txn.creation_block + m_sbtc_lock_interval); 
        require(txn.state == RevTxnStates.DEPOSITED);
         
        m_custodian_rsk.transfer(txn.sbtc_amount); 
        m_locked_sbtc -= txn.sbtc_amount;
        txn.state = RevTxnStates.CHALLENGED;

        emit RevCustodianChallengeAccepted(txn_id);
    }

}


