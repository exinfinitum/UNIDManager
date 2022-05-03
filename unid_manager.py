import os
import re
import argparse

def get_args():
    parser = argparse.ArgumentParser(description='Create/update a list of UNIDs referenced by your extension.')
    parser.add_argument('--first_unid_number', required='true', type=str, help='First UNID hex number in your extension.')
    parser.add_argument('--extension_core_file', required='true', type=str, help='Core file that directly or indirectly references all files in your extension.')
    parser.add_argument('--prefix', required='true', type=str, help='Prefix for UNIDs added by your extension.')
    parser.add_argument('--unid_list_file', required='true', type=str, help='Filename of the UNID list to create/add to.')
    args = parser.parse_args()
    return args

def find_all_unids_in_file(f_string):
    unids = []
    unid_strings = re.findall(r'&[a-zA-Z_0-9]*;', f_string)
    for s in unid_strings:
        unids.append(s[1:len(s) - 1])
    return unids

def get_all_xmls_referenced_in_xml(f_string, f_path):
    xml_files_found = re.findall(r'Module filename="[a-zA-Z_0-9]*/*[a-zA-Z_0-9]*.xml', f_string)
    return [f_path + '/' + f.split('Module filename="')[-1] for f in xml_files_found]

def find_all_unids(root_file_path):
    unids_ordered = []
    xml_files_processed = set()
    xml_files_to_process = []
    root_file_dir = os.path.dirname(root_file_path)
    with open(root_file_path, 'r') as root_file:
        f_string = root_file.read()
        for unid in find_all_unids_in_file(f_string):
            if unid not in unids_ordered:
                unids_ordered.append(unid)
        xml_files_to_process += get_all_xmls_referenced_in_xml(f_string, root_file_dir)
        xml_files_processed.add(root_file_path)

    while len(xml_files_to_process) > 0:
        f_path = xml_files_to_process.pop(0)
        if f_path in xml_files_processed:
            continue;
        print(f'Processing file: {f_path}')
        with open(f_path, 'r') as xml_file:
            f_string = xml_file.read()
            for unid in find_all_unids_in_file(f_string):
                if unid not in unids_ordered:
                    unids_ordered.append(unid)
            xml_files_to_process += get_all_xmls_referenced_in_xml(f_string, os.path.dirname(f_path))
            xml_files_processed.add(f_path)
    return unids_ordered

def load_unid_list(unid_list_file_path):
    unid_names = []
    unid_nums = []
    if not os.path.exists(unid_list_file_path):
        with open(unid_list_file_path, 'w+') as f:
            pass
    with open(unid_list_file_path, 'r+') as f:
        for unid in f.readlines():
            unid_string = unid.strip('\n').strip('<!ENTITY ').strip('">').replace('"','')
            unid_name = unid_string.split(' ')[0]
            unid_num = unid_string.split(' ')[1]
            unid_names.append(unid_name)
            unid_nums.append(unid_num)
    return unid_names, unid_nums

def get_unid_decimal_value(unid):
    return int(unid.split('"')[1], 16)

def main(first_unid_number, prefix, extension_core_file, unid_list_file):
    prefixed_unids = [unid for unid in find_all_unids(f'./{extension_core_file}') if prefix in unid]
    free_unid_numbers = []
    curr_unid_names, curr_unid_nums = load_unid_list(f'./{unid_list_file}')

    with open(unid_list_file, 'w+') as out:
        last_current_num = int(curr_unid_nums[-1], 16) if len(curr_unid_nums) > 0 else first_unid_number
        for i in range(first_unid_number, max(last_current_num, first_unid_number)):
            if hex(i) not in curr_unid_nums:
                free_unid_numbers.append(hex(i))
        curr_unids = {}
        for i in range(len(curr_unid_names)):
            if curr_unid_names[i] in prefixed_unids:
                curr_unids[curr_unid_names[i]] = curr_unid_nums[i]
        curr_free_unid_num = 0
        unid_strs = []
        for i in range(len(prefixed_unids)):
            unid = prefixed_unids[i]
            # If unid is already in our list, use that instead
            if unid in curr_unid_names:
                unid_num = curr_unid_nums[curr_unid_names.index(unid)]
                print(f'Existing UNID: {unid} {unid_num}')
                unid_strs.append('<!ENTITY ' + unid + ' ' + '"' + unid_num + '">\n')
            else:
                if curr_free_unid_num < len(free_unid_numbers):
                    unid_num = free_unid_numbers[curr_free_unid_num]
                    curr_free_unid_num += 1
                elif len(curr_unid_nums) == 0 and i == 0:
                    unid_num = hex(last_current_num)
                else:
                    unid_num = hex(last_current_num + (1 + (curr_free_unid_num - len(free_unid_numbers))))
                    curr_free_unid_num += 1
                print(f'New UNID: {unid} {unid_num}')
                unid_strs.append('<!ENTITY ' + unid + ' ' + '"' + unid_num + '">\n')
        unid_strs.sort(key=get_unid_decimal_value)
        for unid in unid_strs:
            out.write(unid)

if __name__ == "__main__":
    args = get_args();
    main(int(args.first_unid_number, 16), args.prefix, args.extension_core_file, args.unid_list_file)

