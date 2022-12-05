from consolemenu import ConsoleMenu
import sys
import boto3
sys.path.append('./s3/')
from consolemenu import *
from consolemenu.items import *
from consolemenu.prompt_utils import PromptUtils

from bucket_wrapper import BucketWrapper

def list_bucket():
    s3_resource = boto3.resource('s3')
    buckets = BucketWrapper.list(s3_resource)
    for bucket in buckets:
        print(bucket.name)

def select_bucket(bucket_name):
    print(bucket_name + " is selected")

def create_sqs():
    sqs_name = PromptUtils(Screen()).input('Enter SQS name to create')
    #s3_resource = boto3.resource('s3')
    #buckets = BucketWrapper.list(s3_resource)
    select_bucket_menu = ConsoleMenu("Select bucket", "Please select bucket to setup notification", None, None, None, None, False, True, "Back")
    bucket_list = ["test1", "test2"]
    #for bucket in buckets:
     #   bucket_list.append(bucket.name)
    for bucket_name in bucket_list:
        bucket_item = FunctionItem(bucket_name, select_bucket, [bucket_name], None, None, True)
        select_bucket_menu.append_item(bucket_item)
    select_bucket_menu.show()

nested_menu = ConsoleMenu(
    "Sample nested menu",
    {
        "call func1": list_bucket,
        "call func2": create_sqs,
    }
)

def show_main_menu():
    list_bucket_item = FunctionItem("List Buckets", list_bucket)
    create_sqs_item = FunctionItem("Create SQS", create_sqs)
    menu = ConsoleMenu("S3 bucket watcher", "You can list S3 buckets and create AWS SQS for s3 bucket event", None, None, None, None, False)
    menu.append_item(list_bucket_item)
    menu.append_item(create_sqs_item)
    menu.show()

show_main_menu()