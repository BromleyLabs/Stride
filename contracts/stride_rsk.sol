/** 
  @title Contract on RSK for Stride transactions. The "forward" transaction,
  for SBTC->EBTC is implemented using a cross-chain atomic swap where a
  Custodian is involved. The "reverse" tansaction, EBTC->SBTC, however, is 
  automatic and is based on user providing proof of transaction of depositing
  EBTC on Ethereum contract. 
*/ 

pragma solidity ^0.4.24;

import "safe_math.sol";
import "mortal.sol";
import "eth_proof.sol";
import "utils.sol";

contract StrideRSKContract is mortal {
    using SafeMath for uint;
    using StrideUtils for bytes;

    enum FwdTxnStates {UNINITIALIZED, DEPOSITED, ACKNOWLEDGED, CHALLENGED}

    struct ForwardTxn {  /* SBTC -> EBTC Transaction */
        uint txn_id; 
        address user_rsk; /* RSK address */
        bytes32 custodian_pwd_hash; /* Custodian password hash */
        uint timeout_interval; /* Blocks. Arbitary */ 
        uint creation_block; 
        uint sbtc_amount;
        FwdTxnStates state;
    } 

    struct EthTxnReceipt {
        uint status;
        address contract_addr;
        bytes32 event_hash;
        uint txn_block;
        address dest_addr;
        uint ebtc_amount;
    }

    mapping (uint => ForwardTxn) public m_fwd_txns;  
    mapping (bytes32 => bool) public m_sbtc_issued; /* receipt hash => true */

    address public m_custodian_rsk;   
    address public m_eth_contract_addr;
    address public m_eth_proof_addr; /* Address of EthProof contract */
    bytes32 public m_eth_event_hash = keccak256("EBTCSurrendered(address,uint256,uint256,uint256)");
    uint public m_min_confirmations = 30;

    event FwdUserDeposited(uint txn_id);
    event FwdAckByCustodian(uint txn_id, bytes pwd_str); 

    /* Contract initialization functions called by Owner */
    function set_custodian(address addr) public {
        require(msg.sender == m_owner);
        m_custodian_rsk = addr;
    }

    function set_eth_proof_addr(address addr) public {
        require(msg.sender == m_owner);
        m_eth_proof_addr = addr;
    }

    function set_eth_contract_addr(address addr) public {
        require(msg.sender == m_owner);
        m_eth_contract_addr = addr;
    }

    function set_min_confirmations(uint n) public {
        require(msg.sender == m_owner);
        m_min_confirmations = n;
    }

    /** 
     *  Initate SBTC->EBTC transfer by first depositing SBTC to this 
     *  contract. Called by user.  
     *  Note: Custodian may want to check if this amount is as per 
     *  agreed while hash off-chain transaction 
     */
    function fwd_deposit(uint txn_id, bytes32 custodian_pwd_hash, 
                         uint timeout_interval) public payable {
        require(txn_id > 0);
        require(m_fwd_txns[txn_id].txn_id != txn_id, 
                "Transaction already exists");
        require(msg.value > 0, "SBTC cannot be 0"); 

        m_fwd_txns[txn_id] = ForwardTxn(txn_id, msg.sender, custodian_pwd_hash,
                                        timeout_interval, block.number, 
                                        msg.value, FwdTxnStates.DEPOSITED);
        emit FwdUserDeposited(txn_id);
    }

    /** 
     * Send password string to user as acknowledgment. Called by custodian
     */
    function fwd_ack(uint txn_id, bytes pwd_str) public { 
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == m_custodian_rsk, "Only custodian can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, 
                "Transaction not in DEPOSITED state");
        require(block.number <= (txn.creation_block + txn.timeout_interval));
        require(txn.custodian_pwd_hash == keccak256(pwd_str), 
                "Hash does not match");
  
        txn.state = FwdTxnStates.ACKNOWLEDGED;

        emit FwdAckByCustodian(txn_id, pwd_str);
    }

    /** 
     * Called by user. Refund in case no action by Custodian 
     */ 
    function fwd_no_custodian_action_challenge(uint txn_id) public {
        ForwardTxn storage txn = m_fwd_txns[txn_id]; 
        require(msg.sender == txn.user_rsk, "Only user can call this"); 
        require(txn.state == FwdTxnStates.DEPOSITED, "Transaction not in DEPOSITED state"); 
        require(block.number > (txn.creation_block + txn.timeout_interval));

        txn.user_rsk.transfer(txn.sbtc_amount);
        txn.state = FwdTxnStates.CHALLENGED;
    }

    /**
     * Decode Ethereum transaction receipt and read fields of interest. 2 event
     * logs are expected - we are interested in the second log which is emitted
     * by redeem function on Ethereum contract. 
     * TODO: for status == 0 RLP.toUint() may fail as length of byte
       array is 0. 
     */ 
    function parse_eth_txn_receipt(bytes rlp_txn_receipt) internal 
                                   returns (EthTxnReceipt) {
        EthTxnReceipt memory receipt = EthTxnReceipt(0,0,0,0,0,0);

        RLP.RLPItem memory item = RLP.toRLPItem(rlp_txn_receipt);
        RLP.RLPItem[] memory fields = RLP.toList(item);
        receipt.status = RLP.toUint(fields[0]);  /* See TODO note above */
     
        RLP.RLPItem[] memory logs = RLP.toList(fields[3]); 
        RLP.RLPItem[] memory log_fields = RLP.toList(logs[1]); /* Second log */
        receipt.contract_addr = RLP.toAddress(log_fields[0]);
   
        RLP.RLPItem[] memory topics = RLP.toList(log_fields[1]);
        receipt.event_hash = RLP.toBytes32(topics[0]);

        bytes memory event_data = RLP.toData(log_fields[2]);
        uint index = 0 + 12; /* Start of address in 32 bytes field */
        /* The data for some reason is all 32 bytes even for address */
        receipt.dest_addr = address(StrideUtils.get_bytes20(event_data, index)); 
        index += 20;
        receipt.ebtc_amount = uint(StrideUtils.get_bytes32(event_data, index)); 
        index += 32; 
        receipt.txn_block = uint(StrideUtils.get_bytes32(event_data, index));

        return receipt;
    }   


    /** Called by the user, this function redeems SBTC to the destination 
     *  address specified on Ethereum side.  The user provides proof of 
     *  Ethereum transaction receipt which is verified in this function. Reads
     *  logs in transaction receipt containing user RSK destination address and 
     *  SBTC amount (refer to Ethereum contract). 
     *  @param rlp_txn_receipt bytes The full transaction receipt structure 
     *  @param block_hash bytes32 Hash of the block in which Ethereum 
     *  transaction exists
     *  @param path bytes path of the Merkle proof to reach root node
     *   @param rlp_parent_nodes bytes Merkle proof in the form of trie
     */
    function rev_redeem(bytes rlp_txn_receipt, bytes32 block_hash, bytes path, bytes rlp_parent_nodes) public {

        require(m_sbtc_issued[keccak256(rlp_txn_receipt)] != true, 
                "SBTC already issued for this transaction");

        EthProof eth_proof = EthProof(m_eth_proof_addr); 
        require(eth_proof.check_receipt_proof(rlp_txn_receipt,
                block_hash, path, rlp_parent_nodes), "Incorrect proof");         
        
        EthTxnReceipt memory receipt = parse_eth_txn_receipt(rlp_txn_receipt);
        require(receipt.status == 1); /* Successful txn */
        uint curr_block =  eth_proof.m_highest_block();
        require((curr_block - receipt.txn_block) > m_min_confirmations);
        require(receipt.event_hash == m_eth_event_hash); 
        require(receipt.contract_addr == m_eth_contract_addr);

        receipt.dest_addr.transfer(receipt.ebtc_amount); /* SBTC == EBTC */ 
    
        m_sbtc_issued[keccak256(rlp_txn_receipt)] = true; 
    } 
}
