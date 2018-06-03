pragma solidity ^0.4.23;

/* Contract on Ethereum for Stride transactions */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";
import "github.com/oraclize/ethereum-api/oraclizeAPI_0.5.sol";
import "JsmnSolLib.sol";

contract StrideEthContract is mortal,usingOraclize {

    struct FwdTxn {
        bytes32 txnHash;
        bytes32 txnQueryId; 
        bytes32 blockQueryId;
        uint state;
        bool issued;
    }

    string public rskOracleURL = "http://ropsten.bromleylabs.io";
    address public rskContractAddr = 0x0; 
    mapping public (bytes32 => FwdTxn) fwdTxns; /* queryId => FwdTxn */
    bytes32 txnQueryId;
    bytes32 blockQueryId;

    event LogNewOraclizeQuery(string description);

    function setRSKContractAddr(address addr) public {
        require(msg.sender == m_owner, "Only owner can set this");
        rskContractAddr = addr;
    } 

    function setRSKOracleURL(string url) public {
        require(msg.sender == m_owner, "Only owner can set this");
        rskOracleURL = url; 
    } 

    function __callback(bytes32 queryId, string result) {
        require(msg.sender != oraclize_cbAddress());
        if (queryId == fwdTxns[queryId].txnQueryId) {
            /* Parse txn json */
        }

        if (queryId == fwdTxns[queryId].blockQueryId) { 
            /* Parse block number */
        }

        delete validIds[queryId]; 
    }

    /* Called by user. 
       jsonHashRequest: '{"jsonrpc" : "2.0", "id" : 0, "method" : 
       "eth_getTransactionByHash", "params" : ["0x<transaction hash>"]}'
    */
    function issueEBTC(bytes32 txnHash, string jsonHashRequest) public { 
        /* There should be enough balance for all Oraclize queries */
        require(
            oraclize_getPrice("URL") * 2 > this.balance, 
            "Oraclize query not send"
        ); 

        /* Obtain transaction info from RSK */ 
        txnQueryId = oraclize_query(
            "URL", 
            "json(http://ropsten.bromleylabs.io).result",
            jsonHashRequest
       ); 

        /* Obtain latest block number from RSK */ 
        blockQueryId = oraclize_query(
            "URL", 
            "json(http://ropsten.bromleylabs.io).result",
            '{"jsonrpc" : "2.0", "id" : 0, "method" : "eth_blockNumber",\
                "params" : []}'
        );

        FwdTxn txn = FwdTxn(txnHash, 0, false);
        fwdTxns[txnQueryId] = txn; 
        fwdTxns[blockQueryId] = txn; 
    }

}

