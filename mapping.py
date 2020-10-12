import yaml
import sys
import os

supported_environments = ['GT1DEV', 'SW1DEV', 'GT1UAT', 'SW1UAT', 'GT1PERF', 'SW1PERF', 'GT1PROD', 'SW1PROD']
services_array = ['create-service', 'share-service', 'unshare-service']
supported_file_types = ['.yml', 'yaml']


def get_documents(file_path):
    with open(file_path) as file:
        document = yaml.full_load(file)
    return document


txt_file = open("scripts.txt", "w+")


def cf_command(service_name, rlm_id, username, password):
    script = 'cf ' + service_name + ' credhub default ' + rlm_id + " -c " + '\'{"user": "' + username + '","password": "' + password + '"}\''
    txt_file.write(script+'\r\n')
    print(script)


def sf_command(service_name, rlm_id, org, space):
    script = 'cf ' + service_name + ' ' + rlm_id + ' -o ' + org + ' -s ' + space
    txt_file.write(script + '\r\n')
    print(script)


script_arguments = sys.argv
if len(script_arguments) <= 1:
    print("Environment and yml files path are required as arguments in that order")
    sys.exit(0)

environment_argument = script_arguments[1]
if environment_argument not in supported_environments:
    print('Given environment: ' + environment_argument + ', is not one of supported environments.')
    sys.exit(0)

yml_files_path = script_arguments[2]
if yml_files_path[-1] != '/':
    yml_files_path = yml_files_path + '/'
yml_files_to_parse = []
with os.scandir(yml_files_path) as dirs:
    for entry in dirs:
        if entry.name[-4:] in supported_file_types:
            yml_files_to_parse.append(entry.name)
            print(yml_files_to_parse)

for yml_file in yml_files_to_parse:
    document = get_documents(yml_files_path + yml_file)
    credhubs = document["credhubs"]
    for credhub in credhubs:
        create_script = False
        for credhub_property, credhub_value in credhub.items():
            if credhub_property == 'Environments':
                if environment_argument in credhub_value:
                    create_script = True
            else:
                if create_script:
                    if credhub_property in services_array:
                        credhub_service = credhub[credhub_property]
                        if credhub_property == 'create-service':
                            for rml_id, username_pass in credhub_service.items():
                                cf_command(credhub_property, rml_id, username_pass['user'], username_pass['password'])
                        if credhub_property == 'share-service' or credhub_property == 'unshare-service':
                            for rml_id, org_space_array in credhub_service.items():
                                for org_space in org_space_array:
                                    sf_command(credhub_property, rml_id, org_space['ORG'], org_space['SPACE'])
txt_file.close()