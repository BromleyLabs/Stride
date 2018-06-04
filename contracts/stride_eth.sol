pragma solidity ^0.4.23;

/* Contract on Ethereum for Stride transactions */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";
import "github.com/oraclize/ethereum-api/oraclizeAPI_0.5.sol";
import "JsmnSolLib.sol";

contract StrideEthContract is mortal,usingOraclize {
    using JsmnSolLib;

    struct FwdTxn {
        bytes32 txnHash;
        bytes32 txnQueryId; 
        bytes32 blockQueryId;
        uint blockNumberOk; /* enough confirmations */
        uint txnOk; 
        bool issued;
    }

    string public rskOracleURL = "http://ropsten.bromleylabs.io";
    address public rskContractAddr = 0x0; 
    mapping (bytes32 => uint) txnQueryMap;
    mapping (bytes32 => uint) blockQueryMap; 
    mapping (string => address) helperMap;

    FwdTxn [] fwdTxns;
    event LogNewOraclizeQuery(string description);

    function setRSKContractAddr(address addr, string addr_str) public {
        require(msg.sender == m_owner, "Only owner can set this");
        rskContractAddr = addr;
        helperMap[addr_str] = rskContactAddr;
    } 

    function setRSKOracleURL(string url) public {
        require(msg.sender == m_owner, "Only owner can set this");
        rskOracleURL = url; 
    } 

    function __callback(bytes32 queryId, string result) {
        require(msg.sender != oraclize_cbAddress());
        /* Can use either map below */
        FwdTxn storage txn = fxdTnxs[txnQueryMap[queryId]]; 
        if (queryId == txn.txnQueryId) {
            Token[] memory tokens;
            (ok, tokens ntokens) =  parse(result, 29);
            /* Check To address of transaction */
            string memory toAddr = getBytes( 
                result, 
                tokens[17].start, 
                tokens[17].end
            );
            require(helperMap[toAddr] == rskContractAddr, "Incorrect To addr");
            
            /* Check "value" field in transaction */
            string memory sbtc_amount = getBytes( 
                result, 
                tokens[21].start, 
                tokens[21].end
            );


        }
        else if (queryId == txn.blockQueryId) {


        }
        else 
            revert("Incorrect queryId from Oraclize");
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

        bytes32 txnHash;
        bytes32 txnQueryId; 
        bytes32 blockQueryId;
        bool blockNumberOk; /* enough confirmations */
        bool txnOk; 
        bool issued;
        fwdTxns.push(
            FwdTxn(
                txnHash, 
                txnQueryId, 
                blockQueryId, 
                false, 
                false, 
                false,
                false
            )
        );
       txnQueryMap[txnQueryId] = fxdTxns.length - 1; /* Index */
       blockQueryMap[blockQueryId] = fxdTxns.length - 1; /* Index */
    }

}

