pragma solidity ^0.4.23;

contract mortal {
    address public m_owner = msg.sender;  /* Whoever deploys this contract */ 
    function kill() public { if (msg.sender == m_owner) selfdestruct(m_owner); }
}
