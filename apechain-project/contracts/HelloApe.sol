// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract HelloApe {
    string public greeting = "Hello, Apes!";

    function greet() public view returns (string memory) {
        return greeting;
    }
    
    // Add a function to update the greeting
    function setGreeting(string memory _newGreeting) public {
        greeting = _newGreeting;
    }
}