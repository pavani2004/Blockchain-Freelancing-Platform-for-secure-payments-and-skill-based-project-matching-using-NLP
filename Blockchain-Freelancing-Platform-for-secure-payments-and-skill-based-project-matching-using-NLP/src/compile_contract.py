import json
import solcx

# Install specific version of solc
solcx.install_solc('0.8.0')

def compile_contract():
    # Read the Solidity source code
    with open('FreelanceContract.sol', 'r') as file:
        contract_source = file.read()

    # Compile the contract
    compiled_sol = solcx.compile_standard({
        "language": "Solidity",
        "sources": {
            "FreelanceContract.sol": {
                "content": contract_source
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                }
            }
        }
    }, solc_version='0.8.0')

    # Extract the contract data
    contract_data = compiled_sol['contracts']['FreelanceContract.sol']['FreelanceEscrow']
    
    # Create contract JSON
    contract_json = {
        'abi': contract_data['abi'],
        'bytecode': contract_data['evm']['bytecode']['object']
    }

    # Write the JSON file
    with open('FreelanceContract.json', 'w') as file:
        json.dump(contract_json, file, indent=2)

if __name__ == "__main__":
    compile_contract()
    print("Contract compiled successfully! JSON file created.")