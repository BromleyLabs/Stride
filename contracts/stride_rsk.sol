pragma solidity ^0.4.23;

/* User side contract on RSK for Atomic Swap */

import "erc20.sol";
import "mortal.sol";
import "safe_math.sol";

contract StrideRSKContract is mortal {
    using SafeMath for uint;

    enum FwdTxnStates {UNINITIALIZED, CREATED, TRANSFERRED, EXECUTED, REFUNDED}
    enum RevTxnStates {UNINITIALIZED, DEPOSITED, TRANSFERRED, CUSTODIAN_CHALLENGE_ACCEPTED}  

    struct ForwardTxn {
        uint txn_id; 
        address user_rsk; /* RSK address */
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint sbtc_amount;
        FwdTxnStates state;
    } 

    struct ReverseTxn {
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

    event FwdUserTransactionCreated(uint txn_id, address user_rsk, address custodian_rsk);
    event FwdUserTransferred(uint txn_id);
    event FwdCustodianExecutionSuccess(uint txn_id, string pwd_str); 
    event FwdRefundedToUser(uint txn_id);

    event RevCustodianDeposited(uint txn_id, bytes32 ack_hash); 
    event RevTransferredToUser(uint txn_id);
    event RevCustodianChallengeAccepted(uint txn_id);

    function set_custodian(address addr) public {
        require(msg.sender == m_owner);
        m_custodian_rsk = addr;
    }

    function fwd_create_transaction(uint txn_id, bytes32 custodian_pwd_hash, 
                                uint timeout_interval, uint sbtc_amount) public { /* By user */
        require(m_fwd_txns[txn_id].txn_id != txn_id, "Transaction already exists");
        m_fwd_txns[txn_id] = ForwardTxn(txn_id, msg.sender, custodian_pwd_hash, timeout_interval,
                                    block.number, sbtc_amount, FwdTxnStates.CREATED);
        emit FwdUserTransactionCreated(txn_id, msg.sender, m_custodian_rsk);
    }

    function fwd_transfer_to_contract(uint txn_id) public payable { /* To be called by user */
        ForwardTxn memory txn = m_fwd_txns[txn_id]; /* Convenience. TODO: Check if this is reference or a copy */
        require(msg.sender == txn.user_rsk);
        require(txn.state == FwdTxnStates.CREATED);
        require(msg.value == txn.sbtc_amount, "Sent SBTC amount does not match"); 
 
        txn.state = FwdTxnStates.TRANSFERRED;

        emit FwdUserTransferred(txn_id);
    }

    /* This function main job is to send password string to user */ 
    function fwd_execute(uint txn_id, string pwd_str) public { /* Called by custodian */
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.TRANSFERRED, "Transaction not in TRANSFERRED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), "Hash does not match");
  
        m_custodian_rsk.transfer(txn.sbtc_amount);
        txn.state = FwdTxnStates.EXECUTED;

        emit FwdCustodianExecutionSuccess(txn_id, pwd_str);
    }

    /* Refund in case no action by Custodian */ 
    function fwd_request_refund(uint txn_id) public { /* Called by user */
        ForwardTxn memory txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_rsk, "Only user can call this"); 
        require(txn.state == FwdTxnStates.TRANSFERRED, "Transaction not in TRANSFERRED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        txn.user_rsk.transfer(txn.sbtc_amount);
        txn.state = FwdTxnStates.REFUNDED;

        emit FwdRefundedToUser(txn_id);
    }

    function rev_deposit(uint txn_id, address user_rsk, address dest_rsk_addr, uint sbtc_amount,
                         bytes32 ack_hash) payable public {  /* Called by custodian */
        /* The custodian should pay enough so that lock amount is covered */
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        require(address(this).balance.sub(m_locked_sbtc) >= sbtc_amount); 
        m_locked_sbtc += sbtc_amount;

        m_rev_txns[txn_id] = ReverseTxn(txn_id, user_rsk, dest_rsk_addr, ack_hash, sbtc_amount, block.number, RevTxnStates.DEPOSITED); 
         
        emit RevCustodianDeposited(txn_id, ack_hash); 
    }

    function rev_transfer(uint txn_id, bytes ack_str) public { /* Called by user */
        ReverseTxn memory txn = m_rev_txns[txn_id];
        require(msg.sender == txn.user_rsk); 
        require(txn.ack_hash == keccak256(ack_str)); 
       
        txn.dest_rsk_addr.transfer(txn.sbtc_amount);
        txn.state = RevTxnStates.TRANSFERRED; 
        
        emit RevTransferredToUser(txn_id);
    } 

    function rev_challenge(uint txn_id) public { /* Called by custodian if user hasn't acted for a while */
        ReverseTxn memory txn = m_rev_txns[txn_id];
        require(msg.sender == m_custodian_rsk); 
        require(block.number > txn.creation_block + m_sbtc_lock_interval); 
        require(txn.state == RevTxnStates.DEPOSITED);
         
        m_custodian_rsk.transfer(txn.sbtc_amount); /* TODO: Check if transfer() fails, the whole transaction is reverted */
        m_locked_sbtc -= txn.sbtc_amount;
        txn.state = RevTxnStates.CUSTODIAN_CHALLENGE_ACCEPTED;

        emit RevCustodianChallengeAccepted(txn_id);
    }

}


