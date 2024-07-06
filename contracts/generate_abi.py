import argparse
import copy
import json
import re
import sys
from enum import Enum

#
# Parse C++ contract file and return ABI
# takes single argument --contract-file path to contract
#

class ParseState(Enum):
    CLEAR = 1
    ACTION_TOP_LEVEL = 2
    ACTION_PARAMS = 3
    ACTION_PARAMS_TYPE = 4
    ACTION_PARAMS_NAME = 5
    END = 6

def read_file(file):
    with open(file, 'r') as file_handle:
        # Read the entire file content
        content = file_handle.read()
    return content

def simple_tokenizer(text):
    # match words,
    # tokenize by spaces, curly braces, angle brackets, commas, or parenthese
    # retain as tokens: curly braces, angle brackets, commas, or parenthese
    pattern = r'[\w:]+|[()\{\},<>]'

    # Use re.findall to find all matches of the pattern in the text
    tokens = re.findall(pattern, text)

    return tokens

def clean_token(text):
    # strip off unwanted leading and trailing chars
    pattern = r'^[\s\(\):;,.\[\]]+|[\s\(\):;,.\[\]]+$'

    stripped_text = re.sub(pattern, '', text)
    return stripped_text

def normalize_type(raw_type):
    if raw_type == "uint64_t":
        return "uint64"
    if raw_type == "std::string":
        return "string"

# functions to return ABI fields
def comment():
    return "This file was generated with python generate_abi."
def abi_version():
    return "eosio::abi/1.2"
def types():
    return []
def generate_structs(structs):
    return structs
def actions(names):
    actions = []
    for name in names:
        actions.append({"name":name, "type":name, "ricardian_contract":""})
    return actions
def tables():
    return []
def kv_tables():
    return {}
def ricardian_clauses():
    return []
def variants():
    return []
def action_results():
    return []

def main():
    # create parse with our arguments to pass in
    parser = argparse.ArgumentParser(description='Process a contract and create ABI.')
    parser.add_argument('--contract-file', type=str, help='The path to the C++ contract file')

    # get the args error if empty
    args = parser.parse_args()
    if not args.contract_file:
        parser.print_help()
        sys.exit(1)

    # read file and tokenize
    tokens = simple_tokenizer(read_file(args.contract_file))

    # variable to parse and construct ABI
    parse_state = ParseState.CLEAR
    action_name = []
    current_struct_name = None
    current_struct_fields = []
    current_struct_param_type = None
    current_struct_param_name = None
    structs = []

    # parse
    for token in tokens:
        # Process high level work
        # Found an action, grab the name, and start parsing params
        if parse_state == ParseState.ACTION_TOP_LEVEL:
            name = clean_token(token)
            action_name.append(name)
            current_struct_name = name
            parse_state = ParseState.ACTION_PARAMS
            # skip to next token
            continue
        # parse params structurs
        # when "(" just started keep going
        # when ")" finished set struct
        elif parse_state == ParseState.ACTION_PARAMS:
            if token == "(":
                parse_state = ParseState.ACTION_PARAMS_TYPE
                continue
        # when not a "(" must be a param type or name
        #      First is type
        #      Next is name
        elif parse_state == ParseState.ACTION_PARAMS_TYPE:
            current_struct_param_type = normalize_type(clean_token(token))
            # move state
            parse_state = ParseState.ACTION_PARAMS_NAME
            # skip to next
            continue
        #      "," means another param comming
        #      ")" means we are finished with this struct
        elif parse_state == ParseState.ACTION_PARAMS_NAME:
            if token == ",":
                # move state
                parse_state = ParseState.ACTION_PARAMS_TYPE
            elif token == ")":
                # move state
                parse_state = ParseState.CLEAR
                structs.append({
                    "name":copy.deepcopy(current_struct_name),
                    "base":"",
                    "fields":copy.deepcopy(current_struct_fields)
                })
                current_struct_name = None
                current_struct_fields = None

            else:
                current_struct_param_name = clean_token(token)
                current_struct_fields.append({
                    "name":current_struct_param_name,
                    "type":current_struct_param_type
                })

            # skip to next
            continue


        # detect and drive top level states
        if token == "ACTION":
            parse_state = ParseState.ACTION_TOP_LEVEL

    # generate abi structure
    abi_struct = {
        "____comment": comment(),
        "version": abi_version(),
        "types": types(),
        "structs": generate_structs(structs),
        "actions": actions(action_name),
        "tables": tables(),
        "kv_tables": kv_tables(),
        "ricardian_clauses": ricardian_clauses(),
        "variants": variants(),
        "action_results": action_results()
    }

    print(json.dumps(abi_struct, indent=4))


if __name__ == '__main__':
    main()
