pragma solidity ^0.4.23;

/* User side contract on RSK for Atomic Swap */

import "erc20.sol";
import "mortal.sol";
import "safe_math.sol";

contract StrideRSKContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, DEPOSITED, EXECUTED, REFUNDED}
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

    address m_custodian_rsk;   
    uint m_locked_sbtc = 0;
    uint m_sbtc_lock_interval = 100;  /* In blocks */

    event FwdUserDeposited(uint txn_id);
    event FwdCustodianExecutionSuccess(uint txn_id, string pwd_str); 
    event FwdRefundedToUser(uint txn_id);

    event RevCustodianDeposited(uint txn_id, bytes32 ack_hash); 
    event RevTransferredToUser(uint txn_id);
    event RevCustodianChallengeAccepted(uint txn_id);

    function set_custodian(address addr) public {
        require(msg.sender == m_owner);
        m_custodian_rsk = addr;
    }

    /* Called by user.  Transfer SBTC to contract */
    function fwd_deposit(uint txn_id, bytes32 custodian_pwd_hash, 
                                uint timeout_interval) public payable {
        require(m_fwd_txns[txn_id].txn_id != txn_id, "Transaction already exists");
        require(msg.value > 0, "SBTC cannot be 0"); /* NOTE: custodian may want to check if this amount is as per agreed while hash off-chain transaction */

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, msg.sender, custodian_pwd_hash, timeout_interval,
                                    block.number, msg.value, FwdTxnStates.DEPOSITED);
        emit FwdUserDeposited(txn_id);
    }

    /* Called by custodian. Send password string to user. */
    function fwd_execute(uint txn_id, string pwd_str) public { 
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, "Transaction not in DEPOSITED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");
  
        m_custodian_rsk.transfer(txn.sbtc_amount);
        txn.state = FwdTxnStates.EXECUTED;

        emit FwdCustodianExecutionSuccess(txn_id, pwd_str);
    }

    /* Called by user. Refund in case no action by Custodian */ 
    function fwd_request_refund(uint txn_id) public {
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_rsk, "Only user can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, "Transaction not in DEPOSITED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        txn.user_rsk.transfer(txn.sbtc_amount);
        txn.state = FwdTxnStates.REFUNDED;

        emit FwdRefundedToUser(txn_id);
    }

    /* Called by custodian. Send enough SBTCs to contract to pay to user. */
    function rev_deposit(uint txn_id, address user_rsk, address dest_rsk_addr, uint sbtc_amount,
                         bytes32 ack_hash) payable public {  
        /* The custodian should pay enough so that lock amount is covered */
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        require(address(this).balance.sub(m_locked_sbtc) >= sbtc_amount); 
        m_locked_sbtc += sbtc_amount;

        m_rev_txns[txn_id] = ReverseTxn(txn_id, user_rsk, dest_rsk_addr, ack_hash, sbtc_amount, 
                                        block.number, RevTxnStates.DEPOSITED); 
         
        emit RevCustodianDeposited(txn_id, ack_hash); 
    }

    /* Called by user.  Transfer SBTCs to destination address */
    function rev_transfer(uint txn_id, bytes ack_str) public { 
        ReverseTxn memory txn = m_rev_txns[txn_id];
        require(msg.sender == txn.user_rsk); 
        require(txn.ack_hash == keccak256(ack_str)); 
       
        txn.dest_rsk_addr.transfer(txn.sbtc_amount);
        txn.state = RevTxnStates.TRANSFERRED; 
        
        emit RevTransferredToUser(txn_id);
    } 

    /* Called by custodian. Recover custodian's SBTCs if user hasn't acted for a while. */
    function rev_challenge(uint txn_id) public { 
        ReverseTxn memory txn = m_rev_txns[txn_id];
        require(msg.sender == m_custodian_rsk); 
        require(block.number > txn.creation_block + m_sbtc_lock_interval); 
        require(txn.state == RevTxnStates.DEPOSITED);
         
        m_custodian_rsk.transfer(txn.sbtc_amount); 
        m_locked_sbtc -= txn.sbtc_amount;
        txn.state = RevTxnStates.CHALLENGED;

        emit RevCustodianChallengeAccepted(txn_id);
    }

}


