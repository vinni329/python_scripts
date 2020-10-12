import yaml
import sys
import os

supported_environments = ['GT1DEV', 'SW1DEV', 'GT1UAT', 'SW1UAT', 'GT1PERF', 'SW1PERF', 'GT1PROD', 'SW1PROD']
services_array = ['create-service', 'share-service', 'unshare-service']
supported_file_types = ['.yml', 'yaml']
is_dev_uat = False


def get_documents(file_path):
    with open(file_path) as file:
        document = yaml.full_load(file)
    return document


txt_file = open("scripts.txt", "w+")


def cf_target_command(org, env, space):
    script = 'cf target -o ' + org + '-' + env + ' -s ' + space
    print(script)


def cf_command(service_name, rlm_id, username, password):
    script = 'cf ' + service_name + ' credhub default ' + rlm_id + " -c " + '\'{"user": "' + username + '","password": "' + password + '"}\''
    txt_file.write(script+'\r\n')
    print(script)


def sf_command(service_name, rlm_id, org, space, env_var):
    script = 'cf ' + service_name + ' ' + rlm_id + ' -o ' + org + ' -s ' + space + '-' + env_var
    if is_dev_uat:
        script1 = script + '1' + '\r\n'
        script3 = script + '3' + '\r\n'
        for scr in [script1, script3]:
            txt_file.write(scr)
        return
    txt_file.write(script + '\r\n')
    print(script)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def format_environment_variable(env_var):
    no_dms_env_var = check_for_dms_and_remove(env_var)
    formatted_env_var = check_last_char_if_number_remove(no_dms_env_var)
    return formatted_env_var


def check_for_dms_and_remove(env_var):
    env_var_array = env_var.split('DMS')
    if len(env_var_array) > 1:
        return env_var_array[0] + env_var_array[1]
    return env_var_array[0]


def check_last_char_if_number_remove(env_variable):
    last_char = env_variable[-1]
    is_truly_number = is_number(last_char)
    if is_truly_number:
        return env_variable[:-1]
    return env_variable


def check_if_dev_uat_environment(env_var):
    if 'DEV' in env_var or 'UAT' in env_var:
        return True


script_arguments = sys.argv
if len(script_arguments) <= 1:
    print("Environment and yml files path are required as arguments in that order")
    sys.exit(0)

environment_argument = format_environment_variable(script_arguments[1])
if environment_argument not in supported_environments:
    print('Given environment: ' + environment_argument + ', is not one of supported environments.')
    sys.exit(0)

is_dev_uat = check_if_dev_uat_environment(environment_argument)

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
    cf_target_command(document["ORG"], environment_argument, document["SPACE"])
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
                                    sf_command(credhub_property, rml_id, org_space['ORG'], org_space['SPACE'], environment_argument)
txt_file.close()