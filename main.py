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

def create_sqs():
    PromptUtils(Screen()).input("Please input queue name: ");
    

def func3():
    print("Im func3")

nested_menu = ConsoleMenu(
    "Sample nested menu",
    {
        "call func1": list_bucket,
        "call func2": create_sqs,
        "call func3": func3,
    }
)



menu = ConsoleMenu("S3 bucket watcher",
    {
        "List buckets": list_bucket,
        "Create SQS": create_sqs,
        "goto nested menu": nested_menu,
    }
)


menu.show()