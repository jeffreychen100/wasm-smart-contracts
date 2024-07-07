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
    ACTION_RETURN = 2
    ACTION_TOP_LEVEL = 3
    EOSIO_ACTION_TOP_LEVEL = 4
    ACTION_PARAMS = 5
    ACTION_PARAMS_TYPE = 6
    ACTION_PARAMS_NAME = 7
    END = 8

def state_log_wrapper(next_state, debug):
    if debug:
        print(f"Changing to {next_state}")
    return next_state

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
    if raw_type == "uint32_t":
        return "uint32"
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
def ricardian_clauses():
    return []
def variants():
    return []
def action_results(structs):
    return structs

def main():
    # create parse with our arguments to pass in
    parser = argparse.ArgumentParser(description='Process a contract and create ABI.')
    parser.add_argument('--contract-file', type=str, help='The path to the C++ contract file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    # get the args error if empty
    args = parser.parse_args()
    if args.debug:
        print("Starting in debug mode...")
    if not args.contract_file:
        parser.print_help()
        sys.exit(1)

    # read file and tokenize
    tokens = simple_tokenizer(read_file(args.contract_file))

    # variable to parse and construct ABI
    parse_state = state_log_wrapper(ParseState.CLEAR, args.debug)
    action_name = []
    action_return_struct = []
    result_type = None
    current_struct_name = None
    current_struct_fields = []
    current_struct_param_type = None
    current_struct_param_name = None
    structs = []

    # parse
    for token in tokens:
        if args.debug:
            print(f"processing token: {token}")
        # Process high level work
        # Found an action no return type, grab the name, and start parsing params
        if parse_state == ParseState.ACTION_TOP_LEVEL:
            name = clean_token(token)
            action_name.append(name)
            current_struct_name = name
            parse_state = state_log_wrapper(ParseState.ACTION_PARAMS, args.debug)
            # skip to next token
            continue
        # Found an action with return type, grab the name, build return struct,
        #   and start parsing param
        elif parse_state == ParseState.EOSIO_ACTION_TOP_LEVEL:
            name = clean_token(token)
            action_name.append(name)
            current_struct_name = name
            action_return_struct.append({
                "name":copy.deepcopy(current_struct_name),
                "result_type":copy.deepcopy(result_type)
            })
            result_type = None
            parse_state = state_log_wrapper(ParseState.ACTION_PARAMS, args.debug)
            # skip to next token
            continue
        # action has a return structure process that type before action name
        elif parse_state == ParseState.ACTION_RETURN:
            result_type = normalize_type(clean_token(token))
            parse_state = state_log_wrapper(ParseState.EOSIO_ACTION_TOP_LEVEL, args.debug)
            # skip to next token
            continue
        # parse params structurs
        # when "(" just started keep going
        # when ")" finished set struct
        elif parse_state == ParseState.ACTION_PARAMS:
            if token == "(":
                parse_state = state_log_wrapper(ParseState.ACTION_PARAMS_TYPE, args.debug)
                continue
        # when not a "(" must be a param type or name
        #      First is type
        #      Next is name
        elif parse_state == ParseState.ACTION_PARAMS_TYPE:
            current_struct_param_type = normalize_type(clean_token(token))
            # move state
            parse_state = state_log_wrapper(ParseState.ACTION_PARAMS_NAME, args.debug)
            # skip to next
            continue
        #      "," means another param comming
        #      ")" means we are finished with this struct
        elif parse_state == ParseState.ACTION_PARAMS_NAME:
            if token == ",":
                # move state
                parse_state = state_log_wrapper(ParseState.ACTION_PARAMS_TYPE, args.debug)
            elif token == ")":
                # move state
                parse_state = state_log_wrapper(ParseState.CLEAR, args.debug)
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
            parse_state = state_log_wrapper(ParseState.ACTION_TOP_LEVEL, args.debug)
        if token == "eosio::action":
            parse_state = state_log_wrapper(ParseState.ACTION_RETURN, args.debug)

    # generate abi structure
    abi_struct = {
        "____comment": comment(),
        "version": abi_version(),
        "types": types(),
        "structs": generate_structs(structs),
        "actions": actions(action_name),
        "tables": tables(),
        "ricardian_clauses": ricardian_clauses(),
        "variants": variants(),
        "action_results": action_results(action_return_struct)
    }

    print(json.dumps(abi_struct, indent=4))


if __name__ == '__main__':
    main()
