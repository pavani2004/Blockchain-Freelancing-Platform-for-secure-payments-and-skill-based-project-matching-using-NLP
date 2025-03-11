// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FreelanceEscrow {
    address public employer;
    address public freelancer;
    string public jobDescription;
    uint256 public budget;
    bool public isCompleted;
    bool public isPaid;

    constructor(address _freelancer, string memory _jobDescription) payable {
        employer = msg.sender;
        freelancer = _freelancer;
        jobDescription = _jobDescription;
        budget = msg.value;
        isCompleted = false;
        isPaid = false;
    }

    function startProject() public {
        require(msg.sender == freelancer, "Only freelancer can start the project");
    }

    function completeWork() public {
        require(msg.sender == freelancer, "Only freelancer can complete the work");
        isCompleted = true;
    }

    function releasePayment() public {
        require(msg.sender == employer, "Only employer can release payment");
        require(isCompleted, "Work must be completed before payment");
        require(!isPaid, "Payment already released");

        isPaid = true;
        payable(freelancer).transfer(address(this).balance);
    }

    function getProjectStatus() public view returns (string memory) {
        if (isPaid) return "Paid";
        if (isCompleted) return "Completed";
        return "In Progress";
    }

    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
}