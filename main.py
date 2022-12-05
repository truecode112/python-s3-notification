from consolemenu import ConsoleMenu
import sys
import boto3
sys.path.append('./s3/')
sys.path.append('./sqs/')
sys.path.append('./s3watcher/')
from consolemenu import *
from consolemenu.items import *
from consolemenu.prompt_utils import PromptUtils
from botocore.exceptions import ClientError
import json

from s3watcher.s3_watcher import S3Watcher
from s3watcher.s3_event import S3Event
from bucket_wrapper import BucketWrapper
from queue_wrapper import create_queue

def get_account_number():
    session = boto3.Session()
    credentials = session.get_credentials()
    credentials = credentials.get_frozen_credentials()
    access_key = credentials.access_key
    secret_key = credentials.secret_key
    #print('access_key = ' + access_key)
    #print('secret_key = ' + secret_key)

    sts = boto3.client(
        "sts", aws_access_key_id=access_key, aws_secret_access_key=secret_key,
    )
    account_id = sts.get_caller_identity()["Account"]
    return account_id

def list_bucket():
    s3_resource = boto3.resource('s3')
    buckets = BucketWrapper.list(s3_resource)
    for bucket in buckets:
        print(bucket.name)

def configure_s3_sqs_for_notification(bucket_name, queue_name):
    region = "us-east-1"
    settings = {
        "bucket_name": bucket_name,
        "queue_name": queue_name,
        "region": region,
        "account_number": get_account_number()
    }
    s3 = boto3.resource('s3', region_name=region)
    b = s3.Bucket(settings["bucket_name"])
    client = boto3.client("s3")
    bucket_notifications_configuration = {
        'QueueConfigurations': [{
            'Events': ['s3:ObjectCreated:*', 's3:ObjectRemoved:*', 's3:ObjectRestore:*'],
            'Id': 'Notifications',
            'QueueArn':
            'arn:aws:sqs:{region}:{account_number}:{queue_name}'.format(**settings)
        }]
    }
    qpolicy = {
        "Version": "2012-10-17",
        "Id":
        "arn:aws:sqs:{region}:{account_number}:{queue_name}/SQSDefaultPolicy".format(
            **settings),
        "Statement": [{
            "Sid": "allow bucket to notify",
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "SQS:*",
            "Resource": "arn:aws:sqs:{region}:{account_number}:{queue_name}".format(
                **settings),
            "Condition": {
                "ArnLike": {
                    "aws:SourceArn": "arn:aws:s3:*:*:{bucket_name}".format(
                        **settings)
                }
            }
        }]
    }
    print("Bucket notify", bucket_notifications_configuration)
    print("Queue Policy", qpolicy)
    queue_attrs = {"Policy": json.dumps(qpolicy), }
    q = boto3.resource("sqs",
                   region_name=region).get_queue_by_name(
                       QueueName=settings["queue_name"])
    q.set_attributes(Attributes=queue_attrs)
    q.attributes
    client.put_bucket_notification_configuration(
        Bucket=settings["bucket_name"],
        NotificationConfiguration=bucket_notifications_configuration)
    print("Configuration done");


def handle(sqs_name, bucket_name):
    print(bucket_name + " is selected")
    print("Creating AWS SQS Queue : " + sqs_name);
    try:
        queue = create_queue(sqs_name)
        configure_s3_sqs_for_notification(bucket_name, sqs_name)
    except ClientError as error:
        print("Couldn't create queue named {0}.".format(sqs_name))
        return

def create_sqs():
    sqs_name = PromptUtils(Screen()).input('Enter SQS name to create')
    if len(sqs_name.input_string) == 0:
        return
    s3_resource = boto3.resource('s3')
    buckets = BucketWrapper.list(s3_resource)
    select_bucket_menu = ConsoleMenu("Select bucket", "Please select bucket to setup notification", None, None, None, None, False, True, "Back")
    bucket_list = []
    for bucket in buckets:
        bucket_list.append(bucket.name)
    for bucket_name in bucket_list:
        bucket_item = FunctionItem(bucket_name, handle, [sqs_name.input_string, bucket_name], None, None, True)
        select_bucket_menu.append_item(bucket_item)
    select_bucket_menu.show()

def start_watch(bucket_name):
    s3_client = boto3.client('s3');
    bucket_notification = s3_client.get_bucket_notification(Bucket=bucket_name, ExpectedBucketOwner=get_account_number());
    if "QueueConfiguration" in bucket_notification:
        queueConfig = bucket_notification['QueueConfiguration']
        if "Queue" in queueConfig:
            queue = queueConfig['Queue']
            watcher = S3Watcher(bucket=bucket_name, queue_url='https://sqs.us-east-1.amazonaws.com/582543755554/testqueue2')
            for event in watcher.watch():
                print(event)
        else:
            print('No queue url in QueueConfiguration')
    else:
        print('Event notification is not configured in this bucket')

def start_watch_s3():
    s3_resource = boto3.resource('s3')
    buckets = BucketWrapper.list(s3_resource)
    select_bucket_menu = ConsoleMenu("Select bucket", "Please select bucket to start watching", None, None, None, None, False, True, "Back")
    bucket_list = []
    for bucket in buckets:
        bucket_list.append(bucket.name)
    for bucket_name in bucket_list:
        bucket_item = FunctionItem(bucket_name, start_watch, [bucket_name], None, None, True)
        select_bucket_menu.append_item(bucket_item)
    select_bucket_menu.show()

def show_main_menu():
    list_bucket_item = FunctionItem("List Buckets", list_bucket)
    create_sqs_item = FunctionItem("Create SQS", create_sqs)
    s3_watch_item = FunctionItem("Watch S3 Bucket", start_watch_s3)
    menu = ConsoleMenu("S3 bucket watcher", "You can list S3 buckets and create AWS SQS for s3 bucket event", None, None, None, None, False)
    menu.append_item(list_bucket_item)
    menu.append_item(create_sqs_item)
    menu.append_item(s3_watch_item)
    menu.show()

show_main_menu()
