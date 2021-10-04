import os
import re

FIRST_UNID_NUMBER = int("defd0000", 16) # first UNID in your extension
PREFIX = 'heligen_' # prefix for UNIDs added by your extension
EXTENSION_CORE_FILE = 'HGN_IA_Core.xml' # core file that directly or indirectly references all files in your extension
UNID_LIST_FILE = 'unid_list_file.txt' # file that contains the UNID list


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
            unid_name = unid.split(' ')[0]
            unid_num = unid.split(' ')[1].strip('\n')
            unid_names.append(unid_name)
            unid_nums.append(unid_num)
    print(unid_names)
    print(unid_nums)
    return unid_names, unid_nums


prefixed_unids = [unid for unid in find_all_unids(f'./{EXTENSION_CORE_FILE}') if PREFIX in unid]
free_unid_numbers = []
curr_unid_names, curr_unid_nums = load_unid_list(f'./{UNID_LIST_FILE}')

with open(UNID_LIST_FILE, 'w+') as out:
    last_current_num = int(curr_unid_nums[-1], 16) if len(curr_unid_nums) > 0 else FIRST_UNID_NUMBER
    for i in range(FIRST_UNID_NUMBER, max(last_current_num, FIRST_UNID_NUMBER)):
        print(hex(i))
        if hex(i) not in curr_unid_nums:
            free_unid_numbers.append(hex(i))
    curr_unids = {}
    for i in range(len(curr_unid_names)):
        if curr_unid_names[i] in prefixed_unids:
            curr_unids[curr_unid_names[i]] = curr_unid_nums[i]
    curr_free_unid_num = 0
    print(free_unid_numbers)
    for i in range(len(prefixed_unids)):
        unid = prefixed_unids[i]
        # If unid is already in our list, use that instead
        if unid in curr_unid_names:
            unid_num = curr_unid_nums[curr_unid_names.index(unid)]
            out.write(unid + ' ' + unid_num)
            print(f'Existing UNID: {unid} {unid_num}')
        else:
            if curr_free_unid_num < len(free_unid_numbers):
                unid_num = free_unid_numbers[curr_free_unid_num]
                curr_free_unid_num += 1
            elif len(curr_unid_nums) == 0 and i == 0:
                unid_num = hex(last_current_num)
            else:
                unid_num = hex(last_current_num + (1 + (curr_free_unid_num - len(free_unid_numbers))))
                curr_free_unid_num += 1
            out.write(unid + ' ' + unid_num)
            print(f'New UNID: {unid} {unid_num}')
        out.write('\n')
