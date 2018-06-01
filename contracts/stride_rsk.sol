pragma solidity ^0.4.23;

/* Contract on RSK for Stride transactions */ 

import "mortal.sol";
import "safe_math.sol";

contract StrideRSKContract is mortal {
    using SafeMath for uint;

    event UserDeposited(address userRSK, uint sbtcAmount);

    function depositSBTC(address eth_dest_addr) public payable {
        emit UserDeposited(msg.sender, msg.value); 
    }
} 
