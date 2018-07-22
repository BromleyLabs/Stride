pragma solidity ^0.4.24;

library StrideUtils {
    /**
     *  Extracts 32 bytes from a byte array. CAUTION: Beware of left/right 
     *  padding from bytes->bytes32  
     */
    function get_bytes32(bytes b, uint offset) internal pure returns (bytes32) {
        bytes32 out;
        for (uint i = 0; i < 32; i++) 
            out |= bytes32(b[offset + i] & 0xFF) >> (i * 8); 
        return out;
    }

    /**
     *  Extracts 20 bytes from a byte array. Typically used to extract address
     */
    function get_bytes20(bytes b, uint offset) internal pure returns (bytes20) {
        bytes20 out;
        for (uint i = 0; i < 20; i++) 
            out |= bytes20(b[offset + i] & 0xFF) >> (i * 8); 
        return out;
    }

}
