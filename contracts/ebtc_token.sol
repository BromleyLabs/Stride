pragma solidity ^0.4.23;

import "safe_math.sol";
import "erc20.sol";
import "mortal.sol";

contract EBTCToken is ERC20Interface, mortal {
    using SafeMath for uint;

    string public m_symbol;
    string public  m_name;
    uint8 public m_decimals;
    uint public m_total_supply;
    address public m_issuer; /* Issuer of fresh tokens */

    mapping(address => uint) balances;
    mapping(address => mapping(address => uint)) allowed;
    
    event Issued(uint tokens);

    constructor() public {  /* Constructor */
        m_symbol = "EBTC";
        m_name = "Stride Ethereum Bitcoin Token";
        m_decimals = 18;
        m_total_supply =  0;  /* Issue fresh tokens only when needed */
        m_issuer = 0x0; /* TODO: This should be Stride contract address */
    }

    function setIssuer (address issuer) public {
        require(msg.sender == m_owner);
        m_issuer = issuer; 
    }

    function balanceOf(address tokenOwner) public constant returns (uint balance) {
        return balances[tokenOwner];
    }

    function transfer(address to, uint tokens) public returns (bool success) {
        balances[msg.sender] = balances[msg.sender].sub(tokens);
        balances[to] = balances[to].add(tokens);
        emit Transfer(msg.sender, to, tokens);
        return true;
    }

    function approve(address spender, uint tokens) public returns (bool success) {
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        return true;
    }

    function transferFrom(address from, address to, uint tokens) public returns (bool success) {
        balances[from] = balances[from].sub(tokens);
        allowed[from][msg.sender] = allowed[from][msg.sender].sub(tokens);
        balances[to] = balances[to].add(tokens);
        emit Transfer(from, to, tokens);
        return true;
    }

    function allowance(address tokenOwner, address spender) public constant returns (uint remaining) {
        return allowed[tokenOwner][spender];
    }

    function issueFreshTokens(address to, uint tokens) public returns (bool success) {
        require(msg.sender == m_issuer, "Only issuer can issue fresh tokens");     
        balances[to] = balances[to].add(tokens);
        m_total_supply = m_total_supply.add(tokens);
        emit Issued(tokens);
        return true;
    }
 
    function () public payable { /* Don't accept any Eth */
        revert();
    }
}
