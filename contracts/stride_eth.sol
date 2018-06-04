pragma solidity ^0.4.23;

/* Contract on Ethereum for Stride transactions */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";
import "github.com/oraclize/ethereum-api/oraclizeAPI_0.5.sol";

contract StrideEthContract is mortal,usingOraclize {

    struct FwdTxn {
        bytes32 txn_hash;
        bool issued;
    }

    address public m_rsk_addr; /* Set by method below */
    address public m_ebtc_token_addr; /* Set by method below */
    mapping(bytes32 => FwdTxn) m_fwd_txns;
    mapping(bytes32 => bytes32) m_query_map;
    uint public m_min_confirmations = 30;

    function setRSKContractAddr(address addr) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_rsk_addr = addr;
    } 

    function setMinConfirmations(uint n) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_min_confirmations = n;
    }

    function setEBTCTokenAddress(address addr) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_ebtc_token_addr = addr;
    }

    /* Utility function to extract bytes from a byte array given an offset 
       and returns as bytes32 */
    function getBytes32(bytes b, uint offset) private pure returns (bytes32) {
        bytes32 out;
        for (uint i = 0; i < 32; i++) 
            out |= bytes32(b[offset + i] & 0xFF) >> (i * 8); 
        return out;
    }

    function getBytes20(bytes b, uint offset) private pure returns (bytes20) {
        bytes20 out;
        for (uint i = 0; i < 20; i++) 
            out |= bytes20(b[offset + i] & 0xFF) >> (i * 8); 
        return out;
    }

    /* result bytes format:
       current_block(32), txn_block(32), contract_address(20), dest_addr(20), 
       sbtc(32)
    */  
    function __callback(bytes32 query_id, string result) public {
        require(msg.sender != oraclize_cbAddress());

        bytes32 txn_hash = m_query_map[query_id];
        FwdTxn storage txn = m_fwd_txns[txn_hash];
        require(!txn.issued, "Transaction already issued");

        bytes memory b = bytes(result);

        uint offset = 0; 
        uint txn_block = uint(getBytes32(b, offset));

        offset += 32;  
        uint current_block = uint(getBytes32(b, offset));

        require(current_block - txn_block > m_min_confirmations, 
                "Confirmations not enough");

        offset += 32;  
        address to_addr = address(getBytes20(b, offset));
        require(to_addr == m_rsk_addr, "To address does not match");

        offset += 20;  
        address dest_addr = address(getBytes20(b, offset));

        offset += 20;  
        uint ebtc_amount = uint(getBytes32(b, offset)); /* == sbtc */
   
        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(dest_addr,
                                                              ebtc_amount));
        txn.issued = true;

        delete m_query_map[query_id];
    }

    /* Called by user. 
       jsonHashRequest: '{"jsonrpc" : "2.0", "id" : 0, "method" : 
       "eth_getTransactionByHash", "params" : ["0x<transaction hash>"]}'
    */
    function issueEBTC(bytes32 txn_hash, string json_request) public { 
        /* There should be enough balance for all Oraclize queries */
        require(oraclize_getPrice("URL")  > address(this).balance, 
                                  "Oraclize query not send"); 

        /* Obtain transaction info from RSK */ 
        bytes32 query_id;
        query_id = oraclize_query("URL", 
                                  "json(http://ropsten.bromleylabs.io).result",
                                  json_request); 

       if(m_fwd_txns[txn_hash].txn_hash != txn_hash) /* May already exist */ 
           m_fwd_txns[txn_hash] = FwdTxn(txn_hash, false); 

       m_query_map[query_id] = txn_hash;
    }

}

