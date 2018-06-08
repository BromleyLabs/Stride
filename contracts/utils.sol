pragma solidity ^0.4.23;

library StrideUtils {
    /* Utility function to extract bytes from a byte array given an offset 
       and returns as bytes32 */
    function getBytes32(bytes b, uint offset) internal pure returns (bytes32) {
        bytes32 out;
        for (uint i = 0; i < 32; i++) 
            out |= bytes32(b[offset + i] & 0xFF) >> (i * 8); 
        return out;
    }

    function getBytes20(bytes b, uint offset) internal pure returns (bytes20) {
        bytes20 out;
        for (uint i = 0; i < 20; i++) 
            out |= bytes20(b[offset + i] & 0xFF) >> (i * 8); 
        return out;
    }

}
