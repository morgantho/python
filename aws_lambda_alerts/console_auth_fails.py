import boto3
import json

def lambda_handler(event, context):
    detail = event['detail']
    parameters = detail['additionalEventData']
    elements = detail['responseElements']

    login_info = elements.get('ConsoleLogin')
    user_ident = detail.get('userIdentity')
    username   = user_ident.get('userName')
    ip         = detail.get('sourceIPAddress')

    def email(msg):
        mail = boto3.client('sns')
        subject = "Management Console Auth Failure in Prod"
        mail.publish(
            TargetArn="arn:aws:sns:us-east-1:111111111111:Lambda-Alerts",
            Message=json.dumps({'default': msg}),
            Subject=subject,
            MessageStructure='json'
        )

    if login_info == "Success":
        if parameters['MFAUsed'] == "No":
            text = '\n'.join([
                f"User {username}, logged in without MFA."
                ])
            email(text)

    elif login_info == "Failure":
        text = '\n'.join([
            f"User {username}, failed to authenticate from ip: {ip}."
            ])
        email(text)
