pragma solidity ^0.4.24;

import "rlp.sol";

contract EthProof {
    using RLP for RLP.RLPItem;
    using RLP for RLP.Iterator;
    using RLP for bytes;

    mapping (bytes32 => BlockHeader) m_blocks;

    struct BlockHeader {
      uint      prev_block_hash; // 0
      bytes32   state_root;      // 3
      bytes32   txn_root;        // 4
      bytes32   receipt_root;    // 5
    }

    /** Helper function */
    function parse_block_header(bytes rlp_header) pure internal 
                               returns (BlockHeader) {
        BlockHeader memory header;
        RLP.Iterator memory it = rlp_header.toRLPItem().iterator();

        uint idx;
        while(it.hasNext()) {
            if (idx == 0) 
                header.prev_block_hash = it.next().toUint();
            else if (idx == 3) 
                header.state_root = bytes32(it.next().toUint());
            else if (idx == 4) 
                header.txn_root = bytes32(it.next().toUint());
            else if (idx == 5) 
                header.receipt_root = bytes32(it.next().toUint());
            else 
                it.next();
           idx++;
       }
       return header;
    }

    /**
      Submit Ethereum block headers.  Assumption here is headers are valid. No
      validy check in this function.
      TODO: Who is authorized to submit?
     */
    function submit_block(bytes32 block_hash, bytes rlp_header) public {
        BlockHeader memory header = parse_block_header(rlp_header);
        m_blocks[block_hash] = header;
    }

    /** Verify if a transaction is indeed present in a block */
    function check_txn_proof(bytes32 block_hash, bytes rlp_stack, 
                             uint[] indexes, bytes txn_prefix, bytes rlp_txn) 
                             public returns (bool) {
        bytes32 txn_root = m_blocks[block_hash].txn_root;
        if (check_proof(txn_root, rlp_stack, indexes, txn_prefix, rlp_txn)) 
            return true;
        else 
            return false;
    }

    function check_receipt_proof(bytes32 block_hash, bytes rlp_stack, 
                                 uint[] indexes, bytes receipt_prefix, 
                                 bytes rlp_receipt) public returns (bool) {
        bytes32 receipt_root = m_blocks[block_hash].receipt_root;
        if (check_proof(receipt_root, rlp_stack, indexes, receipt_prefix, 
                        rlp_receipt)) 
            return true;
        else 
            return false;
   
    }

    function check_proof(bytes32 root_hash, bytes rlp_stack, uint[] indexes, 
                        bytes value_prefix, bytes rlp_value) 
                        public returns (bool) {
        RLP.RLPItem[] memory stack = rlp_stack.toRLPItem().toList();
        bytes32 node_hash = root_hash; 
        bytes memory curr_node; 
        RLP.RLPItem[] memory curr_node_list;
   
        for (uint i = 0; i < stack.length; i++) {
            if (i == stack.length - 1) {
                curr_node = stack[i].toBytes();
                if (node_hash != keccak256(curr_node))
                    return false; 
                curr_node_list = stack[i].toList();
                RLP.RLPItem memory value = 
                    curr_node_list[curr_node_list.length - 1];
                if (keccak256(abi.encodePacked(value_prefix, rlp_value)) == 
                              keccak256(value.toBytes())) 
                    return true;
                else 
                    return false;
            }

            curr_node = stack[i].toBytes();
            if (node_hash != keccak256(curr_node))
                return false;
            curr_node_list = stack[i].toList();
            node_hash = curr_node_list[indexes[i]].toBytes32();
        }
    }
}
