# aws-versioning-enablement-and-notification

**s3-lifecycle-sns.yaml**
  this cloudformation template basically just create simple notification service on AWS that will be used to send messages to the configured endpoint.


  **bucket-lifecycle.yaml**

  this template creates a s3 bucket that will be used mainly to store our pythong code for our lambda function both the .py and .zip files


  **lambda_s3_life_cycle.yaml**

    this is the core cloudformation template that sets up everything, creating IAM roles and permission, Lambda function, linking bucket and its key, configuring 
    the lambda function metadata. without this template is important to note that the whole solution is null.

    it is also important to note that permission boundary policy is already created in the accounts. if you want to use the templates, your own account might not 
    need it or have it, so you can remove the line or just use comments so that CloudFormation won't demand it.

  **s3-lifecycle-lambda.py**

  this is the actuall python code that does everything for us. it has 6 separated functions that are all linked to each other but performing defferent tasks
  1. lambda_handler function only triggers other functions
  2. get_s3_list function gets all buckets in an account and filter by name and add them to an array list
  3. getS3Version function checks if versioning is enabled on each bucket and if not, send a notification with a list of buckets that do not have versioning enabled
  4. send_sns function basically just get the message from the linked function and send it to the configured endpoint
  5. s3LifeCycleEXISTS function checks for any lifecycle policies that might be attached to each bucket, if the none exists, add buckets to an array list
  6. putLifeCycle_policy function basically takes the list of buckets with no lifecycle policy and enforce the configured one on each bucket
