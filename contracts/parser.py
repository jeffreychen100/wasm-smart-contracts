import json

def parse_abi(file_path):
    with open(file_path, 'r') as file:
        abi = json.load(file)
    return abi

def generate_symbolcontract_abi(int64_abi, name_abi):
    symbol_abi = {
        "version": "eosio::abi/1.1",
        "structs": [],
        "actions": [],
        "tables": []
    }

    for struct in int64_abi['structs']:
        if struct['name'] == 'StoredData':
            new_struct = struct.copy()
            new_struct['fields'][0]['type'] = 'symbol'
            symbol_abi['structs'].append(new_struct)
        else:
            symbol_abi['structs'].append(struct)

    for action in int64_abi['actions']:
        symbol_abi['actions'].append(action)

    for table in int64_abi['tables']:
        if table['name'] == 'mytable':
            new_table = table.copy()
            new_table['type'] = 'StoredData'
            symbol_abi['tables'].append(new_table)
        else:
            symbol_abi['tables'].append(table)

    return symbol_abi

def save_abi(file_path, abi):
    with open(file_path, 'w') as file:
        json.dump(abi, file, indent=4)

int64_abi = parse_abi('int64contract.abi')
name_abi = parse_abi('namecontract.abi')

symbol_abi = generate_symbolcontract_abi(int64_abi, name_abi)

save_abi('symbolcontract.abi', symbol_abi)

print("Generated ABI for symbolcontract:")
print(json.dumps(symbol_abi, indent=4))