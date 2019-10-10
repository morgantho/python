import json
import boto3


def lambda_handler(event, context):
    detail = event['detail']

    parameters = detail['requestParameters']
    elements = detail['responseElements']
    identity = detail['userIdentity']
    event_type = detail['eventName']

    account = identity['accountId']

    cloudtrail_name = parameters['name'].split(':trail/', 1)[-1]

    ids = {
        "111111111111": "Prod",
        "111111111111": "Dev",
        "111111111111": "Uat"
    }

    if account in ids:
        name = ids[account]

    if identity['type'] == "IAMUser":
        username = identity['userName']
        aws_type = identity['type']

    elif identity['type'] == "AssumedRole":
        username = identity['principalId'].split(':', 1)[-1]
        session = identity['sessionContext']['sessionIssuer']
        aws_type = session['userName']

    def email(msg):
        mail = boto3.client('sns')
        subject = f"Cloudtrail Change in {name}"
        mail.publish(
            TargetArn="arn:aws:sns:us-east-2:111111111111:Lambda-Alerts",
            Message=json.dumps({'default': msg}),
            Subject=subject,
            MessageStructure='json'
            )

    if event_type == "StopLogging":
        sts = boto3.client('sts')
        role = f"arn:aws:iam::{account}:role/LambdaSecurity"
        assumedRoleObject = sts.assume_role(
            RoleArn=role,
            RoleSessionName="AssumeRoleSession"
        )

        creds = assumedRoleObject['Credentials']
        ct = boto3.client(
            'cloudtrail',
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )

        trail = ct.describe_trails(
            trailNameList=[],
            includeShadowTrails=False
        )

        trail_arn = trail['trailList'][0]['TrailARN']

        ct.start_logging(Name=trail_arn)

        text = '\n'.join([
            f"{event_type} done to {cloudtrail_name} trail by {username} ({aws_type}).",
            "Logging has been auto re-enabled."
        ])
        email(text)
    else:
        text = '\n'.join([
            f"{event_type} done to {cloudtrail_name} trail by {username} ({aws_type})."
        ])

        if aws_type != "LambdaSecurity":
            email(text)
