pragma solidity ^0.4.23;

/* Contract on RSK for Stride transactions */ 

import "safe_math.sol";
import "mortal.sol";
import "utils.sol";
import "github.com/oraclize/ethereum-api/oraclizeAPI_0.5.sol";

contract StrideRSKContract is mortal, usingOraclize {
    using SafeMath for uint;
    using StrideUtils for bytes;

    struct RevTxn {
        bytes32 txn_hash;
        bool redeemed;
    }

    address public m_eth_addr; /* Set by method below */
    mapping(bytes32 => RevTxn) m_rev_txns;
    mapping(bytes32 => bytes32) m_query_map;
    uint public m_min_confirmations = 30;
    string public m_stride_server_url = "binary(https://sectechbromley.ddns.net/stride/ethereum/ropsten).slice(0, 136)";

    event UserDeposited(address userRSK, uint sbtc_amount);
    event UserRedeemed(address dest_addr, uint sbtc_amount);

    function setStrideServerURL(string url) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_stride_server_url = url;
    }

    function setEthContractAddr(address addr) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_eth_addr = addr;
    } 

    function setMinConfirmations(uint n) public {
        require(msg.sender == m_owner, "Only owner can set this");
        m_min_confirmations = n;
    }

    function depositSBTC(address eth_dest_addr) public payable {
        emit UserDeposited(msg.sender, msg.value); 
    }

    /* Called by Oraclize. 
       result bytes format: current_block(32), txn_block(32), 
                            contract_address(20), dest_addr(20), sbtc(32)
    */  
    function __callback(bytes32 query_id, string result) public {
        require(msg.sender != oraclize_cbAddress());

        bytes32 txn_hash = m_query_map[query_id];
        RevTxn storage txn = m_rev_txns[txn_hash];

        require(!txn.redeemed, "Transaction already issued");

        bytes memory b = bytes(result);
        require(b.length > 0, "Transaction incorrect");

        uint offset = 0; 
        uint current_block = uint(b.getBytes32(offset));

        offset += 32;  
        uint txn_block = uint(b.getBytes32(offset));

        require(current_block - txn_block > m_min_confirmations, 
                "Confirmations not enough");

        offset += 32;  
        address to_addr = address(b.getBytes20(offset));
        require(to_addr == m_eth_addr, "To address does not match");

        offset += 20;  
        address dest_addr = address(b.getBytes20(offset));

        offset += 20;  
        uint sbtc_amount = uint(b.getBytes32(offset)); /* == ebtc */
   
        dest_addr.transfer(sbtc_amount);
       
        txn.redeemed = true;

        delete m_query_map[query_id];
    
        emit UserRedeemed(dest_addr, sbtc_amount);
    }

    /* Called by user. 
       jsonHashRequest: '{"jsonrpc" : "2.0", "id" : 0, "method" : 
       "eth_getTransactionByHash", "params" : ["0x<transaction hash>"]}'
    */
    function redeem(bytes32 txn_hash, string json_request) public { 
        /* There should be enough balance for all Oraclize queries */
        require(oraclize_getPrice("URL")  > address(this).balance, 
                                  "Oraclize query not send"); 

        /* Obtain transaction info from RSK */ 
        bytes32 query_id;
        query_id = oraclize_query(
                      "URL", 
                      m_stride_server_url,
                      json_request); 

       if(m_rev_txns[txn_hash].txn_hash != txn_hash) /* May already exist */ 
           m_rev_txns[txn_hash] = RevTxn(txn_hash, false); 

       m_query_map[query_id] = txn_hash;
    }
} 
