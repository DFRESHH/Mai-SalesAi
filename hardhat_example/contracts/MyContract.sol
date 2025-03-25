pragma solidity .0.8.28;

contract MyContract {
    string value;

    constructor () {
        value = Hello World!;
    }

    function get() public view returns(string memory) {
        return value;
    }

    function set(string memory _value) public {
        value = _value;
    }
}
