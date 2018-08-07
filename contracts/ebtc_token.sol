/**
 * @title ERC20 compliant fixed supply token - EBTC. 
 * @dev EBTC is  equivalent to SBTC on RSK chain. This is a fixed supply token
 * which is initialized during deployment of this contract.  The owner is 
 * is issued the requested amount.
 *
 * @author Bon Filey (bonfiley@gmail.com)
 *
 * Copyright 2018 Bromley Labs Inc. 
 */
pragma solidity ^0.4.24;

import "safe_math.sol";
import "mortal.sol";

contract EBTCToken is mortal { /* ERC20 compliant */
    using SafeMath for uint;

    string public m_symbol;
    string public  m_name;
    uint8 public m_decimals;
    uint public m_total_supply;

    mapping(address => uint) balances;
    mapping(address => mapping(address => uint)) allowed;

    event Transfer(address indexed from, address indexed to, uint tokens);
    event Approval(address indexed tokenOwner, address indexed spender, 
                   uint tokens);

    constructor(uint tokens) public {  /* Constructor */
        m_symbol = "EBTC";
        m_name = "Stride Ethereum Bitcoin Token";
        m_decimals = 18;
        m_total_supply = tokens;  /* Fixed supply */ 
    }

    function balanceOf(address tokenOwner) public constant returns (
                       uint balance) { 
        return balances[tokenOwner];
    }

    function transfer(address to, uint tokens) public returns (bool success) {
        balances[msg.sender] = balances[msg.sender].sub(tokens);
        balances[to] = balances[to].add(tokens);
        emit Transfer(msg.sender, to, tokens);
        return true;
    }

    function approve(address spender, uint tokens) public 
                     returns (bool success) {
        allowed[msg.sender][spender] = tokens;
        emit Approval(msg.sender, spender, tokens);
        return true;
    }

    function transferFrom(address from, address to, uint tokens) public 
                          returns (bool success) {
        balances[from] = balances[from].sub(tokens);
        allowed[from][msg.sender] = allowed[from][msg.sender].sub(tokens);
        balances[to] = balances[to].add(tokens);
        emit Transfer(from, to, tokens);
        return true;
    }

    function allowance(address tokenOwner, address spender) public constant 
                       returns (uint remaining) {
        return allowed[tokenOwner][spender];
    }

    function burn(address from, uint tokens) public returns (bool success) {
        balances[from] = balances[from].sub(tokens);
        m_total_supply = m_total_supply.sub(tokens); 
        return true;
    } 
 
}
