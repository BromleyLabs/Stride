pragma solidity ^0.4.23;

/* Contract on Ethereum for Stride transactions */ 

import "erc20.sol";
import "ebtc_token.sol";
import "mortal.sol";
import "github.com/oraclize/ethereum-api/oraclizeAPI_0.5.sol";
import "JsmnSolLib.sol";

contract StrideEthContract is mortal,usingOraclize {

    mapping (bytes32 => bool) public issued;
    string public rskOracleURL = "http://ropsten.bromleylabs.io";
    address public rskContractAddr = 0x0; 
    mapping public (bytes32 => bool) validIds;

    event LogNewOraclizeQuery(string description);

    function setRSKContractAddr(address addr) public {
        require(msg.sender == m_owner, "Only owner can set this");
        rskContractAddr = addr;
    } 

    function setRSKOracleURL(string url) public {
        require(msg.sender == m_owner, "Only owner can set this");
        rskOracleURL = url; 
    } 

    function issueEBTC(string jsonHashRequest) public { 
        /* Of form: '{"jsonrpc" : "2.0", "id" : 0, 
           "method" : "eth_getTransactionByHash", 
           "params" : 
        ["0x3a232165aa0ae7ae7ea94a3162ee6a8a829390f167ea83e150af204df8624239"]}'
        */

        /* There should be enough balance for all Oraclize queries */
        require(oraclize_getPrice("URL") * 2 > this.balance, 
                "Oraclize query not send"); 

        /* Obtain transaction info from RSK */ 
        bytes32 queryId; 
        queryId = oraclize_query(
            "URL", 
            "json(http://ropsten.bromleylabs.io).result",
            jsonHashRequest
        ) 
        validIds[queryId] = true;

        /* Obtain latest block number from RSK */ 
        queryId = oraclize_query(
            "URL", 
            "json(http://ropsten.bromleylabs.io).result",
            '{"jsonrpc" : "2.0", "id" : 0, "method" : "eth_blockNumber", "params" : []}')
        validIds[queryId] = true;
    }

}

