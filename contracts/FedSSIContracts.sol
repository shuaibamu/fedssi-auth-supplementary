// SPDX-License-Identifier: MIT
// FedSSI-Auth verifiable data registry: single source used for ALL gas, latency and protocol measurements
// (Revision 2). Compiled with solc 0.8.20, optimizer enabled (200 runs), evmVersion london.
pragma solidity ^0.8.20;

/// @notice DID lifecycle. The DID document itself stays off-chain; only its hash is anchored.
contract DIDRegistry {
    struct DIDRecord { address controller; bytes32 documentHash; uint64 createdAt; uint64 updatedAt; bool active; }
    mapping(bytes32 => DIDRecord) private dids;
    event DIDRegistered(bytes32 indexed did, address indexed controller, bytes32 documentHash);
    event DIDUpdated(bytes32 indexed did, bytes32 documentHash);
    event DIDDeactivated(bytes32 indexed did);

    function registerDID(bytes32 did, bytes32 documentHash) external {
        require(dids[did].createdAt == 0, "exists");
        dids[did] = DIDRecord(msg.sender, documentHash, uint64(block.timestamp), uint64(block.timestamp), true);
        emit DIDRegistered(did, msg.sender, documentHash);
    }
    function updateDIDDocument(bytes32 did, bytes32 newHash) external {
        DIDRecord storage r = dids[did];
        require(r.active && r.controller == msg.sender, "not controller");
        r.documentHash = newHash; r.updatedAt = uint64(block.timestamp);
        emit DIDUpdated(did, newHash);
    }
    function deactivateDID(bytes32 did) external {
        DIDRecord storage r = dids[did];
        require(r.active && r.controller == msg.sender, "not controller");
        r.active = false; r.updatedAt = uint64(block.timestamp);
        emit DIDDeactivated(did);
    }
    function resolveDID(bytes32 did) external view returns (address controller, bytes32 documentHash, bool active) {
        DIDRecord storage r = dids[did]; return (r.controller, r.documentHash, r.active);
    }
    /// @notice batched read used at step 7 of Algorithm 1 (holder and issuer in one call)
    function resolveDIDs(bytes32 didA, bytes32 didB) external view returns (bytes32 hashA, bool activeA, bytes32 hashB, bool activeB) {
        DIDRecord storage a = dids[didA]; DIDRecord storage b = dids[didB];
        return (a.documentHash, a.active, b.documentHash, b.active);
    }
}

/// @notice Bitmap status lists, one list per issuer.
contract RevocationList {
    mapping(bytes32 => address) public issuerOf;
    mapping(bytes32 => mapping(uint256 => uint256)) private bitmaps;
    event ListCreated(bytes32 indexed listId, address indexed issuer);
    event IndexRevoked(bytes32 indexed listId, uint256 idx);

    function createList(bytes32 listId) external {
        require(issuerOf[listId] == address(0), "exists");
        issuerOf[listId] = msg.sender; emit ListCreated(listId, msg.sender);
    }
    function revokeIndex(bytes32 listId, uint256 idx) external {
        require(issuerOf[listId] == msg.sender, "not issuer");
        bitmaps[listId][idx >> 8] |= (uint256(1) << (idx & 255));
        emit IndexRevoked(listId, idx);
    }
    function isRevoked(bytes32 listId, uint256 idx) external view returns (bool) {
        return (bitmaps[listId][idx >> 8] >> (idx & 255)) & 1 == 1;
    }
}

/// @notice Federation primitive (Algorithm 2): the admin of a VERIFYING domain unilaterally declares trust in
/// credentials of a given schema issued by a given issuer of another domain; revocable and expiring.
contract TrustAnchorRegistry {
    address public owner;
    mapping(bytes32 => address) public domainAdmin;
    struct Assertion { bytes32 verifierDomain; bytes32 issuerDomain; bytes32 issuerDid; bytes32 schemaHash; uint64 validFrom; uint64 expiry; bool revoked; }
    mapping(bytes32 => Assertion) private assertions;
    event DomainRegistered(bytes32 indexed domainId, address admin);
    event TrustAssertionAdded(bytes32 indexed id, bytes32 verifierDomain, bytes32 issuerDomain);
    event TrustAssertionRevoked(bytes32 indexed id);

    constructor() { owner = msg.sender; }
    function registerDomain(bytes32 domainId, address admin) external {
        require(msg.sender == owner, "not owner");
        require(domainAdmin[domainId] == address(0), "exists");
        domainAdmin[domainId] = admin; emit DomainRegistered(domainId, admin);
    }
    function addTrustAssertion(bytes32 verifierDomain, bytes32 issuerDomain, bytes32 issuerDid, bytes32 schemaHash, uint64 expiry) external returns (bytes32 id) {
        require(msg.sender == domainAdmin[verifierDomain], "not domain admin");
        id = keccak256(abi.encodePacked(verifierDomain, issuerDomain, issuerDid, schemaHash));
        require(assertions[id].validFrom == 0, "exists");
        assertions[id] = Assertion(verifierDomain, issuerDomain, issuerDid, schemaHash, uint64(block.timestamp), expiry, false);
        emit TrustAssertionAdded(id, verifierDomain, issuerDomain);
    }
    function revokeTrustAssertion(bytes32 id) external {
        Assertion storage a = assertions[id];
        require(a.validFrom != 0 && !a.revoked, "unknown or revoked");
        require(msg.sender == domainAdmin[a.verifierDomain], "not domain admin");
        a.revoked = true; emit TrustAssertionRevoked(id);
    }
    function isTrusted(bytes32 verifierDomain, bytes32 issuerDomain, bytes32 issuerDid, bytes32 schemaHash) external view returns (bool) {
        Assertion storage a = assertions[keccak256(abi.encodePacked(verifierDomain, issuerDomain, issuerDid, schemaHash))];
        return a.validFrom != 0 && !a.revoked && block.timestamp < a.expiry;
    }
}
