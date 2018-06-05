pragma solidity ^0.4.23;

/* Contract on Ethereum for Stride transactions */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";
import "utils.sol";
import "github.com/oraclize/ethereum-api/oraclizeAPI_0.5.sol";


contract StrideEthContract is mortal,usingOraclize {
    using SafeMath for uint;
    using StrideUtils for bytes;

    struct FwdTxn {
        bytes32 txn_hash;
        bool issued;
    }

    address public m_rsk_addr; /* Set by method below */
    address public m_ebtc_token_addr; /* Set by method below */
    mapping(bytes32 => FwdTxn) m_fwd_txns;
    mapping(bytes32 => bytes32) m_query_map;
    uint public m_min_confirmations = 30;
    string public m_stride_server_url = "binary(http://localhost/stride/rsk/testnet);";

    event EBTCIssued(address dest_addr, uint ebtc_amount);
    event EBTCSurrendered(address user_eth, uint ebtc_amount);

    function setStrideServerURL(string url) {
        require(msg.sender == m_owner, "Only owner can set this");
        m_stride_server_url = url;
    }

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

    /* Called by Oraclize. 
       result bytes format: current_block(32), txn_block(32), 
                            contract_address(20), dest_addr(20), sbtc(32)
    */  
    function __callback(bytes32 query_id, string result) public {
        require(msg.sender != oraclize_cbAddress());

        bytes32 txn_hash = m_query_map[query_id];
        FwdTxn storage txn = m_fwd_txns[txn_hash];
        require(!txn.issued, "Transaction already issued");

        bytes memory b = bytes(result);
        require(b.length > 0, "Transaction incorrect");

        uint offset = 0; 
        uint txn_block = uint(b.getBytes32(offset));

        offset += 32;  
        uint current_block = uint(b.getBytes32(offset));

        require(current_block.sub(txn_block) > m_min_confirmations, 
                "Confirmations not enough");

        offset += 32;  
        address to_addr = address(b.getBytes20(offset));
        require(to_addr == m_rsk_addr, "To address does not match");

        offset += 20;  
        address dest_addr = address(b.getBytes20(offset));

        offset += 20;  
        uint ebtc_amount = uint(b.getBytes32(offset)); /* == sbtc */
   
        require(EBTCToken(m_ebtc_token_addr).issueFreshTokens(dest_addr,
                                                              ebtc_amount));
        txn.issued = true;

        delete m_query_map[query_id];
       
        emit EBTCIssued(dest_addr, ebtc_amount);
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
        query_id = oraclize_query(
                      "URL", 
                      m_stride_server_url, 
                      json_request); 

       if(m_fwd_txns[txn_hash].txn_hash != txn_hash) /* May already exist */ 
           m_fwd_txns[txn_hash] = FwdTxn(txn_hash, false); 

       m_query_map[query_id] = txn_hash;
    }

   function redeem(address rsk_dest_addr, uint ebtc_amount) {
       /* Assumed user has approved EBTC transfer by this contract */ 
       require(EBTCToken(m_ebtc_token_addr).transferFrom(msg.sender, 0x0, 
                                                         ebtc_amount));
       emit EBTCSurrendered(msg.sender, ebtc_amount);
   }

}

