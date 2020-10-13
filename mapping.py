import yaml
import sys
import os

supported_environments = ['GT1DEV', 'SW1DEV', 'GT1UAT', 'SW1UAT', 'GT1PERF', 'SW1PERF', 'GT1PROD', 'SW1PROD']
supported_file_types = ['.yml', 'yaml']
is_dev_uat = False
txt_file = open("credhub.txt", "w+")
given_environment_variable = ""


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def check_last_char_if_number_remove(env_variable):
    last_char = env_variable[-1]
    is_truly_number = is_number(last_char)
    if is_truly_number:
        return env_variable[:-1]
    return env_variable


def check_for_dms_and_remove(env_var):
    env_var_array = env_var.split('DMS')
    if len(env_var_array) > 1:
        return env_var_array[0] + env_var_array[1]
    return env_var_array[0]


def format_environment_variable(env_var):
    no_dms_env_var = check_for_dms_and_remove(env_var)
    formatted_env_var = check_last_char_if_number_remove(no_dms_env_var)
    return formatted_env_var


def script_error_handling(script_arguments):
    if len(script_arguments) <= 1:
        print("Environment and yml files path are required as arguments in that order")
        sys.exit(0)

    global given_environment_variable
    given_environment_variable = format_environment_variable(script_arguments[1])
    if given_environment_variable not in supported_environments:
        print('Given environment: ' + given_environment_variable + ', is not one of supported environments.')
        sys.exit(0)


def validate_path_to_yml_files_folder(yml_files_path):
    if yml_files_path[-1] != '/':
        yml_files_path = yml_files_path + '/'
    return yml_files_path


def get_yml_files_from_path(yml_files_path):
    yml_files_to_parse = []
    with os.scandir(yml_files_path) as dirs:
        for entry in dirs:
            if entry.name[-4:] in supported_file_types:
                yml_files_to_parse.append(entry.name)
    return yml_files_to_parse


def check_if_is_dev_uat_environment(env_var):
    global is_dev_uat
    if 'DEV' in env_var or 'UAT' in env_var:
        is_dev_uat = True


def get_documents(file_path):
    with open(file_path) as file:
        document = yaml.full_load(file)
    return document


def cf_target_command(org, env, space):
    script = 'cf target -o ' + org + '-' + env + ' -s ' + space
    txt_file.write(script + '\r\n')


def cf_command(service_name, rlm_id, username, password):
    script = 'cf ' + service_name + ' credhub default ' + rlm_id + " -c " + '\'{"user": "' +\
             username + '","password": "' + password + '"}\''
    txt_file.write(script + '\r\n')


def sf_command(service_name, rlm_id, org, space, env_var):
    script = 'cf ' + service_name + ' ' + rlm_id + ' -o ' + org + ' -s ' + space + '-' + env_var
    if is_dev_uat:
        if env_var[:2].upper() == 'SW':
            script2 = script + '2' + '\r\n'
            script4 = script + '4' + '\r\n'
            for scr in [script2, script4]:
                txt_file.write(scr)
            return
        if env_var[:2].upper() == 'GT':
            script1 = script + '1' + '\r\n'
            script3 = script + '3' + '\r\n'
            for scr in [script1, script3]:
                txt_file.write(scr)
            return
    txt_file.write(script + '\r\n')


def main():
    script_arguments = sys.argv
    # Handle Script Argument Exceptions
    script_error_handling(script_arguments)
    check_if_is_dev_uat_environment(given_environment_variable)
    yml_files_path = validate_path_to_yml_files_folder(script_arguments[2])
    yml_files_to_parse = get_yml_files_from_path(yml_files_path)

    for yml_file in yml_files_to_parse:
        document = get_documents(yml_files_path + yml_file)
        # CF TARGET COMMAND
        cf_target_command(document["ORG"], given_environment_variable, document["SPACE"])

        credhubs = document["credhubs"]
        for credhub in credhubs:
            create_script = False
            credhub_valid_environments = credhub['Environments']
            if given_environment_variable in credhub_valid_environments:
                create_script = True

            # Create-Service Scripts
            if create_script and 'create-service' in credhub:
                create_service = credhub['create-service']
                for rml_id, user_password in create_service.items():
                    # CF COMMAND
                    cf_command('create-service', rml_id, user_password['user'], user_password['password'])

            # Share-Service Scripts
            if create_script and 'share-service' in credhub:
                share_service = credhub['share-service']
                for rml_id, org_space_array in share_service.items():
                    for org_space in org_space_array:
                        sf_command('share-service', rml_id, org_space['ORG'], org_space['SPACE'],
                                   given_environment_variable)

            # UnShare-Service Scripts
            if create_script and 'unshare-service' in credhub:
                share_service = credhub['unshare-service']
                for rml_id, org_space_array in share_service.items():
                    for org_space in org_space_array:
                        sf_command('unshare-service', rml_id, org_space['ORG'], org_space['SPACE'],
                                   given_environment_variable)

    txt_file.close()


if __name__ == "__main__":
    main()
