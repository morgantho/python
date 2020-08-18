#!/usr/bin/python3.6
# author: mtho
"""Terragrunt wrapper script."""

import os
import sys
import argparse
import shutil

os.environ['PATH'] = "/usr/bin:/usr/sbin:/usr/local/bin"
os.environ['AWS_PROFILE'] = "terraform"

# terragrunt variables
tf_dir = "/opt/terraform/terragrunt"
tg_dir = "/opt/terragrunt/"

modules = ["infra", "s3", "s3-policy",
           "iam", "iam-env", "batch",
           "web", "web-lb", "input",
           "wtfismyip"]

################# DO NOT EDIT BELOW THIS POINT #######################
# command line input variables #
parser = argparse.ArgumentParser(description="Python terragrunt wrapper")
parser.add_argument('-mod', '--module', help='Module(s) to apply',
                    required=True)
parser.add_argument('-env', '--environment', help='AWS environment',
                    required=True)
parser.add_argument('-c', '--cmd', help='Terraform command', required=True)
parser.add_argument('-u', '--update', nargs='?', default=None,
                    const='update',
                    help='Update cached Terraform code')
parser.add_argument('-i', '--noinit', nargs='?', default=None,
                    const='terragrunt-no-auto-init',
                    help='Do not auto run terraform init')
args = parser.parse_args()

#####################################################################


class tcolors:
    INFO = '\033[92m'
    ALERT = '\033[91m'
    ENDC = '\033[0m'


def name_replace(tf_file, tfvars_file, var_name, var_value):
    with open(tf_file) as template, open(tfvars_file, 'w') as var_file:
        replace = template.read().replace(var_name, var_value)
        var_file.write(replace)


def bucket_replace(var_name):
    x_file = f"company-{var_name}/terraform.x"
    tfvars = f"company-{var_name}/terraform.tfvars"
    s3_name = f"{var_name}.{args.environment}"
    if os.path.isdir(f"{var_name}"):
        with open (x_file) as template, open(tfvars, 'w') as var_file:
            replace = template.read().replace("bucketname", s3_name)
            var_file.write(replace)


def tfvar_file_rm(folder, tf_var):
    if os.path.exists(folder):
        os.chdir(folder)
    if os.path.isfile(tf_var):
        os.remove(tf_var)


def s3_tfvars_rm(folder):
    if args.environment in ["uat", "dev"]:
        account = "env"
    elif args.environment == "devops":
        account = "devops"
    elif args.environment == "prod":
        account = "prod"
    if os.path.isdir(f"{tf_dir}/{account}/infra/s3/{folder}"):
        os.chdir(f"{tf_dir}/{account}/infra/s3/{folder}")
        if os.path.isfile('terraform.tfvars'):
            os.remove('terraform.tfvars')

def main_tf_rm():
    os.chdir(tf_dir)
    os.remove('terraform.tfvars')
    os.remove('accounts.tfvars')


def chdir(folder):
    os.chdir(folder)
    if os.path.isfile('terraform.tfvars') is False:
        os.symlink(f'{tf_dir}/terraform.tfvars', 'terraform.tfvars')

###############################################

# write bucket name into files
b_name = "isfs-terraform-%s" % args.environment
name_replace('terraform.tf', 'terraform.tfvars', 'bucket_name', b_name)
name_replace('accounts.tf', 'accounts.tfvars', 'bucket_name', b_name)

# get aws role arn
if args.environment in ['uat', 'dev']:
    if args.environment == "dev":
        role = "arn:aws:iam::000000000000:role/TerraformAccessRole"
    elif args.environment == "uat":
        role = "arn:aws:iam::000000000000:role/TerraformAccessRole"
    account = f"{tf_dir}/env"
    chdir(account)

elif args.environment == "devops":
    role = "arn:aws:iam::000000000000:role/TerraformAccessRole"
    account = f"{tf_dir}/devops"
    chdir(account)

elif args.environment == "prod":
    role = "arn:aws:iam::000000000000:role/TerraformAccessRole"
    account = f"{tf_dir}/prod"
    chdir(account)

elif args.environment == "services":
    account = f"{tf_dir}/services"
    chdir(account)

# ch into the proper directory
if args.module == "infra":
    os.chdir("infra")

if args.module == "s3":
    os.chdir("infra/s3")
    codebuild = "companyprefix-codebuild-%s" % args.environment
    codepipeline = "companyprefix-codepipeline-%s" % args.environment
    name_replace('codebuild/terraform.x', 'codebuild/terraform.tfvars',
                 'bucketname', codebuild)
    name_replace('codepipeline/terraform.x', 'codepipeline/terraform.tfvars',
                 'bucketname', codepipeline)
    if args.environment != "prod":
        bucket_replace('images')
    bucket_replace('other')
    bucket_replace('codebuild-trail')
    bucket_replace('lambda')
    bucket_replace('email')

if args.module == "s3-policy":
    os.chdir("infra/s3-policy")

if args.module == "iam":
    os.chdir("infra/iam")

if args.module == "iam-env":
    os.chdir("iam-env")
    name_replace('terraform.x', 'terraform.tfvars',
                 'envname', args.environment)

if args.module == "batch":
    os.chdir("batch")

if args.module == "web":
    os.chdir("web")

if args.module == "web-lb":
    os.chdir("web-lb")

if args.module == "wtfismyip":
    os.chdir("wtfismyip")

if args.module == "input":
    input_folder = input("Enter folder directory to cd into: ")
    os.chdir(input_folder)

elif args.module not in modules:
    main_tf_rm()
    sys.exit(
        tcolors.INFO + "No changes applied, module is invalid." + tcolors.ENDC)

# terragrunt commands

if args.environment == "services":
    tg_base = f'--terragrunt-non-interactive --terragrunt-download-dir {tg_dir}'
else:
    tg_base = f'--terragrunt-non-interactive --terragrunt-iam-role "{role}" --terragrunt-download-dir {tg_dir}'


tg_no_init = f'terragrunt apply-all {tg_base} --{args.noinit}'
tg_apply = f'terragrunt apply-all {tg_base}'
tg_destroy = f'terragrunt destroy-all {tg_base}'

if args.cmd == "apply":
    if args.update == "update":
        shutil.rmtree(tg_dir, ignore_errors=True)
        os.system(tg_apply)
    else:
        os.system(tg_apply)

    if args.noinit == "terragrunt-no-auto-init":
        tg_cmd = f'{tg_apply} --{args.noinit}'
        os.system(tg_cmd)

    else:
        os.system(tg_apply)

if args.cmd == "destroy":
    if args.module == "input":
        print(
            tcolors.ALERT + f"Are you sure you want to destroy {input_folder} from {args.environment}?" + tcolors.ENDC
        )
    else:
        print(
            tcolors.ALERT + f"Are you sure you want to destroy {args.module} from {args.environment}?" + tcolors.ENDC
        )
    destroy_confirm = input("Enter yes or no to continue: ")

    if destroy_confirm == "no":
        main_tf_rm()
        sys.exit(tcolors.INFO + "No changes have been made." + tcolors.ENDC)
    elif destroy_confirm == "yes":
        if args.noinit == "terragrunt-no-auto-init":
            tg_cmd = f'{tg_destroy} --{args.noinit}'
            os.system(tg_cmd)
        else:
            os.system(tg_destroy)
    else:
        main_tf_rm()
        sys.exit(tcolors.INFO + "No changes have been made." + tcolors.ENDC)


# delete main tfvars files
main_tf_rm()
s3_tfvars_rm('codebuild')
s3_tfvars_rm('codepipeline')
if args.environment != "prod":
    s3_tfvars_rm('images')
s3_tfvars_rm('other')
s3_tfvars_rm('email')
s3_tfvars_rm('codebuild-trail')
s3_tfvars_rm('lambda')
tfvar_file_rm(f'{account}/infra/s3/codebuild', 'terraform.tfvars')
tfvar_file_rm(f'{account}/infra/s3/codepipeline', 'terraform.tfvars')
tfvar_file_rm(f'{account}/iam-env', 'terraform.tfvars')

sys.exit()
