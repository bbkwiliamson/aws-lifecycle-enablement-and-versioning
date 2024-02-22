import boto3
import operator
import botocore

client = boto3.client('s3')
sts = boto3.client('sts')
sns = boto3.client('sns')
AccountID = sts.get_caller_identity()


def lambda_handler(event, context):  # the main function
    print(event)
    s3_list = []
    life_cycle_s3 = []

    s3_list = get_s3_list(client)

    getS3Version(client, s3_list)
    life_cycle_s3 = s3LifeCycleEXISTS(client, s3_list)

    putLifeCycle_policy(client, life_cycle_s3)


# a function to get all s3 buckets in an account
def get_s3_list(client):
    s3_array = []
    extra_args = {}

    list_buckets = client.list_buckets()
    for bucket in list_buckets['Buckets']:
        if not operator.contains(bucket, "obsidian"):
            s3_array.append(bucket['Name'])

    return s3_array


# get all buckets without versioning enabled
def getS3Version(client, s3_array):
    no_s3_version = []
    for s3_bucket in s3_array:
        try:

            s3 = client.get_bucket_versioning(Bucket=s3_bucket, ExpectedBucketOwner=AccountID['Account'])
            if 'Status' not in s3 or s3['Status'] == 'Disabled':
                no_s3_version.append(s3_bucket)


        except Exception as e:
            print("failed to get buckets because of this error :", e)

    print("S3 BUCKETS WITHOUT VERSIONING ENABLED :", no_s3_version)

    if len(no_s3_version) > 0:
        message = f"Hello team. We have found s3 Buckets with no versioning enabled and we need versioning enabled for security and compliance purposes.\n Please see the list below, and action what belong to your team. Thank you in advance... \n \n"
        message += "\n".join(no_s3_version)
        subject = f"S3 BUCKETS WITHOUT VERSIONING ENABLED IN THE ACCOUNT :{AccountID['Account']}"
        SNSResult = send_sns(message, subject)
        if SNSResult:
            print("Notification Function Successfully triggered and send buckets with no versioning enabled")
            return SNSResult


# sending a notification for buckets with no versioning enabled...
def send_sns(message, subject):
    try:

        topic_arn = f"arn:aws:sns:af-south-1:{AccountID['Account']}:SNS_Notification_for_S3Lifecycle_and_versioning"
        result = sns.publish(TopicArn=topic_arn, Message=message, Subject=subject)
        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(result)
            print("Bucket versioning Notification Send Successfully..!!!")
            return True



    except Exception as e:

        print("Error occured while publish while publish notification and error is :", e)
        return True


# checking if the life cycle policy already exits, if not... add the buckets to a list
def s3LifeCycleEXISTS(client, s3_array):
    no_S3_life_cycle_list = []
    for s3_life_cycle_policy in s3_array:
        try:
            client.get_bucket_lifecycle_configuration(Bucket=s3_life_cycle_policy,
                                                      ExpectedBucketOwner=AccountID['Account'])

        except:
            no_S3_life_cycle_list.append(s3_life_cycle_policy)

    return no_S3_life_cycle_list


# #adding a life cycle policy to every bucket that does not have one
def putLifeCycle_policy(client, no_s3_life_cycle_list):
    s3_bucket_ignored = []
    life_cycle_rule = {
        "ID": "NoncurrentVersionsToGlacier",
        "Status": "Enabled",
        "Filter": {
            "Prefix": ""
        },
        "NoncurrentVersionTransitions": [
            {
                "NoncurrentDays": 30,
                "StorageClass": "GLACIER_IR",
                "NewerNoncurrentVersions": 60
            }
        ]
    }

    for s3_bucket_name in no_s3_life_cycle_list:
        try:
            # print("there is life_cycle_rule")
            client.put_bucket_lifecycle_configuration(Bucket=s3_bucket_name,
                                                      LifecycleConfiguration={'Rules': [life_cycle_rule]},
                                                      ExpectedBucketOwner=AccountID['Account'])
        except botocore.exceptions.ClientError as e:
            s3_bucket_ignored.append(s3_bucket_name)
            print("Buckets with no life_cycle_rule", len(s3_bucket_ignored))
            print("Exception :", e)

    print("List of buckets that #put_lifecyle_function failed: %s" % len(s3_bucket_ignored))


